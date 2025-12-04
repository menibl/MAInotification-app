#!/usr/bin/env python3
"""
Create sample data for MAI database
Matches the exact structure from the user's MongoDB collections
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def create_sample_data():
    """Create sample data matching MAI database structure"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client['MAI']
    
    print("🚀 Starting MAI database sample data creation...")
    
    # Clear existing data
    print("\n🗑️  Clearing existing collections...")
    await db.users.delete_many({})
    await db.cameras.delete_many({})
    await db.missions.delete_many({})
    await db.missionmessagelogs.delete_many({})
    
    # 1. Create Users
    print("\n👤 Creating users...")
    user1_id = ObjectId()
    user2_id = ObjectId()
    
    users = [
        {
            "_id": user1_id,
            "lastLogin": {
                "os": {"version": "10", "name": "Windows"},
                "browser": {"version": "120.0", "name": "Chrome"},
                "ipAddress": "192.168.1.100",
                "isMobile": False,
                "ua": "Mozilla/5.0..."
            },
            "security": {"failedAttempts": 0},
            "signinType": "manual",
            "role": ObjectId(),
            "isNewUser": False,
            "isEmailVerified": True,
            "isSignUpUser": True,
            "isDeleted": False,
            "isActive": True,
            "firstName": "Daniel",
            "lastName": "Cohen",
            "password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7qvLh/5pGO",  # password: test123
            "email": "daniel@example.com",
            "phone": "972501234567",
            "timezone": {
                "value": "Asia/Jerusalem",
                "label": "(GMT+3:00) Israel",
                "offset": 3,
                "abbrev": "IDT",
                "altName": "Israel Daylight Time"
            },
            "systemMessagePhone": ["972501234567"],
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        },
        {
            "_id": user2_id,
            "lastLogin": {
                "os": {"version": "", "name": ""},
                "browser": {"version": "", "name": ""},
                "ipAddress": "0.0.0.0",
                "isMobile": False,
                "ua": ""
            },
            "security": {"failedAttempts": 0},
            "signinType": "manual",
            "role": ObjectId(),
            "isNewUser": False,
            "isEmailVerified": True,
            "isSignUpUser": True,
            "isDeleted": False,
            "isActive": True,
            "firstName": "Lior",
            "lastName": "Levy",
            "password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7qvLh/5pGO",  # password: test123
            "email": "lior@example.com",
            "phone": "972547332390",
            "timezone": {
                "value": "Asia/Jerusalem",
                "label": "(GMT+3:00) Israel",
                "offset": 3,
                "abbrev": "IDT",
                "altName": "Israel Daylight Time"
            },
            "systemMessagePhone": ["9876543210", "8765432109"],
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        }
    ]
    
    await db.users.insert_many(users)
    print(f"   ✅ Created {len(users)} users")
    
    # 2. Create Cameras
    print("\n📹 Creating cameras...")
    camera1_id = ObjectId()
    camera2_id = ObjectId()
    camera3_id = ObjectId()
    
    cameras = [
        {
            "_id": camera1_id,
            "streamStatus": "",
            "isDeleted": False,
            "isActive": True,
            "name": "Front Door Camera",
            "rtmpCode": "ABC123",
            "streamUrl": "rtmp://localhost:1935/live_hls/ABC123",
            "type": "rtmp",
            "createdBy": user1_id,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        },
        {
            "_id": camera2_id,
            "streamStatus": "",
            "isDeleted": False,
            "isActive": True,
            "name": "Backyard Camera",
            "rtmpCode": "XYZ789",
            "streamUrl": "rtmp://localhost:1935/live_hls/XYZ789",
            "type": "rtmp",
            "createdBy": user1_id,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        },
        {
            "_id": camera3_id,
            "streamStatus": "",
            "isDeleted": False,
            "isActive": True,
            "name": "Parking Lot Camera",
            "rtmpCode": "DEF456",
            "streamUrl": "rtmp://localhost:1935/live_hls/DEF456",
            "type": "rtmp",
            "createdBy": user2_id,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        }
    ]
    
    await db.cameras.insert_many(cameras)
    print(f"   ✅ Created {len(cameras)} cameras")
    
    # 3. Create Missions
    print("\n🎯 Creating missions...")
    mission1_id = ObjectId()
    mission2_id = ObjectId()
    
    missions = [
        {
            "_id": mission1_id,
            "objectIds": [ObjectId(), ObjectId()],
            "cameraIds": [camera1_id, camera2_id],
            "question": [],
            "scheduleIds": [ObjectId()],
            "outputOption": [
                {
                    "type": "email",
                    "value": ["daniel@example.com"],
                    "useExistingEmail": True
                }
            ],
            "status": "running",
            "isCompleted": False,
            "isDeleted": False,
            "isActive": True,
            "name": "Home Security",
            "model": {
                "modelId": ObjectId(),
                "modelName": "detect"
            },
            "createdBy": user1_id,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        },
        {
            "_id": mission2_id,
            "objectIds": [ObjectId()],
            "cameraIds": [camera3_id],
            "question": [],
            "scheduleIds": [ObjectId()],
            "outputOption": [
                {
                    "type": "email",
                    "value": ["lior@example.com"],
                    "useExistingEmail": True
                }
            ],
            "status": "running",
            "isCompleted": False,
            "isDeleted": False,
            "isActive": True,
            "name": "Parking Monitoring",
            "model": {
                "modelId": ObjectId(),
                "modelName": "vehicle_detect"
            },
            "createdBy": user2_id,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        }
    ]
    
    await db.missions.insert_many(missions)
    print(f"   ✅ Created {len(missions)} missions")
    
    # 4. Create Mission Message Logs
    print("\n💬 Creating message logs...")
    logs = [
        {
            "_id": ObjectId(),
            "missionId": mission1_id,
            "cameraId": camera1_id,
            "message": "MAI Alert: Person detected at front door - suspicious activity",
            "createdBy": user1_id,
            "notificationSound": "/notificationSounds/attention-cam.mp3",
            "photoUrl": "https://example.com/photos/alert1.jpg",
            "videoUrl": "https://example.com/videos/alert1.mp4",
            "isActive": True,
            "isDeleted": False,
            "createdAt": datetime.now(timezone.utc)
        },
        {
            "_id": ObjectId(),
            "missionId": mission1_id,
            "cameraId": camera2_id,
            "message": "MAI Alert: Motion detected in backyard area",
            "createdBy": user1_id,
            "notificationSound": "/notificationSounds/attention-cam.mp3",
            "photoUrl": "https://example.com/photos/alert2.jpg",
            "videoUrl": "https://example.com/videos/alert2.mp4",
            "isActive": True,
            "isDeleted": False,
            "createdAt": datetime.now(timezone.utc)
        },
        {
            "_id": ObjectId(),
            "missionId": mission2_id,
            "cameraId": camera3_id,
            "message": "MAI Alert: Vehicle entering parking lot",
            "createdBy": user2_id,
            "notificationSound": "/notificationSounds/attention-cam.mp3",
            "photoUrl": "https://example.com/photos/alert3.jpg",
            "videoUrl": "https://example.com/videos/alert3.mp4",
            "isActive": True,
            "isDeleted": False,
            "createdAt": datetime.now(timezone.utc)
        }
    ]
    
    await db.missionmessagelogs.insert_many(logs)
    print(f"   ✅ Created {len(logs)} message logs")
    
    # Print summary
    print("\n" + "="*50)
    print("✅ SAMPLE DATA CREATION COMPLETE!")
    print("="*50)
    print(f"\n📊 Summary:")
    print(f"   • Users: {len(users)}")
    print(f"   • Cameras: {len(cameras)}")
    print(f"   • Missions: {len(missions)}")
    print(f"   • Message Logs: {len(logs)}")
    
    print(f"\n🔑 Test Credentials:")
    print(f"   Email: daniel@example.com")
    print(f"   Password: test123")
    print(f"   User ID: {user1_id}")
    
    print(f"\n   Email: lior@example.com")
    print(f"   Password: test123")
    print(f"   User ID: {user2_id}")
    
    print(f"\n📹 Camera IDs:")
    print(f"   • Front Door: {camera1_id}")
    print(f"   • Backyard: {camera2_id}")
    print(f"   • Parking Lot: {camera3_id}")
    
    print(f"\n🎯 Mission IDs:")
    print(f"   • Home Security: {mission1_id}")
    print(f"   • Parking Monitoring: {mission2_id}")
    
    print("\n✅ You can now use these IDs to test the API!")
    print("="*50)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_sample_data())
