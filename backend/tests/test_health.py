def test_health_is_public_and_reports_database(api_client, db):
    response = api_client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_openapi_schema_is_served(api_client, db):
    response = api_client.get("/api/v1/schema/")
    assert response.status_code == 200
