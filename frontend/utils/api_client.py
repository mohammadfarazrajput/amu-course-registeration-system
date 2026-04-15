"""
API Client
Handles all backend API communication
"""

import requests
from typing import Dict, List, Optional


class APIClient:
    """Client for backend API communication"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def _post(self, endpoint: str, data: dict) -> dict:
        """POST request helper"""
        try:
            response = requests.post(f"{self.base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def _get(self, endpoint: str) -> dict:
        """GET request helper"""
        try:
            response = requests.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    # Authentication
    def login(self, faculty_number: str, enrollment_number: str) -> dict:
        """Student login"""
        return self._post("/api/auth/login", {
            "faculty_number": faculty_number,
            "enrollment_number": enrollment_number
        })
    
    # Eligibility
    def check_eligibility(self, student_id: int) -> dict:
        """Check student eligibility"""
        return self._get(f"/api/eligibility/{student_id}")
    
    # Courses
    def get_course_recommendations(self, student_id: int) -> dict:
        """Get course recommendations"""
        return self._get(f"/api/courses/recommend/{student_id}")
    
    # Registration
    def submit_registration(
        self,
        student_id: int,
        course_ids: List[int],
        registration_mode: str = "a"
    ) -> dict:
        """Submit course registration"""
        return self._post("/api/registration/submit", {
            "student_id": student_id,
            "course_ids": course_ids,
            "registration_mode": registration_mode
        })
    
    # Chat
    def send_chat_message(self, student_id: int, message: str) -> dict:
        """Send chat message to RAG agent"""
        return self._post("/api/chat", {
            "student_id": student_id,
            "message": message
        })
    
    # Health check
    def health_check(self) -> dict:
        """Check if backend is running"""
        try:
            response = self._get("/")
            if "error" in response:
                return {"status": "offline", "error": response["error"]}
            return response
        except Exception:
            return {"status": "offline"}


# Singleton instance
api_client = APIClient()
