from django.db import migrations

CREATE = """
CREATE FUNCTION audit_logs_block_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs_auditlog is append-only: % is not allowed', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_no_update_delete
BEFORE UPDATE OR DELETE ON audit_logs_auditlog
FOR EACH ROW EXECUTE FUNCTION audit_logs_block_mutation();
"""

DROP = """
DROP TRIGGER IF EXISTS audit_logs_no_update_delete ON audit_logs_auditlog;
DROP FUNCTION IF EXISTS audit_logs_block_mutation();
"""


class Migration(migrations.Migration):
    dependencies = [("audit_logs", "0001_initial")]
    operations = [migrations.RunSQL(CREATE, reverse_sql=DROP)]
