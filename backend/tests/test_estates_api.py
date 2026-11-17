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


def test_estates_are_read_only_for_now(api_client, make_user, make_estate, make_membership):
    estate, user = make_estate(), make_user()
    make_membership(user, estate)
    api_client.force_authenticate(user)
    assert api_client.post("/api/v1/estates/", {"name": "x"}).status_code == 405
    assert api_client.delete(f"/api/v1/estates/{estate.id}/").status_code == 405
