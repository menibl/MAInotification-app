#!/usr/bin/env python3
"""
Test script for new Device Chat APIs:
1. Push Notification API
2. Bulk Device Update API
"""
import requests
import json
import sys
from datetime import datetime

BACKEND_URL = "http://localhost:8001"
API = f"{BACKEND_URL}/api"
USER_ID = "test-user-123"

def test_push_notification_api():
    """Test the push notification API endpoints"""
    print("🔔 Testing Push Notification API...")
    
    # Test 1: Subscribe to push notifications
    print("\n1. Testing push subscription...")
    subscription_data = {
        "user_id": USER_ID,
        "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-123",
        "keys": {
            "p256dh": "BDgJHFHHDHg789H",
            "auth": "auth123key"
        }
    }
    
    try:
        response = requests.post(f"{API}/push/subscribe", json=subscription_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Push subscription created: {result['subscription_id']}")
            subscription_id = result['subscription_id']
        else:
            print(f"❌ Push subscription failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Push subscription error: {e}")
        return False
    
    # Test 2: Get user subscriptions
    print("\n2. Testing get push subscriptions...")
    try:
        response = requests.get(f"{API}/push/subscriptions/{USER_ID}")
        if response.status_code == 200:
            subscriptions = response.json()
            print(f"✅ Found {len(subscriptions)} push subscription(s)")
        else:
            print(f"❌ Get subscriptions failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Get subscriptions error: {e}")
    
    # Test 3: Send push notification
    print("\n3. Testing send push notification...")
    notification_data = {
        "user_id": USER_ID,
        "title": "Test Notification",
        "body": "This is a test push notification from the API",
        "icon": "/manifest-icon-192.png",
        "data": {
            "test": True,
            "timestamp": datetime.utcnow().isoformat()
        },
        "actions": [
            {"action": "view", "title": "View"},
            {"action": "dismiss", "title": "Dismiss"}
        ]
    }
    
    try:
        response = requests.post(f"{API}/push/send", json=notification_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Push notification sent: {result['message']}")
            print(f"   Sent: {result['sent_count']}, Failed: {result['failed_count']}")
        else:
            print(f"❌ Send push notification failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Send push notification error: {e}")
    
    # Test 4: Unsubscribe from push notifications
    print("\n4. Testing push unsubscribe...")
    try:
        response = requests.delete(f"{API}/push/unsubscribe/{USER_ID}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Push unsubscribe: {result['message']}")
        else:
            print(f"❌ Push unsubscribe failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Push unsubscribe error: {e}")
    
    return True

def test_device_update_api():
    """Test the device update API endpoints"""
    print("\n📱 Testing Device Update API...")
    
    # First, create some test devices
    print("\n1. Creating test devices...")
    device_ids = []
    test_devices = [
        {"name": "Test Camera 1", "type": "camera", "user_id": USER_ID},
        {"name": "Test Sensor 1", "type": "sensor", "user_id": USER_ID},
        {"name": "Test Device 1", "type": "other", "user_id": USER_ID}
    ]
    
    for device_data in test_devices:
        try:
            response = requests.post(f"{API}/devices", json=device_data)
            if response.status_code == 200:
                device = response.json()
                device_ids.append(device['id'])
                print(f"✅ Created device: {device['name']} (ID: {device['id']})")
            else:
                print(f"❌ Failed to create device: {device_data['name']}")
        except Exception as e:
            print(f"❌ Device creation error: {e}")
    
    if not device_ids:
        print("❌ No devices created, skipping update tests")
        return False
    
    # Test 2: Update single device
    print("\n2. Testing single device update...")
    update_data = {
        "name": "Updated Test Camera",
        "status": "offline",
        "location": "Living Room",
        "description": "Updated camera description",
        "settings": {"resolution": "1080p", "night_vision": True}
    }
    
    try:
        response = requests.put(f"{API}/devices/{device_ids[0]}", json=update_data)
        if response.status_code == 200:
            updated_device = response.json()
            print(f"✅ Device updated: {updated_device['name']}")
            print(f"   Location: {updated_device.get('location', 'N/A')}")
            print(f"   Status: {updated_device['status']}")
        else:
            print(f"❌ Single device update failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Single device update error: {e}")
    
    # Test 3: Bulk device update
    print("\n3. Testing bulk device update...")
    bulk_update_data = {
        "device_updates": [
            {
                "device_id": device_ids[0],
                "updates": {
                    "status": "online",
                    "settings": {"motion_detection": True}
                }
            },
            {
                "device_id": device_ids[1],
                "updates": {
                    "name": "Updated Sensor Name",
                    "location": "Kitchen",
                    "description": "Temperature and humidity sensor"
                }
            },
            {
                "device_id": device_ids[2],
                "updates": {
                    "type": "smart_device",
                    "status": "online"
                }
            }
        ]
    }
    
    try:
        response = requests.put(f"{API}/devices/bulk-update", json=bulk_update_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Bulk update completed:")
            print(f"   Updated: {result['updated_count']} devices")
            print(f"   Failed: {len(result['failed_updates'])} devices")
            print(f"   Total attempted: {result['total_attempted']}")
            
            if result['failed_updates']:
                print("   Failed updates:")
                for fail in result['failed_updates']:
                    print(f"     - {fail}")
        else:
            print(f"❌ Bulk device update failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Bulk device update error: {e}")
    
    # Test 4: Delete test devices
    print("\n4. Cleaning up test devices...")
    for device_id in device_ids:
        try:
            response = requests.delete(f"{API}/devices/{device_id}")
            if response.status_code == 200:
                print(f"✅ Deleted device: {device_id}")
            else:
                print(f"❌ Failed to delete device: {device_id}")
        except Exception as e:
            print(f"❌ Device deletion error: {e}")
    
    return True

def main():
    """Run all API tests"""
    print("🚀 Testing New Device Chat APIs")
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
    push_success = test_push_notification_api()
    device_success = test_device_update_api()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"Push Notification API: {'✅ PASSED' if push_success else '❌ FAILED'}")
    print(f"Device Update API: {'✅ PASSED' if device_success else '❌ FAILED'}")
    
    if push_success and device_success:
        print("\n🎉 All API tests passed!")
        print("\n📋 API Usage Examples:")
        print("\n1. Send Push Notification:")
        print(f"   POST {API}/push/send")
        print("   Body: {\"user_id\": \"user123\", \"title\": \"Alert\", \"body\": \"Device notification\"}")
        
        print("\n2. Bulk Update Devices:")
        print(f"   PUT {API}/devices/bulk-update")
        print("   Body: {\"device_updates\": [{\"device_id\": \"dev123\", \"updates\": {\"status\": \"online\"}}]}")
        
        return True
    else:
        print("\n❌ Some API tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)