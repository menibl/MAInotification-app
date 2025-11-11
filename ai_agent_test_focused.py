#!/usr/bin/env python3
"""
Focused AI Chat Agent Testing
Tests the new AI Chat Agent endpoints specifically
"""
import requests
import json
import sys

class AIAgentTester:
    def __init__(self, base_url="https://mission-control-pwa.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.user_id = "demo-user-123"
        self.test_device_id = "123456"
        self.tests_run = 0
        self.tests_passed = 0
        self.ai_conversation_ids = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name} - {details}")
        return success

    def test_ai_agent_global_chat(self):
        """Test Scenario 1: Global Chat - Intent Understanding"""
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
                    self.ai_conversation_ids.append(result['conversation_id'])
                    details = f"State: {result.get('state')}, AI Response: {result['message'][:100]}..."
                    return self.log_test("Scenario 1: Global Chat Intent Understanding", True, details)
                else:
                    return self.log_test("Scenario 1: Global Chat Intent Understanding", False, "Missing required response fields")
            else:
                return self.log_test("Scenario 1: Global Chat Intent Understanding", False, f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            return self.log_test("Scenario 1: Global Chat Intent Understanding", False, f"Error: {str(e)}")

    def test_ai_agent_camera_scope_chat(self):
        """Test Scenario 2: Camera Scope Chat"""
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
                    self.ai_conversation_ids.append(result['conversation_id'])
                    details = f"Camera-specific intent processed, Conv ID: {result['conversation_id'][:20]}..."
                    return self.log_test("Scenario 2: Camera Scope Chat", True, details)
                else:
                    return self.log_test("Scenario 2: Camera Scope Chat", False, "Missing required response fields")
            else:
                return self.log_test("Scenario 2: Camera Scope Chat", False, f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            return self.log_test("Scenario 2: Camera Scope Chat", False, f"Error: {str(e)}")

    def test_ai_agent_multi_turn_conversation(self):
        """Test Scenario 3: Multi-turn Conversation"""
        if not self.ai_conversation_ids:
            return self.log_test("Scenario 3: Multi-turn Conversation", False, "No previous conversations available")
        
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
                    details = f"State progressed to: {result['state']}"
                    return self.log_test("Scenario 3: Multi-turn Conversation", True, details)
                else:
                    return self.log_test("Scenario 3: Multi-turn Conversation", False, "Missing state in response")
            else:
                return self.log_test("Scenario 3: Multi-turn Conversation", False, f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            return self.log_test("Scenario 3: Multi-turn Conversation", False, f"Error: {str(e)}")

    def test_ai_agent_list_conversations(self):
        """Test Scenario 4: List Conversations"""
        url = f"{self.api_url}/ai-agent/conversations/{self.user_id}"
        
        try:
            response = requests.get(url)
            success = response.status_code == 200
            
            if success:
                result = response.json()
                if result.get('success') and 'conversations' in result:
                    conversation_count = len(result['conversations'])
                    details = f"Found {conversation_count} conversations for user {self.user_id}"
                    return self.log_test("Scenario 4: List Conversations", True, details)
                else:
                    return self.log_test("Scenario 4: List Conversations", False, "Missing conversations in response")
            else:
                return self.log_test("Scenario 4: List Conversations", False, f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            return self.log_test("Scenario 4: List Conversations", False, f"Error: {str(e)}")

    def test_ai_agent_get_specific_conversation(self):
        """Test Scenario 5: Get Specific Conversation"""
        if not self.ai_conversation_ids:
            return self.log_test("Scenario 5: Get Specific Conversation", False, "No conversations available")
        
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
                        details = f"Retrieved conversation with {history_length} messages, state: {conv.get('state')}"
                        return self.log_test("Scenario 5: Get Specific Conversation", True, details)
                    else:
                        return self.log_test("Scenario 5: Get Specific Conversation", False, "Missing conversation details")
                else:
                    return self.log_test("Scenario 5: Get Specific Conversation", False, "Missing conversation in response")
            else:
                return self.log_test("Scenario 5: Get Specific Conversation", False, f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            return self.log_test("Scenario 5: Get Specific Conversation", False, f"Error: {str(e)}")

    def test_ai_agent_send_query_mocked(self):
        """Test sending generated JSON to external API (mocked)"""
        url = f"{self.api_url}/ai-agent/send-query"
        params = {"user_id": self.user_id}
        
        # Sample AI query JSON as specified in review request
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
                if result.get('success') and 'query_json' in result:
                    # Check if it's properly mocked
                    is_mocked = "mocked" in result.get('note', '').lower() or "pending" in result.get('message', '').lower()
                    details = f"External API integration {'mocked' if is_mocked else 'processed'} successfully"
                    return self.log_test("Send Query to External API (Mocked)", True, details)
                else:
                    return self.log_test("Send Query to External API (Mocked)", False, "Missing required response fields")
            else:
                return self.log_test("Send Query to External API (Mocked)", False, f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            return self.log_test("Send Query to External API (Mocked)", False, f"Error: {str(e)}")

    def test_ai_agent_feedback(self):
        """Test AI agent feedback learning endpoint"""
        if not self.ai_conversation_ids:
            return self.log_test("AI Agent Feedback Learning", False, "No conversations available for feedback")
        
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
                    details = f"Feedback processed: {result['message'][:100]}..."
                    return self.log_test("AI Agent Feedback Learning", True, details)
                else:
                    return self.log_test("AI Agent Feedback Learning", False, "Missing required response fields")
            else:
                return self.log_test("AI Agent Feedback Learning", False, f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            return self.log_test("AI Agent Feedback Learning", False, f"Error: {str(e)}")

    def test_ai_agent_delete_conversation(self):
        """Test deleting a conversation"""
        if not self.ai_conversation_ids:
            return self.log_test("Delete AI Conversation", False, "No conversations available to delete")
        
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
                    details = f"Conversation {conversation_id[:20]}... deleted successfully"
                    return self.log_test("Delete AI Conversation", True, details)
                else:
                    return self.log_test("Delete AI Conversation", False, "Delete operation failed")
            else:
                return self.log_test("Delete AI Conversation", False, f"Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            return self.log_test("Delete AI Conversation", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all AI Chat Agent tests"""
        print("🤖 AI Chat Agent Endpoint Testing")
        print(f"Backend URL: {self.base_url}")
        print(f"Test User ID: {self.user_id}")
        print(f"Test Device ID: {self.test_device_id}")
        print("=" * 60)

        # Test all scenarios from the review request
        self.test_ai_agent_global_chat()
        self.test_ai_agent_camera_scope_chat()
        self.test_ai_agent_multi_turn_conversation()
        self.test_ai_agent_list_conversations()
        self.test_ai_agent_get_specific_conversation()
        self.test_ai_agent_send_query_mocked()
        self.test_ai_agent_feedback()
        self.test_ai_agent_delete_conversation()

        # Print results
        print("\n" + "=" * 60)
        print(f"📊 AI Agent Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All AI Chat Agent tests passed!")
            return True
        else:
            failed = self.tests_run - self.tests_passed
            print(f"⚠️  {failed} AI agent test(s) failed")
            return False

def main():
    tester = AIAgentTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ AI Chat Agent backend is fully functional!")
        print("✅ All endpoints working correctly:")
        print("   - POST /api/ai-agent/chat (Global & Camera scope)")
        print("   - POST /api/ai-agent/feedback")
        print("   - GET /api/ai-agent/conversation/{conversation_id}")
        print("   - GET /api/ai-agent/conversations/{user_id}")
        print("   - POST /api/ai-agent/send-query (mocked)")
        print("   - DELETE /api/ai-agent/conversation/{conversation_id}")
    else:
        print("\n❌ Some AI Chat Agent tests failed.")
        print("Please check the backend implementation.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())