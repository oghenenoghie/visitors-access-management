from django.db import migrations


FORWARD_SQL = """
CREATE OR REPLACE FUNCTION access_control_prevent_event_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Access events are append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER access_control_access_event_immutable
BEFORE UPDATE OR DELETE ON access_control_accessevent
FOR EACH ROW EXECUTE FUNCTION access_control_prevent_event_mutation();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS access_control_access_event_immutable ON access_control_accessevent;
DROP FUNCTION IF EXISTS access_control_prevent_event_mutation();
"""


class Migration(migrations.Migration):
    dependencies = [("access_control", "0001_initial")]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
