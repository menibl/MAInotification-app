#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Device Chat PWA
Tests all REST endpoints, WebSocket functionality, and data persistence
Enhanced with File Upload and Message Referencing Tests
"""
import requests
import sys
import json
from datetime import datetime
import time
import websocket
import threading
import os
import tempfile
from pathlib import Path

class DeviceChatAPITester:
    def __init__(self, base_url="https://8b6b2575-d42f-4bc0-80fe-15fb1cd93712.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.user_id = "demo-user-123"
        self.test_device_id = "123456"  # camera202 as mentioned in review request
        self.tests_run = 0
        self.tests_passed = 0
        self.created_devices = []
        self.created_notifications = []
        self.uploaded_files = []  # Track uploaded files for cleanup
        self.chat_messages = []   # Track chat messages for referencing tests
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
            
        url = f"{self.api_url}/chat/send"
        params = {
            "user_id": self.user_id,
            "device_id": self.created_devices[0],
            "message": "Hello from test!",
            "sender": "user"
        }
        
        try:
            response = requests.post(url, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and result.get('message_id'):
                    self.chat_messages.append(result['message_id'])
                    self.log_test("Send Chat Message", True, f"Message ID: {result['message_id']}")
                    return True, result
                else:
                    self.log_test("Send Chat Message", False, "Invalid response format")
                    return False, {}
            else:
                self.log_test("Send Chat Message", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Send Chat Message", False, f"Error: {str(e)}")
            return False, {}

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
            
        url = f"{self.api_url}/chat/send"
        params = {
            "user_id": self.user_id,
            "device_id": self.created_devices[0],
            "message": "What is your purpose as a security camera AI?",
            "sender": "user"
        }
        
        try:
            response = requests.post(url, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and result.get('ai_response'):
                    ai_message = result['ai_response'].get('message', '')
                    if ai_message and len(ai_message) > 10:  # Basic check for meaningful response
                        self.log_test("OpenAI Response Quality", True, f"AI responded with {len(ai_message)} characters")
                        return True, result
                    else:
                        self.log_test("OpenAI Response Quality", False, "AI response too short or empty")
                        return False, {}
                else:
                    self.log_test("OpenAI Integration", False, "No AI response in result")
                    return False, {}
            else:
                self.log_test("OpenAI Integration", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("OpenAI Integration", False, f"Error: {str(e)}")
            return False, {}

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

    def create_test_file(self, filename, content, size_mb=None):
        """Create a temporary test file"""
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        if size_mb:
            # Create file of specific size
            with open(file_path, 'wb') as f:
                f.write(b'0' * (size_mb * 1024 * 1024))
        else:
            # Create file with specific content
            with open(file_path, 'w') as f:
                f.write(content)
        
        return file_path

    def test_file_upload_small(self):
        """Test uploading a small text file"""
        # Create a small test file
        test_content = "This is a test file for upload functionality.\nIt contains multiple lines.\nTesting file upload API."
        file_path = self.create_test_file("test_document.txt", test_content)
        
        try:
            url = f"{self.api_url}/files/upload"
            
            with open(file_path, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                data = {
                    'user_id': self.user_id,
                    'device_id': self.test_device_id
                }
                
                response = requests.post(url, files=files, data=data)
                
            success = response.status_code == 200
            if success:
                result = response.json()
                if result.get('success') and result.get('file_id'):
                    self.uploaded_files.append(result['file_id'])
                    self.log_test("Upload Small File", True, f"File ID: {result['file_id']}")
                    return True, result
                else:
                    self.log_test("Upload Small File", False, "Invalid response format")
                    return False, {}
            else:
                self.log_test("Upload Small File", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Upload Small File", False, f"Error: {str(e)}")
            return False, {}
        finally:
            # Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_file_upload_image(self):
        """Test uploading an image file"""
        # Create a small fake image file (just binary data)
        file_path = self.create_test_file("test_image.jpg", "")
        
        # Write some binary data to simulate an image
        with open(file_path, 'wb') as f:
            # Simple fake JPEG header + data
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00')
            f.write(b'0' * 1000)  # 1KB of fake image data
        
        try:
            url = f"{self.api_url}/files/upload"
            
            with open(file_path, 'rb') as f:
                files = {'file': ('test_image.jpg', f, 'image/jpeg')}
                data = {
                    'user_id': self.user_id,
                    'device_id': self.test_device_id
                }
                
                response = requests.post(url, files=files, data=data)
                
            success = response.status_code == 200
            if success:
                result = response.json()
                if result.get('success') and result.get('file_id'):
                    self.uploaded_files.append(result['file_id'])
                    self.log_test("Upload Image File", True, f"File ID: {result['file_id']}")
                    return True, result
                else:
                    self.log_test("Upload Image File", False, "Invalid response format")
                    return False, {}
            else:
                self.log_test("Upload Image File", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Upload Image File", False, f"Error: {str(e)}")
            return False, {}
        finally:
            # Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_file_upload_large(self):
        """Test uploading a large file (close to 100MB limit)"""
        # Create a 50MB file to test large file handling
        file_path = self.create_test_file("large_test_file.bin", "", size_mb=50)
        
        try:
            url = f"{self.api_url}/files/upload"
            
            with open(file_path, 'rb') as f:
                files = {'file': ('large_test_file.bin', f, 'application/octet-stream')}
                data = {
                    'user_id': self.user_id,
                    'device_id': self.test_device_id
                }
                
                # Set a longer timeout for large file upload
                response = requests.post(url, files=files, data=data, timeout=120)
                
            success = response.status_code == 200
            if success:
                result = response.json()
                if result.get('success') and result.get('file_id'):
                    self.uploaded_files.append(result['file_id'])
                    self.log_test("Upload Large File (50MB)", True, f"File ID: {result['file_id']}")
                    return True, result
                else:
                    self.log_test("Upload Large File (50MB)", False, "Invalid response format")
                    return False, {}
            else:
                self.log_test("Upload Large File (50MB)", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Upload Large File (50MB)", False, f"Error: {str(e)}")
            return False, {}
        finally:
            # Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_file_upload_oversized(self):
        """Test uploading a file that exceeds 100MB limit"""
        # Create a 101MB file to test size limit
        file_path = self.create_test_file("oversized_file.bin", "", size_mb=101)
        
        try:
            url = f"{self.api_url}/files/upload"
            
            with open(file_path, 'rb') as f:
                files = {'file': ('oversized_file.bin', f, 'application/octet-stream')}
                data = {
                    'user_id': self.user_id,
                    'device_id': self.test_device_id
                }
                
                response = requests.post(url, files=files, data=data, timeout=120)
                
            # Should return 413 (Payload Too Large)
            success = response.status_code == 413
            if success:
                self.log_test("Upload Oversized File (101MB)", True, "Correctly rejected oversized file")
                return True, {}
            else:
                self.log_test("Upload Oversized File (101MB)", False, f"Expected 413, got {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Upload Oversized File (101MB)", False, f"Error: {str(e)}")
            return False, {}
        finally:
            # Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_get_file(self):
        """Test retrieving uploaded files"""
        if not self.uploaded_files:
            return self.log_test("Get File", False, "No uploaded files to retrieve")
        
        file_id = self.uploaded_files[0]
        url = f"{self.api_url}/files/{file_id}"
        
        try:
            response = requests.get(url)
            success = response.status_code == 200
            
            if success:
                # Check if we got file content
                content_length = len(response.content)
                self.log_test("Get File", True, f"Retrieved file with {content_length} bytes")
                return True, response.content
            else:
                self.log_test("Get File", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Get File", False, f"Error: {str(e)}")
            return False, {}

    def test_get_user_files(self):
        """Test getting all files for a user"""
        url = f"{self.api_url}/files/user/{self.user_id}"
        
        try:
            response = requests.get(url)
            success = response.status_code == 200
            
            if success:
                files = response.json()
                file_count = len(files) if isinstance(files, list) else 0
                self.log_test("Get User Files", True, f"Found {file_count} files for user")
                return True, files
            else:
                self.log_test("Get User Files", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Get User Files", False, f"Error: {str(e)}")
            return False, {}

    def test_delete_file(self):
        """Test deleting an uploaded file"""
        if not self.uploaded_files:
            return self.log_test("Delete File", False, "No uploaded files to delete")
        
        # Delete the last uploaded file
        file_id = self.uploaded_files.pop()
        url = f"{self.api_url}/files/{file_id}"
        
        try:
            response = requests.delete(url)
            success = response.status_code == 200
            
            if success:
                self.log_test("Delete File", True, f"Deleted file {file_id}")
                return True, response.json()
            else:
                self.log_test("Delete File", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Delete File", False, f"Error: {str(e)}")
            return False, {}

    def test_enhanced_chat_with_files(self):
        """Test sending chat message with file attachments"""
        if not self.uploaded_files:
            return self.log_test("Enhanced Chat with Files", False, "No uploaded files available")
        
        if not self.created_devices:
            return self.log_test("Enhanced Chat with Files", False, "No devices available")
        
        url = f"{self.api_url}/chat/send"
        params = {
            'user_id': self.user_id,
            'device_id': self.created_devices[0],
            'message': 'I have attached some files for you to analyze. Can you tell me about them?',
            'sender': 'user',
            'file_ids': self.uploaded_files[:2]  # Attach first 2 files
        }
        
        try:
            response = requests.post(url, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and result.get('ai_response'):
                    message_id = result.get('message_id')
                    if message_id:
                        self.chat_messages.append(message_id)
                    ai_message = result['ai_response'].get('message', '')
                    self.log_test("Enhanced Chat with Files", True, f"AI responded with {len(ai_message)} characters")
                    return True, result
                else:
                    self.log_test("Enhanced Chat with Files", False, "Invalid response format")
                    return False, {}
            else:
                self.log_test("Enhanced Chat with Files", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Enhanced Chat with Files", False, f"Error: {str(e)}")
            return False, {}

    def test_chat_with_message_references(self):
        """Test sending chat message with referenced messages"""
        if not self.chat_messages:
            return self.log_test("Chat with Message References", False, "No previous messages to reference")
        
        if not self.created_devices:
            return self.log_test("Chat with Message References", False, "No devices available")
        
        url = f"{self.api_url}/chat/send"
        params = {
            'user_id': self.user_id,
            'device_id': self.created_devices[0],
            'message': 'Regarding your previous response, can you provide more details?',
            'sender': 'user',
            'referenced_messages': self.chat_messages[:2]  # Reference first 2 messages
        }
        
        try:
            response = requests.post(url, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and result.get('ai_response'):
                    ai_message = result['ai_response'].get('message', '')
                    self.log_test("Chat with Message References", True, f"AI responded with context, {len(ai_message)} characters")
                    return True, result
                else:
                    self.log_test("Chat with Message References", False, "Invalid response format")
                    return False, {}
            else:
                self.log_test("Chat with Message References", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Chat with Message References", False, f"Error: {str(e)}")
            return False, {}

    def test_chat_with_files_and_references(self):
        """Test sending chat message with both file attachments and message references"""
        if not self.uploaded_files or not self.chat_messages:
            return self.log_test("Chat with Files and References", False, "Need both files and previous messages")
        
        if not self.created_devices:
            return self.log_test("Chat with Files and References", False, "No devices available")
        
        url = f"{self.api_url}/chat/send"
        params = {
            'user_id': self.user_id,
            'device_id': self.created_devices[0],
            'message': 'Based on our previous conversation and these new files, what insights can you provide?',
            'sender': 'user',
            'file_ids': self.uploaded_files[:1],  # Attach 1 file
            'referenced_messages': self.chat_messages[:1]  # Reference 1 message
        }
        
        try:
            response = requests.post(url, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and result.get('ai_response'):
                    ai_message = result['ai_response'].get('message', '')
                    self.log_test("Chat with Files and References", True, f"AI responded with full context, {len(ai_message)} characters")
                    return True, result
                else:
                    self.log_test("Chat with Files and References", False, "Invalid response format")
                    return False, {}
            else:
                self.log_test("Chat with Files and References", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Chat with Files and References", False, f"Error: {str(e)}")
            return False, {}

    def cleanup_uploaded_files(self):
        """Clean up any remaining uploaded files"""
        for file_id in self.uploaded_files:
            try:
                url = f"{self.api_url}/files/{file_id}"
                requests.delete(url)
            except:
                pass  # Ignore cleanup errors

    def test_status_endpoints(self):
        """Test original status endpoints"""
        # Test create status check
        status_data = {"client_name": "test-client"}
        success1, _ = self.run_test("Create Status Check", "POST", "status", 200, status_data)
        
        # Test get status checks
        success2, _ = self.run_test("Get Status Checks", "GET", "status", 200)
        
        return success1 and success2

    def run_all_tests(self):
        """Run all backend tests including new file upload and enhanced chat features"""
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

        # File Upload Tests (NEW)
        print("\n📁 Testing File Upload APIs...")
        self.test_file_upload_small()
        self.test_file_upload_image()
        self.test_file_upload_large()
        self.test_file_upload_oversized()
        self.test_get_file()
        self.test_get_user_files()

        # Basic chat functionality tests
        print("\n💬 Testing Basic Chat Functionality...")
        self.test_send_chat_message()
        self.test_get_chat_history()
        
        # Enhanced Chat Tests (NEW)
        print("\n🔗 Testing Enhanced Chat with Files and References...")
        self.test_enhanced_chat_with_files()
        self.test_chat_with_message_references()
        self.test_chat_with_files_and_references()
        
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

        # File cleanup test
        print("\n🗑️ Testing File Deletion...")
        self.test_delete_file()

        # WebSocket tests
        print("\n🔌 Testing WebSocket Connectivity...")
        self.test_websocket_connection()

        # Original status endpoints
        print("\n📊 Testing Status Endpoints...")
        self.test_status_endpoints()

        # Cleanup remaining files
        print("\n🧹 Cleaning up test files...")
        self.cleanup_uploaded_files()

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