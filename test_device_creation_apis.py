#!/usr/bin/env python3
"""
Test script for Device Creation and ID Update APIs
"""
import requests
import json
import time
from datetime import datetime

BACKEND_URL = "http://localhost:8001"
API = f"{BACKEND_URL}/api"
USER_ID = "test-api-user"

def test_create_device_with_custom_id():
    """Test creating a device with custom ID"""
    print("🏗️  Testing Device Creation with Custom ID...")
    
    # Test data
    custom_id = f"my-camera-{int(time.time())}"
    device_data = {
        "device_id": custom_id,
        "name": "My Security Camera",
        "type": "camera",
        "user_id": USER_ID,
        "location": "Front Door",
        "description": "4K Security Camera with AI detection",
        "settings": {
            "resolution": "4K",
            "night_vision": True,
            "motion_detection": True,
            "recording": False,
            "ai_detection": ["person", "vehicle", "package"]
        },
        "status": "online"
    }
    
    try:
        response = requests.post(f"{API}/devices/create-with-id", params=device_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Device created successfully:")
            print(f"   ID: {result['device']['id']}")
            print(f"   Name: {result['device']['name']}")
            print(f"   Location: {result['device']['location']}")
            print(f"   Settings: {json.dumps(result['device']['settings'], indent=2)}")
            return custom_id
        else:
            print(f"❌ Failed to create device: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating device: {e}")
        return None

def test_update_device_id(old_id):
    """Test updating a device's ID"""
    if not old_id:
        print("⏭️  Skipping ID update test - no device to update")
        return None
        
    print(f"\n🔄 Testing Device ID Update...")
    
    new_id = f"updated-camera-{int(time.time())}"
    
    try:
        response = requests.put(
            f"{API}/devices/{old_id}/update-id",
            params={
                "new_device_id": new_id,
                "preserve_data": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Device ID updated successfully:")
            print(f"   Old ID: {result['old_device_id']}")
            print(f"   New ID: {result['new_device_id']}")
            print(f"   Data preservation: {result['data_preservation']}")
            return new_id
        else:
            print(f"❌ Failed to update device ID: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error updating device ID: {e}")
        return None

def test_create_regular_device():
    """Test creating a device with auto-generated ID"""
    print(f"\n📱 Testing Regular Device Creation...")
    
    device_data = {
        "name": "Auto-ID Sensor",
        "type": "sensor",
        "user_id": USER_ID,
        "location": "Kitchen",
        "description": "Temperature and humidity sensor"
    }
    
    try:
        response = requests.post(f"{API}/devices", json=device_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Regular device created:")
            print(f"   Auto-generated ID: {result['id']}")
            print(f"   Name: {result['name']}")
            return result['id']
        else:
            print(f"❌ Failed to create regular device: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating regular device: {e}")
        return None

def test_send_notification_to_device(device_id, device_name):
    """Test sending notification to the created device"""
    if not device_id:
        print("⏭️  Skipping notification test - no device available")
        return
        
    print(f"\n🔔 Testing Notification to Device...")
    
    notification_data = {
        "user_id": USER_ID,
        "device_id": device_id,
        "title": f"{device_name} Test",
        "body": "This is a test notification for the newly created device!"
    }
    
    try:
        response = requests.post(f"{API}/push/send", json=notification_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Notification sent: {result['message']}")
        else:
            print(f"❌ Failed to send notification: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error sending notification: {e}")

def get_user_devices():
    """Get all devices for the test user"""
    try:
        response = requests.get(f"{API}/devices/{USER_ID}")
        if response.status_code == 200:
            devices = response.json()
            print(f"\n📋 Current devices for user {USER_ID}:")
            for device in devices:
                print(f"   - {device['name']} (ID: {device['id'][:20]}...)")
                print(f"     Type: {device['type']}, Status: {device['status']}")
                if device.get('location'):
                    print(f"     Location: {device['location']}")
            return devices
        else:
            print(f"❌ Failed to get devices: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting devices: {e}")
        return []

def cleanup_test_devices():
    """Clean up test devices"""
    print(f"\n🧹 Cleaning up test devices...")
    devices = get_user_devices()
    
    for device in devices:
        if device['user_id'] == USER_ID:
            try:
                response = requests.delete(f"{API}/devices/{device['id']}")
                if response.status_code == 200:
                    print(f"✅ Deleted: {device['name']}")
                else:
                    print(f"❌ Failed to delete: {device['name']}")
            except Exception as e:
                print(f"❌ Error deleting {device['name']}: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing Device Creation and ID Update APIs")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User ID: {USER_ID}")
    print("=" * 60)
    
    # Test API connectivity
    try:
        response = requests.get(f"{API}/")
        if response.status_code == 200:
            print("✅ Backend API is accessible")
        else:
            print("❌ Backend API is not responding correctly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend API: {e}")
        return False
    
    # Run tests
    device_id_1 = test_create_device_with_custom_id()
    updated_device_id = test_update_device_id(device_id_1)
    device_id_2 = test_create_regular_device()
    
    # Show all devices
    get_user_devices()
    
    # Test notifications
    if updated_device_id:
        test_send_notification_to_device(updated_device_id, "Updated Camera")
    if device_id_2:
        test_send_notification_to_device(device_id_2, "Auto-ID Sensor")
    
    # Print API documentation
    print("\n" + "=" * 60)
    print("📚 API Documentation:")
    print("\n1️⃣ Create Device with Custom ID:")
    print(f"   POST {API}/devices/create-with-id")
    print("   Params: device_id, name, type, user_id, location, description, settings, status")
    
    print("\n2️⃣ Update Device ID:")
    print(f"   PUT {API}/devices/{{old_device_id}}/update-id")
    print("   Params: new_device_id, preserve_data (true/false)")
    
    print("\n3️⃣ Create Device (Auto-ID):")
    print(f"   POST {API}/devices")
    print("   Body: {\"name\": \"...\", \"type\": \"...\", \"user_id\": \"...\"}")
    
    print("\n4️⃣ Send Device Notification:")
    print(f"   POST {API}/push/send")
    print("   Body: {\"user_id\": \"...\", \"device_id\": \"...\", \"title\": \"...\", \"body\": \"...\"}")
    
    # Ask about cleanup
    print(f"\n🤔 Test devices created with user_id: {USER_ID}")
    print("To cleanup manually, run: python test_device_creation_apis.py --cleanup")
    
    print("\n🎉 All tests completed!")
    return True

if __name__ == "__main__":
    main()