"""
FastAPI Backend Tests using AAA (Arrange-Act-Assert) Pattern

Tests cover:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/participants
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide TestClient for making requests."""
    return TestClient(app)


@pytest.fixture
def reset_activities(monkeypatch):
    """Reset activities to a clean state before each test."""
    clean_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": []
        }
    }
    monkeypatch.setattr("src.app.activities", clean_activities)
    return clean_activities


# ============================================================================
# GET /activities Tests
# ============================================================================

class TestGetActivities:
    """Test GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all available activities."""
        # Arrange
        expected_count = 2

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities_data = response.json()
        assert len(activities_data) == expected_count
        assert "Chess Club" in activities_data
        assert "Programming Class" in activities_data

    def test_get_activities_returns_correct_structure(self, client, reset_activities):
        """Test that each activity has the required fields."""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        for activity_name, activity_info in activities_data.items():
            assert set(activity_info.keys()) == required_fields
            assert isinstance(activity_info["participants"], list)
            assert isinstance(activity_info["max_participants"], int)

    def test_get_activities_includes_participant_count(self, client, reset_activities):
        """Test that participant lists are correctly returned."""
        # Arrange
        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        assert len(activities_data["Chess Club"]["participants"]) == 1
        assert "michael@mergington.edu" in activities_data["Chess Club"]["participants"]
        assert len(activities_data["Programming Class"]["participants"]) == 0


# ============================================================================
# POST /activities/{activity_name}/signup Tests
# ============================================================================

class TestPostSignup:
    """Test POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_participant_success(self, client, reset_activities):
        """Test successful signup for a new participant."""
        # Arrange
        activity_name = "Programming Class"
        email = "alice@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]

    def test_signup_participant_appears_in_activities(self, client, reset_activities):
        """Test that a signed-up participant appears in the activities list."""
        # Arrange
        activity_name = "Programming Class"
        email = "bob@mergington.edu"

        # Act
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        response = client.get("/activities")

        # Assert
        participants = response.json()[activity_name]["participants"]
        assert email in participants

    def test_signup_duplicate_raises_error(self, client, reset_activities):
        """Test that duplicate signup returns error."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_raises_error(self, client, reset_activities):
        """Test that signup for non-existent activity returns 404."""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "charlie@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_new_participants(self, client, reset_activities):
        """Test signing up multiple different participants."""
        # Arrange
        activity_name = "Programming Class"
        emails = ["alice@mergington.edu", "bob@mergington.edu", "charlie@mergington.edu"]

        # Act
        for email in emails:
            client.post(f"/activities/{activity_name}/signup", params={"email": email})
        response = client.get("/activities")

        # Assert
        participants = response.json()[activity_name]["participants"]
        assert len(participants) == 3
        for email in emails:
            assert email in participants


# ============================================================================
# DELETE /activities/{activity_name}/participants Tests
# ============================================================================

class TestDeleteParticipant:
    """Test DELETE /activities/{activity_name}/participants endpoint."""

    def test_delete_participant_success(self, client, reset_activities):
        """Test successful removal of a participant."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]

    def test_delete_participant_removed_from_list(self, client, reset_activities):
        """Test that deleted participant is removed from the activity."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        response = client.get("/activities")

        # Assert
        participants = response.json()[activity_name]["participants"]
        assert email not in participants

    def test_delete_nonexistent_participant_raises_error(self, client, reset_activities):
        """Test that deleting non-existent participant returns 404."""
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_delete_from_nonexistent_activity_raises_error(self, client, reset_activities):
        """Test that deleting from non-existent activity returns 404."""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "alice@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_delete_participant_multiple_times(self, client, reset_activities):
        """Test that multiple participants can be deleted."""
        # Arrange
        activity_name = "Programming Class"
        emails = ["alice@mergington.edu", "bob@mergington.edu"]
        # Add participants
        for email in emails:
            client.post(f"/activities/{activity_name}/signup", params={"email": email})

        # Act
        for email in emails:
            response = client.delete(
                f"/activities/{activity_name}/participants",
                params={"email": email}
            )
            assert response.status_code == 200

        # Assert
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert len(participants) == 0
