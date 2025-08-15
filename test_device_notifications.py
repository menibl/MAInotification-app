#!/usr/bin/env python3
"""
Test script for device-specific notifications
"""
import requests
import time

API = "http://localhost:8001/api"
USER_ID = "demo-user-123"

def get_devices():
    """Get all devices for the user"""
    response = requests.get(f"{API}/devices/{USER_ID}")
    return response.json() if response.status_code == 200 else []

def send_device_notification(device_id, device_name, message):
    """Send notification to specific device"""
    response = requests.post(f"{API}/push/send", json={
        "user_id": USER_ID,
        "device_id": device_id,
        "title": f"{device_name} Alert",
        "body": message
    })
    return response.json()

def main():
    print("🔔 Testing Device-Specific Notifications")
    print("=" * 50)
    
    # Get devices
    devices = get_devices()
    if not devices:
        print("❌ No devices found!")
        return
    
    print(f"📱 Found {len(devices)} devices:")
    for device in devices:
        print(f"  - {device['name']} (ID: {device['id'][:8]}...)")
    
    print("\n🚀 Sending test notifications...")
    
    # Send notifications to different devices
    test_notifications = [
        (devices[0]['id'], devices[0]['name'], "Motion detected at front entrance"),
        (devices[1]['id'] if len(devices) > 1 else devices[0]['id'], 
         devices[1]['name'] if len(devices) > 1 else devices[0]['name'], 
         "Temperature reading: 72°F"),
        (devices[2]['id'] if len(devices) > 2 else devices[0]['id'],
         devices[2]['name'] if len(devices) > 2 else devices[0]['name'],
         "Door sensor activated")
    ]
    
    for device_id, device_name, message in test_notifications:
        result = send_device_notification(device_id, device_name, message)
        if result.get('success'):
            print(f"✅ Sent to {device_name}: {message}")
        else:
            print(f"❌ Failed to send to {device_name}")
        time.sleep(1)
    
    print("\n📋 Test Complete!")
    print("\nNow you can:")
    print("1. 📱 Check main notifications view - see ALL notifications")
    print("2. 💬 Enter specific device chat - see ONLY that device's notifications")
    print("3. 🔔 Notifications appear mixed with chat messages in device view")
    
    # Show API endpoints
    print(f"\n🔗 API Endpoints:")
    print(f"📝 All notifications: GET {API}/notifications/{USER_ID}")
    print(f"📱 Device notifications: GET {API}/notifications/{USER_ID}/device/{{device_id}}")

if __name__ == "__main__":
    main()