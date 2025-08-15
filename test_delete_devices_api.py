#!/usr/bin/env python3
"""
Test script for Delete All Devices API
"""
import requests
import json
import time
from datetime import datetime

BACKEND_URL = "http://localhost:8001"
API = f"{BACKEND_URL}/api"
TEST_USER_ID = "delete-test-user"

def create_test_devices():
    """Create some test devices to delete"""
    print("🏗️  Creating test devices...")
    
    devices = [
        {"device_id": "TEST_CAM_001", "name": "Test Camera 1", "type": "camera"},
        {"device_id": "TEST_CAM_002", "name": "Test Camera 2", "type": "camera"},
        {"device_id": "TEST_SENSOR_001", "name": "Test Sensor 1", "type": "sensor"},
        {"device_id": "TEST_SENSOR_002", "name": "Test Sensor 2", "type": "sensor"},
    ]
    
    created_devices = []
    
    for device in devices:
        try:
            response = requests.post(
                f"{API}/devices/create-with-id",
                params={
                    "device_id": device["device_id"],
                    "name": device["name"],
                    "type": device["type"],
                    "user_id": TEST_USER_ID,
                    "location": "Test Location",
                    "description": "Test device for deletion testing"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                created_devices.append(result["device"])
                print(f"✅ Created: {device['name']} (ID: {device['device_id']})")
            else:
                print(f"❌ Failed to create: {device['name']}")
                
        except Exception as e:
            print(f"❌ Error creating {device['name']}: {e}")
    
    return created_devices

def create_test_notifications(devices):
    """Create test notifications for the devices"""
    print(f"\n🔔 Creating test notifications...")
    
    created_notifications = 0
    
    for device in devices:
        try:
            response = requests.post(f"{API}/push/send", json={
                "user_id": TEST_USER_ID,
                "device_id": device["id"],
                "title": f"Test Alert from {device['name']}",
                "body": f"This is a test notification from {device['name']}"
            })
            
            if response.status_code == 200:
                created_notifications += 1
                print(f"✅ Created notification for: {device['name']}")
            else:
                print(f"❌ Failed to create notification for: {device['name']}")
                
        except Exception as e:
            print(f"❌ Error creating notification for {device['name']}: {e}")
    
    return created_notifications

def get_user_stats(user_id):
    """Get statistics for a user"""
    try:
        # Get devices
        devices_response = requests.get(f"{API}/devices/{user_id}")
        devices_count = len(devices_response.json()) if devices_response.status_code == 200 else 0
        
        # Get notifications
        notifications_response = requests.get(f"{API}/notifications/{user_id}")
        notifications_count = len(notifications_response.json()) if notifications_response.status_code == 200 else 0
        
        # Get push subscriptions
        subscriptions_response = requests.get(f"{API}/push/subscriptions/{user_id}")
        subscriptions_count = len(subscriptions_response.json()) if subscriptions_response.status_code == 200 else 0
        
        return {
            "devices": devices_count,
            "notifications": notifications_count,
            "push_subscriptions": subscriptions_count
        }
        
    except Exception as e:
        print(f"❌ Error getting user stats: {e}")
        return {"devices": 0, "notifications": 0, "push_subscriptions": 0}

def test_safe_delete():
    """Test safe delete (devices only)"""
    print(f"\n🛡️  Testing Safe Delete (devices only)...")
    
    try:
        response = requests.delete(f"{API}/devices/user/{TEST_USER_ID}/delete-all-safe")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Safe delete successful:")
            print(f"   Deleted devices: {result['deleted_count']}")
            print(f"   Message: {result['message']}")
            if result.get('note'):
                print(f"   Note: {result['note']}")
            return True
        else:
            print(f"❌ Safe delete failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in safe delete: {e}")
        return False

def test_full_delete():
    """Test full delete with confirmation"""
    print(f"\n💥 Testing Full Delete (with related data)...")
    
    try:
        response = requests.delete(
            f"{API}/devices/user/{TEST_USER_ID}/delete-all",
            params={
                "delete_notifications": True,
                "delete_chat_messages": True,
                "delete_push_subscriptions": False,
                "confirm_deletion": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Full delete successful:")
            print(f"   Deleted devices: {result['deleted_count']}")
            print(f"   Related data deleted: {json.dumps(result['related_data_deleted'], indent=2)}")
            return True
        else:
            print(f"❌ Full delete failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in full delete: {e}")
        return False

def test_delete_without_confirmation():
    """Test delete without confirmation (should fail)"""
    print(f"\n⚠️  Testing Delete Without Confirmation (should fail)...")
    
    try:
        response = requests.delete(f"{API}/devices/user/{TEST_USER_ID}/delete-all")
        
        if response.status_code == 400:
            result = response.json()
            print(f"✅ Correctly rejected without confirmation:")
            print(f"   Error: {result['detail']}")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing confirmation: {e}")
        return False

def main():
    """Run all delete API tests"""
    print("🗑️  Testing Delete All Devices APIs")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
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
    
    # Phase 1: Test Safe Delete
    print(f"\n{'='*20} PHASE 1: SAFE DELETE TEST {'='*20}")
    
    # Create test data
    devices = create_test_devices()
    notifications_count = create_test_notifications(devices)
    
    print(f"\n📊 Before safe delete:")
    stats_before = get_user_stats(TEST_USER_ID)
    print(f"   Devices: {stats_before['devices']}")
    print(f"   Notifications: {stats_before['notifications']}")
    print(f"   Push Subscriptions: {stats_before['push_subscriptions']}")
    
    # Test safe delete
    safe_delete_success = test_safe_delete()
    
    print(f"\n📊 After safe delete:")
    stats_after_safe = get_user_stats(TEST_USER_ID)
    print(f"   Devices: {stats_after_safe['devices']}")
    print(f"   Notifications: {stats_after_safe['notifications']} (should be preserved)")
    print(f"   Push Subscriptions: {stats_after_safe['push_subscriptions']}")
    
    # Phase 2: Test Full Delete
    print(f"\n{'='*20} PHASE 2: FULL DELETE TEST {'='*20}")
    
    # Create test data again
    devices = create_test_devices()
    notifications_count = create_test_notifications(devices)
    
    print(f"\n📊 Before full delete:")
    stats_before_full = get_user_stats(TEST_USER_ID)
    print(f"   Devices: {stats_before_full['devices']}")
    print(f"   Notifications: {stats_before_full['notifications']}")
    print(f"   Push Subscriptions: {stats_before_full['push_subscriptions']}")
    
    # Test delete without confirmation first
    confirmation_test = test_delete_without_confirmation()
    
    # Test full delete
    full_delete_success = test_full_delete()
    
    print(f"\n📊 After full delete:")
    stats_after_full = get_user_stats(TEST_USER_ID)
    print(f"   Devices: {stats_after_full['devices']}")
    print(f"   Notifications: {stats_after_full['notifications']} (should be deleted)")
    print(f"   Push Subscriptions: {stats_after_full['push_subscriptions']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"   Safe Delete: {'✅ PASSED' if safe_delete_success else '❌ FAILED'}")
    print(f"   Confirmation Check: {'✅ PASSED' if confirmation_test else '❌ FAILED'}")
    print(f"   Full Delete: {'✅ PASSED' if full_delete_success else '❌ FAILED'}")
    
    # API Documentation
    print("\n" + "=" * 60)
    print("📚 Delete APIs Documentation:")
    
    print("\n🛡️  Safe Delete (devices only):")
    print(f"   DELETE {API}/devices/user/{{user_id}}/delete-all-safe")
    print("   - Deletes only devices")
    print("   - Preserves notifications, messages, subscriptions")
    print("   - No confirmation required")
    
    print("\n💥 Full Delete (with related data):")
    print(f"   DELETE {API}/devices/user/{{user_id}}/delete-all")
    print("   Params:")
    print("   - confirm_deletion=true (required)")
    print("   - delete_notifications=true/false (default: true)")
    print("   - delete_chat_messages=true/false (default: true)")
    print("   - delete_push_subscriptions=true/false (default: false)")
    
    print(f"\n🎯 For YOUR use case (demo-user-123):")
    print("   Safe: DELETE /api/devices/user/demo-user-123/delete-all-safe")
    print("   Full: DELETE /api/devices/user/demo-user-123/delete-all?confirm_deletion=true")
    
    all_passed = safe_delete_success and confirmation_test and full_delete_success
    print(f"\n🎉 All tests {'PASSED' if all_passed else 'had issues'}!")
    
    return all_passed

if __name__ == "__main__":
    main()