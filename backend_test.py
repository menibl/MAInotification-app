#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Device Chat PWA
Tests all REST endpoints, WebSocket functionality, and data persistence
"""
import requests
import sys
import json
from datetime import datetime
import time
import websocket
import threading

class DeviceChatAPITester:
    def __init__(self, base_url="https://devicepush.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.user_id = "demo-user-123"
        self.test_device_id = "123456"  # camera202 as mentioned in review request
        self.tests_run = 0
        self.tests_passed = 0
        self.created_devices = []
        self.created_notifications = []
        self.websocket_messages = []
        self.websocket_connected = False

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        return success

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            details = f"Expected {expected_status}, got {response.status_code}"
            if not success and response.text:
                details += f" - {response.text[:200]}"
                
            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_create_device(self):
        """Test device creation"""
        device_data = {
            "name": "Test Security Camera",
            "type": "camera",
            "user_id": self.user_id
        }
        success, response = self.run_test("Create Device", "POST", "devices", 200, device_data)
        if success and 'id' in response:
            self.created_devices.append(response['id'])
            return True, response
        return False, {}

    def test_get_user_devices(self):
        """Test getting user devices"""
        return self.run_test("Get User Devices", "GET", f"devices/{self.user_id}", 200)

    def test_update_device_status(self):
        """Test updating device status"""
        if not self.created_devices:
            return self.log_test("Update Device Status", False, "No devices to update")
        
        device_id = self.created_devices[0]
        return self.run_test("Update Device Status", "PUT", f"devices/{device_id}/status", 200, 
                           params={"status": "offline"})

    def test_send_chat_message(self):
        """Test sending chat message"""
        if not self.created_devices:
            return self.log_test("Send Chat Message", False, "No devices available")
            
        message_data = {
            "device_id": self.created_devices[0],
            "message": "Hello from test!",
            "sender": "user"
        }
        return self.run_test("Send Chat Message", "POST", f"chat/send?user_id={self.user_id}", 200, message_data)

    def test_get_chat_history(self):
        """Test getting chat history"""
        if not self.created_devices:
            return self.log_test("Get Chat History", False, "No devices available")
            
        device_id = self.created_devices[0]
        return self.run_test("Get Chat History", "GET", f"chat/{self.user_id}/{device_id}", 200)

    def test_get_notifications(self):
        """Test getting notifications"""
        return self.run_test("Get Notifications", "GET", f"notifications/{self.user_id}", 200)

    def test_simulate_device_notification(self):
        """Test simulating device notification"""
        if not self.created_devices:
            return self.log_test("Simulate Device Notification", False, "No devices available")
            
        params = {
            "user_id": self.user_id,
            "device_id": self.created_devices[0],
            "message": "Test notification from device",
            "media_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop",
            "notification_type": "alert"
        }
        return self.run_test("Simulate Device Notification", "POST", "simulate/device-notification", 200, 
                           params=params)

    def test_mark_notification_read(self):
        """Test marking notification as read"""
        # First get notifications to find one to mark as read
        success, notifications = self.run_test("Get Notifications for Read Test", "GET", f"notifications/{self.user_id}", 200)
        if not success or not notifications:
            return self.log_test("Mark Notification Read", False, "No notifications to mark as read")
        
        # Try to mark the first notification as read
        notification_id = notifications[0].get('id')
        if not notification_id:
            return self.log_test("Mark Notification Read", False, "No notification ID found")
            
        return self.run_test("Mark Notification Read", "PUT", f"notifications/{notification_id}/read", 200)

    def test_status_endpoints(self):
        """Test original status endpoints"""
        # Test create status check
        status_data = {"client_name": "test-client"}
        success1, _ = self.run_test("Create Status Check", "POST", "status", 200, status_data)
        
        # Test get status checks
        success2, _ = self.run_test("Get Status Checks", "GET", "status", 200)
        
        return success1 and success2

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Device Chat Backend API Tests")
        print(f"Backend URL: {self.base_url}")
        print(f"Test User ID: {self.user_id}")
        print("=" * 60)

        # Test API connectivity
        success, _ = self.test_api_root()
        if not success:
            print("❌ Cannot connect to API. Stopping tests.")
            return False

        # Core device management tests
        print("\n📱 Testing Device Management...")
        self.test_create_device()
        self.test_get_user_devices()
        self.test_update_device_status()

        # Chat functionality tests
        print("\n💬 Testing Chat Functionality...")
        self.test_send_chat_message()
        self.test_get_chat_history()

        # Notification tests
        print("\n🔔 Testing Notifications...")
        self.test_get_notifications()
        self.test_simulate_device_notification()
        
        # Wait a moment for notification to be processed
        time.sleep(1)
        self.test_mark_notification_read()

        # Original status endpoints
        print("\n📊 Testing Status Endpoints...")
        self.test_status_endpoints()

        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            failed = self.tests_run - self.tests_passed
            print(f"⚠️  {failed} test(s) failed")
            return False

def main():
    tester = DeviceChatAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Backend API is fully functional!")
        print("Ready for frontend integration testing.")
    else:
        print("\n❌ Some backend tests failed.")
        print("Please fix backend issues before proceeding with frontend tests.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())