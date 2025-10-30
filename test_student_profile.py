#!/usr/bin/env python3
"""
Test script for student profile endpoints
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "test.student@example.com"
TEST_PASSWORD = "testpassword123"

def test_student_profile_endpoints():
    """Test student profile management endpoints"""
    print("🧪 Testing Student Profile Endpoints")
    print("=" * 50)
    
    # Step 1: Register a test student
    print("\n1. Registering test student...")
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "first_name": "Test",
        "last_name": "Student",
        "wilaya": "Algiers",
        "phone_number": "0555123456",
        "academic_stream": "Mathematics"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/student/register", json=register_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            print("   ✅ Student registered successfully")
        else:
            print(f"   ❌ Registration failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return False
    
    # Step 2: Login to get tokens
    print("\n2. Logging in...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/student/login", json=login_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access')
            print("   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False
    
    # Set up headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Step 3: Get student profile
    print("\n3. Getting student profile...")
    try:
        response = requests.get(f"{BASE_URL}/student/profile", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Profile retrieved successfully")
            print(f"   Student: {data['data']['first_name']} {data['data']['last_name']}")
            print(f"   Email: {data['data']['email']}")
            print(f"   Academic Stream: {data['data']['academic_stream']}")
        else:
            print(f"   ❌ Get profile failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Get profile error: {e}")
        return False
    
    # Step 4: Update student profile
    print("\n4. Updating student profile...")
    update_data = {
        "first_name": "Updated",
        "last_name": "Student",
        "wilaya": "Oran",
        "phone_number": "0555987654"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/student/profile/update", json=update_data, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Profile updated successfully")
            print(f"   Updated name: {data['data']['first_name']} {data['data']['last_name']}")
            print(f"   Updated wilaya: {data['data']['wilaya']}")
        else:
            print(f"   ❌ Update profile failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Update profile error: {e}")
        return False
    
    # Step 5: Get student by ID (public endpoint)
    print("\n5. Getting student by ID (public)...")
    try:
        # First get the student ID from profile
        profile_response = requests.get(f"{BASE_URL}/student/profile", headers=headers)
        student_id = profile_response.json()['data']['id']
        
        response = requests.get(f"{BASE_URL}/student/{student_id}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Student retrieved by ID successfully")
            print(f"   Student: {data['data']['first_name']} {data['data']['last_name']}")
        else:
            print(f"   ❌ Get student by ID failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Get student by ID error: {e}")
        return False
    
    print("\n✅ All student profile endpoints working correctly!")
    return True

if __name__ == "__main__":
    success = test_student_profile_endpoints()
    sys.exit(0 if success else 1)

