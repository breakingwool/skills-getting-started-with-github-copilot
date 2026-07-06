from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(deepcopy(original))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_list():
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["description"]


def test_signup_adds_participant():
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant():
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_returns_404_for_unknown_activity():
    response = client.post("/activities/Unknown/signup?email=someone@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_removes_email():
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    assert response.status_code == 200
    assert "unregistered" in response.json()["message"].lower()
    assert email not in activities[activity_name]["participants"]


def test_unregister_unknown_participant_returns_404():
    response = client.delete("/activities/Chess Club/participants/not-a-student@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
