"""
Tests for the Mergington High School Activities API endpoints.
Uses the AAA (Arrange-Act-Assert) pattern for clarity.
"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client: TestClient):
        """
        Arrange: No setup needed, fixtures handle state reset.
        Act: Request all activities.
        Assert: Verify response contains all activities with correct structure.
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) >= 3
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
    
    def test_get_activities_response_structure(self, client: TestClient):
        """
        Arrange: No setup needed.
        Act: Request activities.
        Assert: Verify each activity has required fields.
        """
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, details in activities.items():
            assert isinstance(activity_name, str)
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_successful(self, client: TestClient):
        """
        Arrange: Prepare a new email for signup.
        Act: Post signup request.
        Assert: Verify participant is added and response is successful.
        """
        # Arrange
        activity = "Chess Club"
        email = "new_student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}",
            headers={"content-type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_signup_duplicate_email_rejected(self, client: TestClient):
        """
        Arrange: Use an email already registered for the activity.
        Act: Attempt to signup with duplicate email.
        Assert: Verify request fails with 400 status.
        """
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already in participants
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}",
            headers={"content-type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_activity_full_rejected(self, client: TestClient):
        """
        Arrange: Use an activity with max capacity reached.
        Act: Attempt to signup for a full activity.
        Assert: Verify request fails with 400 status.
        """
        # Arrange
        activity = "Programming Class"  # max_participants=2, already has 2
        email = "another_student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}",
            headers={"content-type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 400
        assert "full" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_not_found(self, client: TestClient):
        """
        Arrange: Use a nonexistent activity name.
        Act: Attempt to signup for nonexistent activity.
        Assert: Verify request fails with 404 status.
        """
        # Arrange
        activity = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}",
            headers={"content-type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/participants endpoint."""
    
    def test_unregister_successful(self, client: TestClient):
        """
        Arrange: Prepare an existing participant to remove.
        Act: Send delete request to unregister participant.
        Assert: Verify participant is removed and response is successful.
        """
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/participants?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_unregister_nonexistent_participant_not_found(self, client: TestClient):
        """
        Arrange: Use a participant email not in the activity.
        Act: Send delete request for nonexistent participant.
        Assert: Verify request fails with 404 status.
        """
        # Arrange
        activity = "Chess Club"
        email = "nonexistent@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/participants?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]
    
    def test_unregister_nonexistent_activity_not_found(self, client: TestClient):
        """
        Arrange: Use a nonexistent activity name.
        Act: Send delete request for nonexistent activity.
        Assert: Verify request fails with 404 status.
        """
        # Arrange
        activity = "Nonexistent Club"
        email = "someone@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/participants?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestIntegration:
    """Integration tests combining multiple operations."""
    
    def test_signup_then_unregister_workflow(self, client: TestClient):
        """
        Arrange: Pick an activity with available spots.
        Act: Signup a participant, then unregister them.
        Assert: Verify both operations succeed and participant count changes.
        """
        # Arrange
        activity = "Gym Class"
        email = "test_workflow@mergington.edu"
        
        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}",
            headers={"content-type": "application/json"}
        )
        
        # Assert - Signup successful
        assert signup_response.status_code == 200
        activities_after_signup = client.get("/activities").json()
        assert email in activities_after_signup[activity]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/participants?email={email}"
        )
        
        # Assert - Unregister successful
        assert unregister_response.status_code == 200
        activities_after_unregister = client.get("/activities").json()
        assert email not in activities_after_unregister[activity]["participants"]
