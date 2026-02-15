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


def test_signup_at_maximum_capacity():
    activity_name = "Chess Club"
    max_capacity = activities[activity_name]["max_participants"]
    
    # Fill the activity to maximum capacity
    for i in range(max_capacity - len(activities[activity_name]["participants"])):
        email = f"student{i}@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )
        assert response.status_code == 200
    
    # Verify activity is at capacity
    activities_response = client.get("/activities")
    current_activities = activities_response.json()
    assert len(current_activities[activity_name]["participants"]) == max_capacity
    
    # Attempt to sign up one more student when at capacity
    overflow_email = "overflow@mergington.edu"
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": overflow_email},
    )
    
    # Currently the app allows signup beyond max_participants
    # This test documents the current behavior
    # If capacity checking is added in the future, update this assertion
    # to expect 400 status code with "Activity is at maximum capacity" detail
    assert response.status_code == 200
