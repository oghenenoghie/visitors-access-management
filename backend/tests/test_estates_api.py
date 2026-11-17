def test_anonymous_gets_401_in_the_standard_error_shape(api_client, db):
    response = api_client.get("/api/v1/estates/")
    assert response.status_code == 401
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "not_authenticated"
    assert set(body["error"]) == {"code", "message", "details"}


def test_list_returns_only_the_callers_estates(api_client, make_user, make_estate, make_membership):
    mine, theirs = make_estate(name="Mine"), make_estate(name="Theirs")
    user = make_user()
    make_membership(user, mine)
    api_client.force_authenticate(user)
    response = api_client.get("/api/v1/estates/")
    assert response.status_code == 200
    names = [e["name"] for e in response.json()["results"]]
    assert names == ["Mine"]
    assert theirs.name not in names


def test_other_estate_detail_is_404_not_403(api_client, make_user, make_estate, make_membership):
    mine, theirs = make_estate(), make_estate()
    user = make_user()
    make_membership(user, mine)
    api_client.force_authenticate(user)
    assert api_client.get(f"/api/v1/estates/{mine.id}/").status_code == 200
    response = api_client.get(f"/api/v1/estates/{theirs.id}/")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_user_without_membership_sees_nothing(api_client, make_user, make_estate):
    make_estate()
    api_client.force_authenticate(make_user())
    assert api_client.get("/api/v1/estates/").json()["results"] == []


def test_only_platform_admins_can_write_estates(api_client, make_user, make_estate, make_member):
    from apps.estates.models import EstateRole

    estate = make_estate()
    for role in EstateRole.values:
        api_client.force_authenticate(make_member(estate, role))
        assert api_client.post("/api/v1/estates/", {"name": "x"}).status_code == 403
        assert (
            api_client.patch(
                f"/api/v1/estates/{estate.id}/", {"name": "y"}, format="json"
            ).status_code
            == 403
        )


def test_estates_cannot_be_deleted(api_client, platform_admin, make_estate):
    estate = make_estate()
    api_client.force_authenticate(platform_admin)
    assert api_client.delete(f"/api/v1/estates/{estate.id}/").status_code == 405


def test_platform_admin_creates_and_updates_estates_with_audit(api_client, platform_admin):
    from apps.audit_logs.models import AuditLog

    api_client.force_authenticate(platform_admin)
    created = api_client.post(
        "/api/v1/estates/",
        {"name": "Palm Estate", "estate_code": "PALM-1", "timezone": "Africa/Lagos"},
        format="json",
    )
    assert created.status_code == 201
    estate_id = created.json()["id"]
    updated = api_client.patch(
        f"/api/v1/estates/{estate_id}/", {"name": "Palm Estate Phase 2"}, format="json"
    )
    assert updated.status_code == 200
    log = AuditLog.objects.get(action="estate.updated")
    assert log.previous_values["name"] == "Palm Estate"
    assert log.new_values["name"] == "Palm Estate Phase 2"
    assert log.actor == platform_admin and str(log.estate_id) == estate_id
    assert AuditLog.objects.filter(action="estate.created").exists()


def test_estate_validation_and_immutable_code(api_client, platform_admin, make_estate):
    api_client.force_authenticate(platform_admin)
    bad = api_client.post(
        "/api/v1/estates/",
        {"name": "X", "estate_code": "lower case", "timezone": "Mars/Olympus"},
        format="json",
    )
    assert bad.status_code == 400
    assert set(bad.json()["error"]["details"]) == {"estate_code", "timezone"}
    estate = make_estate(estate_code="KEEP1")
    change = api_client.patch(
        f"/api/v1/estates/{estate.id}/", {"estate_code": "NEW2"}, format="json"
    )
    assert change.status_code == 400
