#!/usr/bin/env python3
"""Test script for authentication flow"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"


def test_auth_flow():
    print("1. Testing Registration...")
    # Register a new user
    register_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpass123",
    }

    response = requests.post(f"{BASE_URL}/register", json=register_data)
    if response.status_code == 201:
        print("✓ User registered successfully")
        print(f"  User: {response.json()}")
    else:
        print(f"✗ Registration failed: {response.json()}")

    print("\n2. Testing Login...")
    # Login
    login_data = {"username": "testuser2", "password": "testpass123"}

    response = requests.post(
        f"{BASE_URL}/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        print("✓ Login successful")
        print(f"  Token: {token[:50]}...")
    else:
        print(f"✗ Login failed: {response.json()}")
        return

    # Set auth headers
    headers = {"Authorization": f"Bearer {token}"}

    print("\n3. Testing /users/me...")
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    if response.status_code == 200:
        print("✓ User profile retrieved")
        print(f"  Profile: {response.json()}")
    else:
        print(f"✗ Failed to get profile: {response.json()}")

    print("\n4. Testing Task Creation...")
    task_data = {
        "title": "Test task for user2",
        "description": "This is a test task",
        "status": "todo",
    }

    response = requests.post(f"{BASE_URL}/tasks", json=task_data, headers=headers)
    if response.status_code == 201:
        task = response.json()
        task_id = task["id"]
        print("✓ Task created successfully")
        print(f"  Task: {task}")
    else:
        print(f"✗ Task creation failed: {response.json()}")
        return

    print("\n5. Testing Task List...")
    response = requests.get(f"{BASE_URL}/tasks", headers=headers)
    if response.status_code == 200:
        tasks = response.json()
        print(f"✓ Retrieved {len(tasks)} tasks")
        for task in tasks:
            print(f"  - {task['title']} ({task['status']})")
    else:
        print(f"✗ Failed to list tasks: {response.json()}")

    print("\n6. Testing Unauthorized Access...")
    response = requests.get(f"{BASE_URL}/tasks")
    if response.status_code == 401:
        print("✓ Unauthorized access properly rejected")
    else:
        print(f"✗ Security issue: got status {response.status_code}")

    print("\n7. Testing Task Update...")
    update_data = {"status": "done"}
    response = requests.put(
        f"{BASE_URL}/tasks/{task_id}", json=update_data, headers=headers
    )
    if response.status_code == 200:
        print("✓ Task updated successfully")
        print(f"  Updated task: {response.json()}")
    else:
        print(f"✗ Task update failed: {response.json()}")

    print("\n8. Testing Task Deletion...")
    response = requests.delete(f"{BASE_URL}/tasks/{task_id}", headers=headers)
    if response.status_code == 204:
        print("✓ Task deleted successfully")
    else:
        print(f"✗ Task deletion failed: {response.status_code}")

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    test_auth_flow()
