import os

os.environ["USE_MONGOMOCK"] = "True"  # must be set before app/db import

import pytest

from app import create_app
from app.db import get_students_collection, reset_client


@pytest.fixture
def client():
    reset_client()
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        get_students_collection().delete_many({})
        yield client


def create_student(client, name="Ada Lovelace", reg_no="ENG/20/0001", email="ada@example.com"):
    return client.post("/api/students", json={"name": name, "reg_no": reg_no, "email": email})


def auth(token):
    return {"Authorization": f"Token {token}"}


def test_create_student(client):
    response = create_student(client)
    assert response.status_code == 201
    body = response.get_json()
    assert "id" in body
    assert "access_token" in body
    assert get_students_collection().count_documents({}) == 1


def test_create_rejects_duplicate_reg_no(client):
    create_student(client)
    response = create_student(client, email="different@example.com")
    assert response.status_code == 400


def test_create_rejects_duplicate_email(client):
    create_student(client)
    response = create_student(client, reg_no="ENG/20/9999")
    assert response.status_code == 400


def test_create_rejects_missing_fields(client):
    response = client.post("/api/students", json={"name": "Ada"})
    assert response.status_code == 400


def test_owner_can_retrieve_own_details(client):
    created = create_student(client).get_json()
    response = client.get(f"/api/students/{created['id']}", headers=auth(created["access_token"]))
    assert response.status_code == 200
    body = response.get_json()
    assert body["reg_no"] == "ENG/20/0001"
    assert "access_token" not in body


def test_retrieve_without_token_is_forbidden(client):
    created = create_student(client).get_json()
    response = client.get(f"/api/students/{created['id']}")
    assert response.status_code == 403


def test_retrieve_with_wrong_token_is_forbidden(client):
    created = create_student(client).get_json()
    other = create_student(client, name="Grace Hopper", reg_no="ENG/20/0002", email="grace@example.com").get_json()
    response = client.get(f"/api/students/{created['id']}", headers=auth(other["access_token"]))
    assert response.status_code == 403


def test_retrieve_unknown_id_is_not_found(client):
    response = client.get("/api/students/000000000000000000000000", headers=auth("does-not-matter"))
    assert response.status_code == 404


def test_retrieve_malformed_id_is_not_found(client):
    response = client.get("/api/students/not-a-valid-id", headers=auth("does-not-matter"))
    assert response.status_code == 404


def test_owner_can_update_name_only(client):
    created = create_student(client).get_json()
    response = client.patch(
        f"/api/students/{created['id']}",
        json={"name": "Ada K. Lovelace", "reg_no": "HACKED/0001", "email": "hacked@example.com"},
        headers=auth(created["access_token"]),
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["name"] == "Ada K. Lovelace"
    assert body["reg_no"] == "ENG/20/0001"
    assert body["email"] == "ada@example.com"


def test_owner_can_delete_account(client):
    created = create_student(client).get_json()
    response = client.delete(f"/api/students/{created['id']}", headers=auth(created["access_token"]))
    assert response.status_code == 200
    assert get_students_collection().count_documents({}) == 0


def test_delete_without_token_is_forbidden(client):
    created = create_student(client).get_json()
    response = client.delete(f"/api/students/{created['id']}")
    assert response.status_code == 403
    assert get_students_collection().count_documents({}) == 1
