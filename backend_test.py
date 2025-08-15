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
        """Test device creation with specific device ID"""
        # First try to create the specific device mentioned in review request
        device_data = {
            "device_id": self.test_device_id,
            "name": "camera202",
            "type": "camera", 
            "user_id": self.user_id,
            "location": "Front Door",
            "description": "Security camera for testing",
            "status": "online"
        }
        
        # Use the create-with-id endpoint
        success, response = self.run_test("Create Specific Device (camera202)", "POST", 
                                        f"devices/create-with-id?device_id={self.test_device_id}&name=camera202&type=camera&user_id={self.user_id}&location=Front Door&description=Security camera for testing", 
                                        200)
        if success:
            self.created_devices.append(self.test_device_id)
            return True, response
        
        # If that fails, try regular device creation
        regular_device_data = {
            "name": "Test Security Camera",
            "type": "camera",
            "user_id": self.user_id
        }
        success, response = self.run_test("Create Regular Device", "POST", "devices", 200, regular_device_data)
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

    def on_websocket_message(self, ws, message):
        """Handle WebSocket messages"""
        try:
            data = json.loads(message)
            self.websocket_messages.append(data)
            print(f"📨 WebSocket received: {data.get('type', 'unknown')}")
        except Exception as e:
            print(f"❌ WebSocket message parse error: {e}")

    def on_websocket_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"❌ WebSocket error: {error}")

    def on_websocket_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        self.websocket_connected = False
        print("🔌 WebSocket connection closed")

    def on_websocket_open(self, ws):
        """Handle WebSocket open"""
        self.websocket_connected = True
        print("🔌 WebSocket connection opened")

    def test_websocket_connection(self):
        """Test WebSocket connectivity"""
        try:
            # Convert https to wss for WebSocket
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
            ws_url = f"{ws_url}/ws/{self.user_id}"
            
            print(f"🔌 Testing WebSocket connection to: {ws_url}")
            
            # Create WebSocket connection
            ws = websocket.WebSocketApp(ws_url,
                                      on_open=self.on_websocket_open,
                                      on_message=self.on_websocket_message,
                                      on_error=self.on_websocket_error,
                                      on_close=self.on_websocket_close)
            
            # Run WebSocket in a separate thread
            wst = threading.Thread(target=ws.run_forever)
            wst.daemon = True
            wst.start()
            
            # Wait for connection
            time.sleep(2)
            
            if self.websocket_connected:
                # Test ping/pong
                ws.send(json.dumps({"type": "ping"}))
                time.sleep(1)
                
                # Test chat message if we have devices
                if self.created_devices:
                    chat_message = {
                        "type": "chat",
                        "device_id": self.created_devices[0],
                        "message": "Hello from WebSocket test!"
                    }
                    ws.send(json.dumps(chat_message))
                    time.sleep(3)  # Wait for AI response
                
                ws.close()
                return self.log_test("WebSocket Connection", True, f"Connected and received {len(self.websocket_messages)} messages")
            else:
                return self.log_test("WebSocket Connection", False, "Failed to connect")
                
        except Exception as e:
            return self.log_test("WebSocket Connection", False, f"Error: {str(e)}")

    def test_openai_integration(self):
        """Test OpenAI integration through chat"""
        if not self.created_devices:
            return self.log_test("OpenAI Integration", False, "No devices available")
            
        message_data = {
            "device_id": self.created_devices[0],
            "message": "What is your purpose as a security camera AI?",
            "sender": "user"
        }
        
        success, response = self.run_test("OpenAI Chat Integration", "POST", f"chat/send?user_id={self.user_id}", 200, message_data)
        
        if success and response.get('ai_response'):
            ai_message = response['ai_response'].get('message', '')
            if ai_message and len(ai_message) > 10:  # Basic check for meaningful response
                return self.log_test("OpenAI Response Quality", True, f"AI responded with {len(ai_message)} characters")
            else:
                return self.log_test("OpenAI Response Quality", False, "AI response too short or empty")
        
        return success

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
        print(f"Test Device ID: {self.test_device_id}")
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
        
        # OpenAI integration test
        print("\n🤖 Testing OpenAI Integration...")
        self.test_openai_integration()

        # Notification tests
        print("\n🔔 Testing Notifications...")
        self.test_get_notifications()
        self.test_simulate_device_notification()
        
        # Wait a moment for notification to be processed
        time.sleep(1)
        self.test_mark_notification_read()

        # WebSocket tests
        print("\n🔌 Testing WebSocket Connectivity...")
        self.test_websocket_connection()

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