import pytest
from api import app, db

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

#test short code creation
def test_create_short_url(client):
    response = client.post("/urls", json={
        "original_url": "https://example.com"
    })

    assert response.status_code == 201

    data = response.get_json()
    assert "short_code" in data
    assert data["original_url"] == "https://example.com"

#test redirection
def test_redirect(client):
    # Create short code
    response = client.post("/urls", json={
        "original_url": "https://example.com"
    })

    data = response.get_json()
    code = data["short_code"]

    redirect_response = client.get(f"/{code}")

    assert redirect_response.status_code == 302
    assert redirect_response.location == "https://example.com"

#test aliases
def test_custom_alias(client):
    response = client.post("/urls", json={
        "original_url": "https://example.com",
        "custom_alias": "myalias"
    })

    assert response.status_code == 201

    data = response.get_json()
    assert data["short_code"] == "myalias"


#test click count incrementation
def test_click_count_increment(client):
    response = client.post("/urls", json={
        "original_url": "https://example.com"
    })

    code = response.get_json()["short_code"]

    client.get(f"/{code}")
    client.get(f"/{code}")

    metadata = client.get(f"/short/{code}")
    data = metadata.get_json()

    assert data["click_count"] == 2