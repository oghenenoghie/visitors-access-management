import csv
import io
import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.audit_logs.services import record
from apps.properties.models import Property, PropertyStatus, ResidentialUnit
from apps.users.models import User

from .models import ResidentProfile, ResidentStatus

MAX_IMPORT_BYTES = 5 * 1024 * 1024
MAX_IMPORT_ROWS = 1000
email_validator = EmailValidator()
phone_validator = RegexValidator(r"^\+?[0-9]{7,15}$")


def _parse_csv(uploaded_file, expected_headers):
    if uploaded_file.size > MAX_IMPORT_BYTES:
        raise ValidationError({"file": "CSV file must not exceed 5 MB."})
    try:
        text = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError({"file": "CSV must be UTF-8 encoded."}) from exc
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    if len(headers) != len(set(headers)):
        raise ValidationError({"file": "CSV contains duplicate column headings."})
    missing = sorted(set(expected_headers) - set(headers))
    if missing:
        raise ValidationError({"file": f"Missing required columns: {', '.join(missing)}."})
    rows = []
    for row_number, row in enumerate(reader, start=2):
        if row_number - 1 > MAX_IMPORT_ROWS:
            raise ValidationError(
                {"file": f"CSV cannot contain more than {MAX_IMPORT_ROWS} data rows."}
            )
        if None in row:
            raise ValidationError(
                {"file": f"Row {row_number} contains more values than the CSV headings."}
            )
        if not any((value or "").strip() for value in row.values()):
            continue
        rows.append((row_number, {key: (value or "").strip() for key, value in row.items()}))
    if not rows:
        raise ValidationError({"file": "CSV contains no data rows."})
    return rows


def _validate_units(estate, uploaded_file):
    rows = _parse_csv(uploaded_file, ["property_id", "unit_number"])
    errors = []
    valid = []
    seen = set()
    for row_number, row in rows:
        try:
            property_id = uuid.UUID(row["property_id"])
            property_record = Property.objects.get(
                pk=property_id, estate=estate, status=PropertyStatus.ACTIVE
            )
        except (ValueError, Property.DoesNotExist):
            errors.append(
                {
                    "row": row_number,
                    "field": "property_id",
                    "message": "Property is not active in this estate.",
                }
            )
            continue
        unit_number = row["unit_number"]
        block = row.get("block", "")
        floor = row.get("floor", "")
        if len(unit_number) > 40 or len(block) > 40 or len(floor) > 30:
            errors.append(
                {
                    "row": row_number,
                    "field": "unit_number",
                    "message": "Unit number, block or floor exceeds its allowed length.",
                }
            )
            continue
        if not unit_number:
            errors.append(
                {
                    "row": row_number,
                    "field": "unit_number",
                    "message": "Unit number is required.",
                }
            )
            continue
        key = (str(property_id), block, unit_number.casefold())
        if key in seen or ResidentialUnit.objects.filter(
            property=property_record, block=block, unit_number__iexact=unit_number
        ).exists():
            errors.append(
                {
                    "row": row_number,
                    "field": "unit_number",
                    "message": "This unit already exists in the property or CSV.",
                }
            )
            continue
        seen.add(key)
        valid.append(
            {
                "property": property_record,
                "unit_number": unit_number,
                "block": block,
                "floor": floor,
            }
        )
    return valid, errors


def _validate_residents(estate, uploaded_file):
    rows = _parse_csv(uploaded_file, ["email", "first_name", "last_name"])
    errors = []
    valid = []
    seen = set()
    for row_number, row in rows:
        email = User.objects.normalize_email(row["email"]).lower()
        first_name = row["first_name"]
        last_name = row["last_name"]
        phone = row.get("phone_number", "")
        try:
            email_validator(email)
        except DjangoValidationError:
            errors.append(
                {
                    "row": row_number,
                    "field": "email",
                    "message": "Enter a valid email address.",
                }
            )
            continue
        if len(email) > 254 or len(first_name) > 150 or len(last_name) > 150 or len(phone) > 16:
            errors.append(
                {
                    "row": row_number,
                    "field": "email",
                    "message": "A field exceeds its maximum allowed length.",
                }
            )
            continue
        if not first_name or not last_name:
            errors.append(
                {
                    "row": row_number,
                    "field": "name",
                    "message": "First and last name are required.",
                }
            )
            continue
        if email.casefold() in seen or User.objects.filter(email__iexact=email).exists():
            errors.append(
                {
                    "row": row_number,
                    "field": "email",
                    "message": "This email already exists in the system or CSV.",
                }
            )
            continue
        if phone:
            try:
                phone_validator(phone)
            except DjangoValidationError:
                errors.append(
                    {
                        "row": row_number,
                        "field": "phone_number",
                        "message": "Enter a valid phone number.",
                    }
                )
                continue
        seen.add(email.casefold())
        valid.append(
            {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": phone,
            }
        )
    return valid, errors


@transaction.atomic
def process_bulk_import(*, estate, import_type, uploaded_file, dry_run, actor, request):
    if import_type == "units":
        valid, errors = _validate_units(estate, uploaded_file)
    elif import_type == "residents":
        valid, errors = _validate_residents(estate, uploaded_file)
    else:
        raise ValidationError({"import_type": "Choose 'units' or 'residents'."})

    result = {
        "import_type": import_type,
        "estate_id": str(estate.pk),
        "dry_run": dry_run,
        "valid_rows": len(valid),
        "error_rows": len(errors),
        "errors": errors,
        "committed": False,
    }
    if dry_run:
        return result
    if errors:
        raise ValidationError(
            {
                "message": "Import was not committed because validation errors remain.",
                **result,
            }
        )
    if import_type == "units":
        ResidentialUnit.objects.bulk_create(
            [ResidentialUnit(**row) for row in valid], batch_size=250
        )
    else:
        profiles = []
        for row in valid:
            user = User.objects.create_user(
                email=row["email"],
                password=None,
                first_name=row["first_name"],
                last_name=row["last_name"],
                phone_number=row["phone_number"],
                is_active=False,
            )
            profiles.append(
                ResidentProfile(user=user, estate=estate, status=ResidentStatus.PENDING)
            )
        ResidentProfile.objects.bulk_create(profiles, batch_size=250)

    result["committed"] = True
    record(
        action=f"resident.bulk_{import_type}_imported",
        actor=actor,
        estate=estate,
        resource_type=f"residents.{import_type}_import",
        resource_id="",
        new_values={
            "import_type": import_type,
            "row_count": len(valid),
            "error_count": 0,
        },
        request=request,
    )
    return result
