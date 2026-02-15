from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


client = TestClient(app)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog():
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Basketball Team" in payload
    assert "participants" in payload["Basketball Team"]


def test_signup_adds_new_participant():
    email = "new.student@mergington.edu"
    activity_name = "Chess Club"

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"

    activities_response = client.get("/activities")
    updated_activities = activities_response.json()
    assert email in updated_activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant():
    activity_name = "Soccer Club"
    existing_email = activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_returns_404_for_unknown_activity():
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "test@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
