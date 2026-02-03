"""
Tests for the Mergington High School Activities API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        }
    })
    yield


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        
        # Verify Chess Club data
        chess = data["Chess Club"]
        assert chess["description"] == "Learn strategies and compete in chess tournaments"
        assert chess["max_participants"] == 12
        assert len(chess["participants"]) == 2
        assert chess["current_participants"] == 2
        assert chess["available_spots"] == 10

    def test_get_activities_includes_participant_count(self, client):
        """Test that activities include participant counts"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "current_participants" in activity_data
            assert "available_spots" in activity_data
            assert activity_data["current_participants"] == len(activity_data["participants"])
            assert activity_data["available_spots"] == activity_data["max_participants"] - activity_data["current_participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_registered(self, client):
        """Test signup when student is already registered"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_updates_participant_list(self, client):
        """Test that signup properly updates the participant list"""
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        
        client.post("/activities/Chess Club/signup?email=new@mergington.edu")
        
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()["Chess Club"]["participants"])
        
        assert updated_count == initial_count + 1


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/NonExistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_registered(self, client):
        """Test unregister when student is not registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]

    def test_unregister_updates_participant_list(self, client):
        """Test that unregister properly updates the participant list"""
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        
        client.delete("/activities/Chess Club/unregister?email=michael@mergington.edu")
        
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()["Chess Club"]["participants"])
        
        assert updated_count == initial_count - 1


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_signup_with_special_characters_in_activity_name(self, client):
        """Test signup with URL-encoded activity name"""
        # Add an activity with special characters
        activities["Art & Craft"] = {
            "description": "Creative arts",
            "schedule": "Mondays",
            "max_participants": 10,
            "participants": []
        }
        
        response = client.post(
            "/activities/Art & Craft/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200

    def test_multiple_signups_and_unregisters(self, client):
        """Test multiple signup and unregister operations"""
        # Multiple signups
        emails = ["test1@mergington.edu", "test2@mergington.edu", "test3@mergington.edu"]
        for email in emails:
            response = client.post(f"/activities/Chess Club/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all added
        activities_response = client.get("/activities")
        participants = activities_response.json()["Chess Club"]["participants"]
        for email in emails:
            assert email in participants
        
        # Unregister one
        response = client.delete("/activities/Chess Club/unregister?email=test2@mergington.edu")
        assert response.status_code == 200
        
        # Verify removed
        activities_response = client.get("/activities")
        participants = activities_response.json()["Chess Club"]["participants"]
        assert "test2@mergington.edu" not in participants
        assert "test1@mergington.edu" in participants
        assert "test3@mergington.edu" in participants
