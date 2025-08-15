#!/usr/bin/env python3
"""
Demo setup script to create sample devices and data for testing
"""
import asyncio
import requests
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8001"
API = f"{BACKEND_URL}/api"
USER_ID = "demo-user-123"

# Sample devices
DEMO_DEVICES = [
    {
        "name": "Security Camera 01",
        "type": "camera",
        "user_id": USER_ID
    },
    {
        "name": "Door Sensor",
        "type": "sensor", 
        "user_id": USER_ID
    },
    {
        "name": "Temperature Monitor",
        "type": "sensor",
        "user_id": USER_ID
    },
    {
        "name": "Smart Doorbell",
        "type": "camera",
        "user_id": USER_ID
    }
]

def setup_demo_devices():
    """Create demo devices"""
    print("Creating demo devices...")
    device_ids = []
    
    for device_data in DEMO_DEVICES:
        try:
            response = requests.post(f"{API}/devices", json=device_data)
            if response.status_code == 200:
                device = response.json()
                device_ids.append(device['id'])
                print(f"✓ Created device: {device['name']} (ID: {device['id']})")
            else:
                print(f"✗ Failed to create device: {device_data['name']}")
        except Exception as e:
            print(f"✗ Error creating device {device_data['name']}: {e}")
    
    return device_ids

def send_demo_notifications(device_ids):
    """Send some demo notifications"""
    print("\nSending demo notifications...")
    
    demo_notifications = [
        {
            "user_id": USER_ID,
            "device_id": device_ids[0] if device_ids else "camera-01",
            "message": "Motion detected at front door",
            "media_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop",
            "notification_type": "alert"
        },
        {
            "user_id": USER_ID,
            "device_id": device_ids[1] if len(device_ids) > 1 else "sensor-01", 
            "message": "Door opened",
            "notification_type": "message"
        },
        {
            "user_id": USER_ID,
            "device_id": device_ids[2] if len(device_ids) > 2 else "temp-01",
            "message": "Temperature is 75°F",
            "notification_type": "message"
        },
        {
            "user_id": USER_ID,
            "device_id": device_ids[0] if device_ids else "camera-01",
            "message": "Package delivered",
            "media_url": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400&h=300&fit=crop",
            "notification_type": "alert"
        }
    ]
    
    for notif in demo_notifications:
        try:
            response = requests.post(f"{API}/simulate/device-notification", params=notif)
            if response.status_code == 200:
                print(f"✓ Sent notification: {notif['message']}")
            else:
                print(f"✗ Failed to send notification: {notif['message']}")
        except Exception as e:
            print(f"✗ Error sending notification: {e}")

def main():
    print("Setting up Device Chat demo...")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"User ID: {USER_ID}")
    print("-" * 50)
    
    # Test API connection
    try:
        response = requests.get(f"{API}/")
        if response.status_code == 200:
            print("✓ Backend API is accessible")
        else:
            print("✗ Backend API is not responding correctly")
            return
    except Exception as e:
        print(f"✗ Cannot connect to backend API: {e}")
        return
    
    # Setup demo data
    device_ids = setup_demo_devices()
    
    if device_ids:
        send_demo_notifications(device_ids)
    
    print("\n" + "="*50)
    print("Demo setup complete!")
    print("\nYou can now:")
    print("1. Open the frontend app")
    print("2. View your devices in the device list")
    print("3. Click on devices to start chatting")
    print("4. Check notifications by clicking the bell icon")
    print("\nTo test real-time notifications, use the simulate endpoint:")
    print(f"POST {API}/simulate/device-notification")

if __name__ == "__main__":
    main()