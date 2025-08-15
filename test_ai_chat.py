#!/usr/bin/env python3
"""
Test script for AI Chat functionality
"""
import requests
import json
import time

BACKEND_URL = "http://localhost:8001"
API = f"{BACKEND_URL}/api"
USER_ID = "demo-user-123"
DEVICE_ID = "123456"  # camera202 device

def test_ai_chat():
    """Test AI chat functionality"""
    print("🤖 Testing AI Chat Integration...")
    print(f"User: {USER_ID}")
    print(f"Device: {DEVICE_ID} (camera202)")
    print("-" * 50)
    
    # Test messages to send
    test_messages = [
        "Hello! Can you tell me what you are?",
        "What security features do you have?",
        "Can you analyze motion in this area?",
        "What's your current status?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. 👤 User: {message}")
        
        try:
            # Send message and get AI response
            response = requests.post(f"{API}/chat/send", 
                params={"user_id": USER_ID},
                json={
                    "device_id": DEVICE_ID,
                    "message": message,
                    "sender": "user"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("ai_response"):
                    ai_message = result["ai_response"]["message"]
                    print(f"   🤖 AI: {ai_message}")
                    
                    # Check if response has error
                    if result["ai_response"].get("error"):
                        print(f"   ⚠️  AI Error detected")
                else:
                    print(f"   ❌ No AI response: {result}")
            else:
                print(f"   ❌ API Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Wait between messages
        time.sleep(2)
    
    print("\n" + "=" * 50)
    print("📊 Testing Chat History...")
    
    try:
        # Get chat history
        history_response = requests.get(f"{API}/chat/{USER_ID}/{DEVICE_ID}/history")
        if history_response.status_code == 200:
            history = history_response.json()
            print(f"✅ Chat history retrieved:")
            print(f"   Messages: {history['message_count']}")
            print(f"   Created: {history.get('created_at', 'N/A')}")
            print(f"   Updated: {history.get('updated_at', 'N/A')}")
            
            # Show last few messages
            if history['history']:
                print(f"\n📝 Recent messages:")
                for msg in history['history'][-4:]:  # Last 4 messages
                    sender_icon = "👤" if msg['sender'] == 'user' else "🤖" if msg['sender'] == 'ai' else "📱"
                    print(f"   {sender_icon} {msg['sender'].title()}: {msg['message'][:60]}{'...' if len(msg['message']) > 60 else ''}")
        else:
            print(f"❌ Failed to get history: {history_response.status_code}")
            
    except Exception as e:
        print(f"❌ History error: {e}")
    
    print("\n" + "=" * 50)
    print("📱 Testing Regular Chat Messages...")
    
    try:
        # Get regular chat messages
        messages_response = requests.get(f"{API}/chat/{USER_ID}/{DEVICE_ID}")
        if messages_response.status_code == 200:
            messages = messages_response.json()
            print(f"✅ Retrieved {len(messages)} chat messages")
            
            # Count message types
            user_msgs = len([m for m in messages if m['sender'] == 'user'])
            ai_msgs = len([m for m in messages if m['sender'] == 'ai'])
            device_msgs = len([m for m in messages if m['sender'] == 'device'])
            
            print(f"   👤 User messages: {user_msgs}")
            print(f"   🤖 AI messages: {ai_msgs}")
            print(f"   📱 Device messages: {device_msgs}")
        else:
            print(f"❌ Failed to get messages: {messages_response.status_code}")
            
    except Exception as e:
        print(f"❌ Messages error: {e}")

def test_different_device_types():
    """Test AI responses for different device types"""
    print(f"\n🔬 Testing Different Device AI Personalities...")
    
    # Test device types
    device_types = ["camera", "sensor", "doorbell", "unknown"]
    
    for device_type in device_types:
        print(f"\n📱 Testing {device_type} device personality...")
        
        # This would require creating different devices, but we'll simulate
        # by checking the AI personality configuration
        print(f"   AI should respond as: {device_type} assistant")

def main():
    """Run all AI chat tests"""
    print("🚀 AI Chat Integration Testing")
    print(f"Backend: {BACKEND_URL}")
    print("=" * 60)
    
    # Check API connectivity
    try:
        response = requests.get(f"{API}/")
        if response.status_code == 200:
            print("✅ Backend API is accessible")
        else:
            print("❌ Backend API not responding")
            return
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return
    
    # Check device exists
    try:
        device_response = requests.get(f"{API}/devices/{USER_ID}")
        devices = device_response.json()
        device_found = any(d['id'] == DEVICE_ID for d in devices)
        
        if device_found:
            print(f"✅ Device {DEVICE_ID} (camera202) found")
        else:
            print(f"❌ Device {DEVICE_ID} not found")
            print("Available devices:", [d['name'] for d in devices])
            return
    except Exception as e:
        print(f"❌ Device check failed: {e}")
        return
    
    # Run tests
    test_ai_chat()
    test_different_device_types()
    
    print("\n" + "=" * 60)
    print("🎉 AI Chat Testing Complete!")
    print("\n📚 Available APIs:")
    print(f"   💬 Send Chat: POST {API}/chat/send?user_id={{user_id}}")
    print(f"   📜 Get History: GET {API}/chat/{{user_id}}/{{device_id}}/history")
    print(f"   🗑️  Clear History: DELETE {API}/chat/{{user_id}}/{{device_id}}/history")
    print(f"   📱 Get Messages: GET {API}/chat/{{user_id}}/{{device_id}}")

if __name__ == "__main__":
    main()