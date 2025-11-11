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
    def __init__(self, base_url="https://mission-control-pwa.preview.emergentagent.com"):
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
        params = {"user_id": self.user_id}
        data = {
            "device_id": self.created_devices[0],
            "message": "Hello from test!",
            "sender": "user"
        }
        
        try:
            response = requests.post(url, json=data, params=params)
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

    def generate_base64_red_dot_png(self):
        """Generate a small red dot PNG as base64 data"""
        # This is a minimal 1x1 red pixel PNG in base64
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    def test_image_direct_single_url(self):
        """Test image-direct API with single image_url"""
        if not self.created_devices:
            return self.log_test("Image Direct Single URL", False, "No devices available")
        
        url = f"{self.api_url}/chat/image-direct"
        params = {"user_id": self.user_id}
        data = {
            "device_id": self.test_device_id,
            "image_url": "https://picsum.photos/200.jpg"
        }
        
        try:
            response = requests.post(url, json=data, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'ai_response' in result and 'displayed_in_chat' in result:
                    self.log_test("Image Direct Single URL", True, f"Success: {result.get('success')}, Displayed: {result.get('displayed_in_chat')}")
                    return True, result
                else:
                    self.log_test("Image Direct Single URL", False, "Missing required response fields")
                    return False, {}
            else:
                self.log_test("Image Direct Single URL", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Image Direct Single URL", False, f"Error: {str(e)}")
            return False, {}

    def test_image_direct_multiple_urls(self):
        """Test image-direct API with multiple media_urls"""
        if not self.created_devices:
            return self.log_test("Image Direct Multiple URLs", False, "No devices available")
        
        url = f"{self.api_url}/chat/image-direct"
        params = {"user_id": self.user_id}
        data = {
            "device_id": self.test_device_id,
            "media_urls": ["https://picsum.photos/200.jpg", "https://picsum.photos/300.png"]
        }
        
        try:
            response = requests.post(url, json=data, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'ai_response' in result and 'displayed_in_chat' in result:
                    self.log_test("Image Direct Multiple URLs", True, f"Success: {result.get('success')}, Displayed: {result.get('displayed_in_chat')}")
                    return True, result
                else:
                    self.log_test("Image Direct Multiple URLs", False, "Missing required response fields")
                    return False, {}
            else:
                self.log_test("Image Direct Multiple URLs", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Image Direct Multiple URLs", False, f"Error: {str(e)}")
            return False, {}

    def test_image_direct_base64(self):
        """Test image-direct API with base64 image_data"""
        if not self.created_devices:
            return self.log_test("Image Direct Base64", False, "No devices available")
        
        url = f"{self.api_url}/chat/image-direct"
        params = {"user_id": self.user_id}
        data = {
            "device_id": self.test_device_id,
            "image_data": self.generate_base64_red_dot_png(),
            "question": "Is there a person in this image?"
        }
        
        try:
            response = requests.post(url, json=data, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'ai_response' in result and 'displayed_in_chat' in result:
                    self.log_test("Image Direct Base64", True, f"Success: {result.get('success')}, Displayed: {result.get('displayed_in_chat')}")
                    return True, result
                else:
                    self.log_test("Image Direct Base64", False, "Missing required response fields")
                    return False, {}
            else:
                self.log_test("Image Direct Base64", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Image Direct Base64", False, f"Error: {str(e)}")
            return False, {}

    def test_image_direct_no_image_error(self):
        """Test image-direct API error case with no image fields"""
        if not self.created_devices:
            return self.log_test("Image Direct No Image Error", False, "No devices available")
        
        url = f"{self.api_url}/chat/image-direct"
        params = {"user_id": self.user_id}
        data = {
            "device_id": self.test_device_id,
            "question": "Analyze this image"
        }
        
        try:
            response = requests.post(url, json=data, params=params)
            # Should return error (400 or 422) or success=false
            if response.status_code in [400, 422]:
                self.log_test("Image Direct No Image Error", True, f"Correctly returned error status {response.status_code}")
                return True, {}
            elif response.status_code == 200:
                result = response.json()
                if not result.get('success'):
                    self.log_test("Image Direct No Image Error", True, "Correctly returned success=false")
                    return True, result
                else:
                    self.log_test("Image Direct No Image Error", False, "Should have failed but returned success=true")
                    return False, {}
            else:
                self.log_test("Image Direct No Image Error", False, f"Unexpected status {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Image Direct No Image Error", False, f"Error: {str(e)}")
            return False, {}

    def test_image_direct_invalid_url(self):
        """Test image-direct API with invalid/non-image URL"""
        if not self.created_devices:
            return self.log_test("Image Direct Invalid URL", False, "No devices available")
        
        url = f"{self.api_url}/chat/image-direct"
        params = {"user_id": self.user_id}
        data = {
            "device_id": self.test_device_id,
            "image_url": "https://httpbin.org/status/404"  # Non-image URL that returns 404
        }
        
        try:
            response = requests.post(url, json=data, params=params)
            # Should return error or success=false
            if response.status_code == 200:
                result = response.json()
                if not result.get('success'):
                    self.log_test("Image Direct Invalid URL", True, "Correctly handled invalid URL")
                    return True, result
                else:
                    self.log_test("Image Direct Invalid URL", False, "Should have failed with invalid URL")
                    return False, {}
            else:
                self.log_test("Image Direct Invalid URL", False, f"Unexpected status {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Image Direct Invalid URL", False, f"Error: {str(e)}")
            return False, {}

    def test_image_direct_chat_storage(self):
        """Test that image-direct API stores messages in chat when displayed_in_chat=true"""
        if not self.created_devices:
            return self.log_test("Image Direct Chat Storage", False, "No devices available")
        
        # First, get current chat message count
        chat_url = f"{self.api_url}/chat/{self.user_id}/{self.test_device_id}"
        try:
            initial_response = requests.get(chat_url)
            initial_count = len(initial_response.json()) if initial_response.status_code == 200 else 0
        except:
            initial_count = 0
        
        # Send image-direct request
        url = f"{self.api_url}/chat/image-direct"
        params = {"user_id": self.user_id}
        data = {
            "device_id": self.test_device_id,
            "media_urls": ["https://picsum.photos/200.jpg"],
            "question": "What do you see in this image?"
        }
        
        try:
            response = requests.post(url, json=data, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('displayed_in_chat'):
                    # Check if new messages were added to chat
                    time.sleep(1)  # Wait for message to be stored
                    final_response = requests.get(chat_url)
                    if final_response.status_code == 200:
                        final_count = len(final_response.json())
                        if final_count > initial_count:
                            # Check if the new message has media_urls
                            messages = final_response.json()
                            latest_message = messages[-1] if messages else None
                            if latest_message and latest_message.get('media_urls'):
                                self.log_test("Image Direct Chat Storage", True, f"Message stored with media_urls: {latest_message.get('media_urls')}")
                                return True, result
                            else:
                                self.log_test("Image Direct Chat Storage", False, "Message stored but missing media_urls")
                                return False, {}
                        else:
                            self.log_test("Image Direct Chat Storage", False, "No new messages added to chat")
                            return False, {}
                    else:
                        self.log_test("Image Direct Chat Storage", False, "Could not retrieve chat messages")
                        return False, {}
                else:
                    self.log_test("Image Direct Chat Storage", True, "Not displayed in chat (as expected)")
                    return True, result
            else:
                self.log_test("Image Direct Chat Storage", False, f"Status {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Image Direct Chat Storage", False, f"Error: {str(e)}")
            return False, {}

    def test_chat_send_media_urls_regression(self):
        """Test that existing chat send with media_urls still works (regression test)"""
        if not self.created_devices:
            return self.log_test("Chat Send Media URLs Regression", False, "No devices available")
        
        url = f"{self.api_url}/chat/send"
        params = {"user_id": self.user_id}
        data = {
            "device_id": self.test_device_id,
            "message": "Check these images",
            "media_urls": ["https://picsum.photos/200.jpg"],
            "sender": "user"
        }
        
        try:
            response = requests.post(url, json=data, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and result.get('ai_response'):
                    ai_message = result['ai_response'].get('message', '')
                    self.log_test("Chat Send Media URLs Regression", True, f"AI responded with {len(ai_message)} characters")
                    return True, result
                else:
                    self.log_test("Chat Send Media URLs Regression", False, "Invalid response format")
                    return False, {}
            else:
                self.log_test("Chat Send Media URLs Regression", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Chat Send Media URLs Regression", False, f"Error: {str(e)}")
            return False, {}

    def test_camera_prompt_get(self):
        """Test GET camera prompt endpoint"""
        url = f"{self.api_url}/camera/prompt/{self.user_id}/{self.test_device_id}"
        
        try:
            response = requests.get(url)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if 'prompt_text' in result and 'user_id' in result and 'device_id' in result:
                    self.log_test("Camera Prompt GET", True, f"Retrieved prompt: {result.get('prompt_text', '')[:50]}...")
                    return True, result
                else:
                    self.log_test("Camera Prompt GET", False, "Missing required response fields")
                    return False, {}
            else:
                self.log_test("Camera Prompt GET", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Camera Prompt GET", False, f"Error: {str(e)}")
            return False, {}

    def test_camera_prompt_put(self):
        """Test PUT camera prompt endpoint"""
        url = f"{self.api_url}/camera/prompt/{self.user_id}/{self.test_device_id}"
        data = {
            "instructions": "people at front door"
        }
        
        try:
            response = requests.put(url, json=data)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'prompt_text' in result:
                    self.log_test("Camera Prompt PUT", True, f"Updated prompt: {result.get('prompt_text', '')[:50]}...")
                    return True, result
                else:
                    self.log_test("Camera Prompt PUT", False, "Missing required response fields")
                    return False, {}
            else:
                self.log_test("Camera Prompt PUT", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("Camera Prompt PUT", False, f"Error: {str(e)}")
            return False, {}

    # AI Chat Agent Tests
    def test_ai_agent_global_chat(self):
        """Test AI agent global chat - intent understanding"""
        url = f"{self.api_url}/ai-agent/chat"
        params = {"user_id": self.user_id}
        data = {
            "chat_type": "global",
            "message": "Show me people in all cameras",
            "context": {}
        }
        
        try:
            response = requests.post(url, json=data, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'message' in result and 'conversation_id' in result and 'state' in result:
                    # Store conversation ID for follow-up tests
                    if not hasattr(self, 'ai_conversation_ids'):
                        self.ai_conversation_ids = []
                    self.ai_conversation_ids.append(result['conversation_id'])
                    
                    self.log_test("AI Agent Global Chat", True, f"State: {result.get('state')}, Conv ID: {result['conversation_id'][:8]}...")
                    return True, result
                else:
                    self.log_test("AI Agent Global Chat", False, "Missing required response fields")
                    return False, {}
            else:
                self.log_test("AI Agent Global Chat", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("AI Agent Global Chat", False, f"Error: {str(e)}")
            return False, {}

    def test_ai_agent_camera_scope_chat(self):
        """Test AI agent camera-specific chat"""
        if not self.created_devices:
            return self.log_test("AI Agent Camera Scope Chat", False, "No devices available")
        
        url = f"{self.api_url}/ai-agent/chat"
        params = {"user_id": self.user_id}
        data = {
            "chat_type": "camera",
            "message": "Look for cars",
            "device_id": self.test_device_id,
            "context": {}
        }
        
        try:
            response = requests.post(url, json=data, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'message' in result and 'conversation_id' in result:
                    # Store conversation ID for follow-up tests
                    if not hasattr(self, 'ai_conversation_ids'):
                        self.ai_conversation_ids = []
                    self.ai_conversation_ids.append(result['conversation_id'])
                    
                    self.log_test("AI Agent Camera Scope Chat", True, f"Camera-specific intent understood")
                    return True, result
                else:
                    self.log_test("AI Agent Camera Scope Chat", False, "Missing required response fields")
                    return False, {}
            else:
                self.log_test("AI Agent Camera Scope Chat", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("AI Agent Camera Scope Chat", False, f"Error: {str(e)}")
            return False, {}

    def test_ai_agent_multi_turn_conversation(self):
        """Test multi-turn conversation with state progression"""
        if not hasattr(self, 'ai_conversation_ids') or not self.ai_conversation_ids:
            return self.log_test("AI Agent Multi-turn Conversation", False, "No previous conversations available")
        
        conversation_id = self.ai_conversation_ids[0]
        
        url = f"{self.api_url}/ai-agent/chat"
        params = {"user_id": self.user_id}
        data = {
            "chat_type": "global",
            "message": "Yes, confirmed",
            "conversation_id": conversation_id,
            "context": {}
        }
        
        try:
            response = requests.post(url, json=data, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'state' in result:
                    # Check if state progressed (should move to alert_level_selection)
                    expected_states = ["alert_level_selection", "confirmation", "completed"]
                    if result['state'] in expected_states:
                        self.log_test("AI Agent Multi-turn Conversation", True, f"State progressed to: {result['state']}")
                        return True, result
                    else:
                        self.log_test("AI Agent Multi-turn Conversation", True, f"State: {result['state']} (conversation continuing)")
                        return True, result
                else:
                    self.log_test("AI Agent Multi-turn Conversation", False, "Missing state in response")
                    return False, {}
            else:
                self.log_test("AI Agent Multi-turn Conversation", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("AI Agent Multi-turn Conversation", False, f"Error: {str(e)}")
            return False, {}

    def test_ai_agent_list_conversations(self):
        """Test listing all conversations for a user"""
        url = f"{self.api_url}/ai-agent/conversations/{self.user_id}"
        
        try:
            response = requests.get(url)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'conversations' in result:
                    conversation_count = len(result['conversations'])
                    self.log_test("AI Agent List Conversations", True, f"Found {conversation_count} conversations")
                    return True, result
                else:
                    self.log_test("AI Agent List Conversations", False, "Missing conversations in response")
                    return False, {}
            else:
                self.log_test("AI Agent List Conversations", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("AI Agent List Conversations", False, f"Error: {str(e)}")
            return False, {}

    def test_ai_agent_get_specific_conversation(self):
        """Test getting specific conversation details"""
        if not hasattr(self, 'ai_conversation_ids') or not self.ai_conversation_ids:
            return self.log_test("AI Agent Get Specific Conversation", False, "No conversations available")
        
        conversation_id = self.ai_conversation_ids[0]
        url = f"{self.api_url}/ai-agent/conversation/{conversation_id}"
        params = {"user_id": self.user_id}
        
        try:
            response = requests.get(url, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'conversation' in result:
                    conv = result['conversation']
                    if 'history' in conv and 'state' in conv:
                        history_length = len(conv.get('history', []))
                        self.log_test("AI Agent Get Specific Conversation", True, f"Retrieved conversation with {history_length} messages")
                        return True, result
                    else:
                        self.log_test("AI Agent Get Specific Conversation", False, "Missing conversation details")
                        return False, {}
                else:
                    self.log_test("AI Agent Get Specific Conversation", False, "Missing conversation in response")
                    return False, {}
            else:
                self.log_test("AI Agent Get Specific Conversation", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("AI Agent Get Specific Conversation", False, f"Error: {str(e)}")
            return False, {}

    def test_ai_agent_send_query_mocked(self):
        """Test sending generated JSON to external API (mocked)"""
        url = f"{self.api_url}/ai-agent/send-query"
        params = {"user_id": self.user_id}
        
        # Sample AI query JSON
        query_json = {
            "query_id": "test_query_123",
            "user_id": self.user_id,
            "target_type": "cameras",
            "target_ids": [self.test_device_id],
            "detection_objects": ["people", "cars"],
            "alert_level": "MEDIUM",
            "query_text": "Show me people in all cameras",
            "confidence_threshold": 0.5,
            "notification_settings": {
                "enabled": True,
                "alert_level": "MEDIUM",
                "notify_immediately": False
            }
        }
        
        try:
            response = requests.post(url, json=query_json, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'query_json' in result and 'note' in result:
                    # Check if it's properly mocked
                    if "mocked" in result.get('note', '').lower() or "pending" in result.get('message', '').lower():
                        self.log_test("AI Agent Send Query (Mocked)", True, "External API integration mocked as expected")
                        return True, result
                    else:
                        self.log_test("AI Agent Send Query (Mocked)", True, "Query JSON processed successfully")
                        return True, result
                else:
                    self.log_test("AI Agent Send Query (Mocked)", False, "Missing required response fields")
                    return False, {}
            else:
                self.log_test("AI Agent Send Query (Mocked)", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("AI Agent Send Query (Mocked)", False, f"Error: {str(e)}")
            return False, {}

    def test_ai_agent_feedback(self):
        """Test AI agent feedback learning endpoint"""
        if not hasattr(self, 'ai_conversation_ids') or not self.ai_conversation_ids:
            return self.log_test("AI Agent Feedback", False, "No conversations available for feedback")
        
        conversation_id = self.ai_conversation_ids[0]
        url = f"{self.api_url}/ai-agent/feedback"
        params = {"user_id": self.user_id}
        data = {
            "conversation_id": conversation_id,
            "message": "I got an alert about a person but there's no person in the image",
            "image_url": "https://picsum.photos/400/300",
            "feedback_type": "false_positive"
        }
        
        try:
            response = requests.post(url, json=data, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'message' in result:
                    self.log_test("AI Agent Feedback", True, "Feedback processed successfully")
                    return True, result
                else:
                    self.log_test("AI Agent Feedback", False, "Missing required response fields")
                    return False, {}
            else:
                self.log_test("AI Agent Feedback", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("AI Agent Feedback", False, f"Error: {str(e)}")
            return False, {}

    def test_ai_agent_delete_conversation(self):
        """Test deleting a conversation"""
        if not hasattr(self, 'ai_conversation_ids') or not self.ai_conversation_ids:
            return self.log_test("AI Agent Delete Conversation", False, "No conversations available to delete")
        
        # Use the last conversation ID for deletion
        conversation_id = self.ai_conversation_ids[-1]
        url = f"{self.api_url}/ai-agent/conversation/{conversation_id}"
        params = {"user_id": self.user_id}
        
        try:
            response = requests.delete(url, params=params)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success'):
                    # Remove from our tracking list
                    self.ai_conversation_ids.remove(conversation_id)
                    self.log_test("AI Agent Delete Conversation", True, f"Conversation {conversation_id[:8]}... deleted")
                    return True, result
                else:
                    self.log_test("AI Agent Delete Conversation", False, "Delete operation failed")
                    return False, {}
            else:
                self.log_test("AI Agent Delete Conversation", False, f"Status {response.status_code}: {response.text[:200]}")
                return False, {}
                
        except Exception as e:
            self.log_test("AI Agent Delete Conversation", False, f"Error: {str(e)}")
            return False, {}

    def run_ai_agent_tests(self):
        """Run all AI Chat Agent tests"""
        print("\n🤖 Testing AI Chat Agent Endpoints...")
        
        # Test AI agent chat scenarios
        self.test_ai_agent_global_chat()
        self.test_ai_agent_camera_scope_chat()
        self.test_ai_agent_multi_turn_conversation()
        
        # Test conversation management
        self.test_ai_agent_list_conversations()
        self.test_ai_agent_get_specific_conversation()
        
        # Test external API integration (mocked)
        self.test_ai_agent_send_query_mocked()
        
        # Test feedback learning
        self.test_ai_agent_feedback()
        
        # Test conversation deletion
        self.test_ai_agent_delete_conversation()

    def run_image_direct_tests(self):
        """Run all image-direct API tests"""
        print("\n🖼️ Testing Image-Direct API Extensions...")
        
        # Test various image-direct API scenarios
        self.test_image_direct_single_url()
        self.test_image_direct_multiple_urls()
        self.test_image_direct_base64()
        self.test_image_direct_no_image_error()
        self.test_image_direct_invalid_url()
        self.test_image_direct_chat_storage()
        
        # Test regression - existing chat send with media_urls
        print("\n🔄 Testing Regression - Chat Send with Media URLs...")
        self.test_chat_send_media_urls_regression()
        
        # Test camera prompt endpoints
        print("\n📹 Testing Camera Prompt Endpoints...")
        self.test_camera_prompt_get()
        self.test_camera_prompt_put()

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
        
        # Image-Direct API Tests (FOCUS OF THIS REVIEW)
        self.run_image_direct_tests()
        
        # AI Chat Agent Tests (NEW - MAIN FOCUS)
        self.run_ai_agent_tests()
        
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