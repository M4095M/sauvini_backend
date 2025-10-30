#!/usr/bin/env python3
"""
Quick test script for the Django backend API
"""
import requests
import json

BASE_URL = "http://localhost:4000/api/v1"

def test_health():
    """Test health check endpoint"""
    print("🔍 Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_student_registration():
    """Test student registration"""
    print("👨‍🎓 Testing Student Registration...")
    import time
    timestamp = int(time.time())
    data = {
        "first_name": "Test",
        "last_name": "Student",
        "wilaya": "Algiers",
        "phone_number": "0555123456",
        "academic_stream": "Mathematics",
        "password": "testpassword123",
        "password_confirm": "testpassword123",
        "email": f"test.student.{timestamp}@example.com"
    }
    response = requests.post(f"{BASE_URL}/auth/student/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    return response.json().get('student_id')

def test_student_login():
    """Test student login"""
    print("🔐 Testing Student Login...")
    data = {
        "email": "test.student@example.com",
        "password": "testpassword123",
        "user_type": "student"
    }
    response = requests.post(f"{BASE_URL}/auth/student/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    return response.json().get('access_token')

def test_admin_login():
    """Test admin login"""
    print("👨‍💼 Testing Admin Login...")
    data = {
        "email": "admin@sauvini.com",
        "password": "Admin123!",
        "user_type": "admin"
    }
    response = requests.post(f"{BASE_URL}/auth/admin/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    return response.json().get('access_token')

def test_protected_endpoint(token):
    """Test protected endpoint with token"""
    print("🔒 Testing Protected Endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/admin/all-professors", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("🚀 Starting Django Backend API Tests\n")
    
    # Test health check
    test_health()
    
    # Test student registration
    student_id = test_student_registration()
    
    # Test student login
    student_token = test_student_login()
    
    # Test admin login
    admin_token = test_admin_login()
    
    # Test protected endpoint
    if admin_token:
        test_protected_endpoint(admin_token)
    
    print("✅ All tests completed!")
