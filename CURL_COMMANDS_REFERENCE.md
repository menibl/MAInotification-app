# Complete CURL Commands Reference - All APIs

## Base Configuration

```bash
# Set these variables for all commands
export API_URL="https://aidevicechat.preview.emergentagent.com/api"
export USER_EMAIL="menibl1111@gmail.com"
export USER_ID="menibl1111@gmail.com"
export CAMERA_ID="d9325867-371a-4d08-98bd-aeeee866a348"
```

---

## 1. Authentication APIs

### Register User
```bash
curl -X POST "$API_URL/auth/register" \
-H 'Content-Type: application/json' \
-d '{
    "email": "newuser@example.com",
    "password": "securePassword123"
}'
```

### Login User
```bash
curl -X POST "$API_URL/auth/login" \
-H 'Content-Type: application/json' \
-d '{
    "email": "menibl1111@gmail.com",
    "password": "yourPassword"
}'
```

### Enable 2FA
```bash
curl -X POST "$API_URL/auth/enable-2fa?email=menibl1111@gmail.com"
```

### Verify 2FA Code
```bash
curl -X POST "$API_URL/auth/verify-2fa" \
-H 'Content-Type: application/json' \
-d '{
    "email": "menibl1111@gmail.com",
    "code": "123456"
}'
```

### Get Current User
```bash
curl -X GET "$API_URL/auth/me?token=YOUR_JWT_TOKEN"
```

### Google OAuth Start
```bash
curl -X GET "$API_URL/oauth/google/start"
# This will redirect to Google OAuth
```

---

## 2. Device Management APIs

### Create Device (Auto-Generated ID)
```bash
curl -X POST "$API_URL/devices" \
-H 'Content-Type: application/json' \
-d '{
    "name": "Front Door Camera",
    "type": "camera",
    "user_id": "menibl1111@gmail.com",
    "location": "Main Entrance",
    "description": "Primary entrance security camera",
    "settings": {
        "resolution": "1080p",
        "fps": 30,
        "live_stream_url": "https://www.maifocus.com/show/camera-001"
    }
}'
```

### Create Device with Custom ID
```bash
curl -X POST "$API_URL/devices/create-with-id?device_id=CAM-001&name=Front%20Camera&type=camera&user_id=menibl1111@gmail.com&location=Entrance&status=online"
```

### Get All User Devices
```bash
curl -X GET "$API_URL/devices/menibl1111@gmail.com"
```

### Get Devices (Formatted with jq)
```bash
curl -s "$API_URL/devices/menibl1111@gmail.com" | jq '.[] | {id, name, status, location}'
```

### Update Device
```bash
curl -X PUT "$API_URL/devices/$CAMERA_ID" \
-H 'Content-Type: application/json' \
-d '{
    "name": "Updated Camera Name",
    "status": "offline",
    "location": "New Location",
    "settings": {
        "resolution": "4K",
        "live_stream_url": "https://new-stream.example.com"
    }
}'
```

### Update Device Status Only
```bash
curl -X PUT "$API_URL/devices/$CAMERA_ID/status?status=online"
```

### Update Device ID
```bash
curl -X PUT "$API_URL/devices/old-camera-id/update-id?new_device_id=new-camera-id&preserve_data=true"
```

### Bulk Update Devices
```bash
curl -X PUT "$API_URL/devices/bulk-update" \
-H 'Content-Type: application/json' \
-d '{
    "device_updates": [
        {
            "device_id": "camera-1",
            "updates": {
                "status": "online",
                "location": "Building A"
            }
        },
        {
            "device_id": "camera-2",
            "updates": {
                "name": "Updated Camera 2"
            }
        }
    ]
}'
```

### Delete Single Device
```bash
curl -X DELETE "$API_URL/devices/$CAMERA_ID"
```

### Delete All User Devices
```bash
curl -X DELETE "$API_URL/devices/user/$USER_EMAIL/delete-all?confirm_deletion=true&delete_notifications=true&delete_chat_messages=true"
```

### Delete All User Devices (Safe - Preserves Data)
```bash
curl -X DELETE "$API_URL/devices/user/$USER_EMAIL/delete-all-safe"
```

---

## 3. Chat APIs

### Send Chat Message
```bash
curl -X POST "$API_URL/chat/send?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "message": "What do you see in the camera?",
    "sender": "user"
}'
```

### Send Chat with Media URLs
```bash
curl -X POST "$API_URL/chat/send?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "message": "Check this image",
    "sender": "user",
    "media_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
}'
```

### Send Chat with File IDs
```bash
curl -X POST "$API_URL/chat/send?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "message": "Check the attached files",
    "sender": "user",
    "file_ids": ["file-abc123", "file-def456"]
}'
```

### Send Chat with Referenced Messages
```bash
curl -X POST "$API_URL/chat/send?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "message": "Regarding your previous message...",
    "sender": "user",
    "referenced_messages": ["msg-xyz789"]
}'
```

### Get Chat Messages
```bash
curl -X GET "$API_URL/chat/$USER_EMAIL/$CAMERA_ID"
```

### Get Chat History (Extended)
```bash
curl -X GET "$API_URL/chat/$USER_EMAIL/$CAMERA_ID/history"
```

### Delete Chat History
```bash
curl -X DELETE "$API_URL/chat/$USER_EMAIL/$CAMERA_ID/history"
```

### Direct Image Analysis
```bash
curl -X POST "$API_URL/chat/image-direct?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "image_url": "https://example.com/snapshot.jpg",
    "question": "What do you see in this image?"
}'
```

### Direct Image Analysis (Multiple Images)
```bash
curl -X POST "$API_URL/chat/image-direct?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "media_urls": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
    ],
    "question": "Compare these two images"
}'
```

### Direct Image Analysis (Base64)
```bash
curl -X POST "$API_URL/chat/image-direct?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "question": "Analyze this image"
}'
```

### Mission Chat - Send to All Cameras
```bash
curl -X POST "$API_URL/chat/mission/send?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
    "mission_id": "mission-abc123",
    "message": "All cameras, report your status"
}'
```

### Mission Chat - Get History
```bash
curl -X GET "$API_URL/chat/mission/$USER_EMAIL/Building-Security"
```

### Global Chat - Send
```bash
curl -X POST "$API_URL/chat/global/send?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
    "message": "System-wide announcement: Maintenance in 1 hour"
}'
```

### Global Chat - Get History
```bash
curl -X GET "$API_URL/chat/global/$USER_EMAIL"
```

---

## 4. Notification APIs

### Get User Notifications
```bash
curl -X GET "$API_URL/notifications/$USER_EMAIL"
```

### Get Device Notifications
```bash
curl -X GET "$API_URL/notifications/$USER_EMAIL/device/$CAMERA_ID"
```

### Mark Notification as Read
```bash
curl -X PUT "$API_URL/notifications/notif-abc123/read"
```

### Simulate Device Notification (Testing)
```bash
curl -X POST "$API_URL/simulate/device-notification" \
-H 'Content-Type: application/json' \
-d '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "message": "Test notification message",
    "media_url": "https://example.com/image.jpg",
    "notification_type": "message"
}'
```

---

## 5. Push Notification APIs

### Subscribe to Push Notifications
```bash
curl -X POST "$API_URL/push/subscribe" \
-H 'Content-Type: application/json' \
-d '{
    "user_id": "menibl1111@gmail.com",
    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
    "keys": {
        "p256dh": "BKj...base64...",
        "auth": "Ab9...base64..."
    }
}'
```

### Send Push Notification (Simple)
```bash
curl -X POST "$API_URL/push/send" \
-H 'Content-Type: application/json' \
-d '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "title": "Motion Alert",
    "body": "Person detected at entrance"
}'
```

### Send Push Notification (With Video)
```bash
curl -X POST "$API_URL/push/send" \
-H 'Content-Type: application/json' \
-d '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "title": "🎥 Motion Alert",
    "body": "Person detected - Click to view video",
    "image": "https://picsum.photos/400/300",
    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "sound_id": "alert"
}'
```

### Send Push Notification (Complete with All Metadata)
```bash
curl -X POST "$API_URL/push/send" \
-H 'Content-Type: application/json' \
-d '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "title": "Motion Detected",
    "body": "Person at entrance",
    "camera_id": "CAM-001",
    "camera_name": "Entrance Camera",
    "mission_id": "mission-123",
    "mission_name": "Building Security",
    "user_email": "menibl1111@gmail.com",
    "video_url": "https://example.com/video.mp4",
    "image": "https://example.com/image.jpg",
    "image_url": "https://example.com/image.jpg",
    "rtmp_code": "rtmp://stream.server.com/live/cam1",
    "sound_id": "alert",
    "require_interaction": true
}'
```

### Get User Push Subscriptions
```bash
curl -X GET "$API_URL/push/subscriptions/$USER_EMAIL"
```

### Unsubscribe from Push (All)
```bash
curl -X DELETE "$API_URL/push/unsubscribe/$USER_EMAIL"
```

### Unsubscribe from Push (Specific Endpoint)
```bash
curl -X DELETE "$API_URL/push/unsubscribe/$USER_EMAIL?endpoint=https://fcm.googleapis.com/fcm/send/..."
```

---

## 6. File Upload APIs

### Upload File
```bash
curl -X POST "$API_URL/files/upload?user_id=$USER_EMAIL" \
-F "file=@/path/to/your/file.pdf" \
-F "device_id=$CAMERA_ID" \
-F "message_id=msg-abc123"
```

### Upload Image
```bash
curl -X POST "$API_URL/files/upload?user_id=$USER_EMAIL" \
-F "file=@/path/to/image.jpg"
```

### Get/Download File
```bash
curl -X GET "$API_URL/files/file-abc123" -o downloaded_file.pdf
```

### Get User Files List
```bash
curl -X GET "$API_URL/files/user/$USER_EMAIL"
```

### Delete File
```bash
curl -X DELETE "$API_URL/files/file-abc123"
```

---

## 7. AI Settings APIs

### Get Chat Settings
```bash
curl -X GET "$API_URL/chat/settings/$USER_EMAIL/$CAMERA_ID"
```

### Create Chat Settings
```bash
curl -X POST "$API_URL/chat/settings/$USER_EMAIL/$CAMERA_ID" \
-H 'Content-Type: application/json' \
-d '{
    "role_name": "Security Expert AI",
    "system_message": "You are a professional security expert monitoring cameras",
    "instructions": "Watch for suspicious activities and unauthorized access",
    "model": "gpt-5-nano"
}'
```

### Update Chat Settings
```bash
curl -X PUT "$API_URL/chat/settings/$USER_EMAIL/$CAMERA_ID" \
-H 'Content-Type: application/json' \
-d '{
    "role_name": "Updated Security AI",
    "instructions": "Focus on detecting vehicles in restricted areas"
}'
```

### Delete Chat Settings
```bash
curl -X DELETE "$API_URL/chat/settings/$USER_EMAIL/$CAMERA_ID"
```

### Parse Role Change Command
```bash
curl -X POST "$API_URL/chat/parse-role-change" \
-H 'Content-Type: application/json' \
-d '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "message": "act as a detective looking for clues"
}'
```

---

## 8. Camera Prompt APIs

### Get Camera Prompt
```bash
curl -X GET "$API_URL/camera/prompt/$USER_EMAIL/$CAMERA_ID"
```

### Update Camera Prompt
```bash
curl -X PUT "$API_URL/camera/prompt/$USER_EMAIL/$CAMERA_ID" \
-H 'Content-Type: application/json' \
-d '{
    "instructions": "watch for packages left at the door"
}'
```

### Parse Camera Prompt Command
```bash
curl -X POST "$API_URL/camera/prompt/parse" \
-H 'Content-Type: application/json' \
-d '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "message": "watch for vehicles parking in no-parking zones"
}'
```

### Fix Camera Prompt from Feedback
```bash
curl -X POST "$API_URL/camera/prompt/fix-from-feedback" \
-H 'Content-Type: application/json' \
-d '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "message": "You missed the delivery truck. Watch for all large vehicles.",
    "referenced_messages": ["msg-previous-alert"]
}'
```

---

## 9. Mission APIs

### Get User Missions
```bash
curl -X GET "$API_URL/missions/$USER_EMAIL"
```

### Create Mission
```bash
curl -X POST "$API_URL/missions?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
    "name": "Parking Security",
    "description": "Monitor all parking lot entrances and exits",
    "camera_ids": ["camera-1", "camera-2", "camera-3"]
}'
```

### Assign Cameras to Mission
```bash
curl -X POST "$API_URL/missions/assign-cameras" \
-H 'Content-Type: application/json' \
-d '{
    "user_id": "menibl1111@gmail.com",
    "mission_id": "mission-abc123",
    "camera_ids": ["camera-1", "camera-2", "camera-3", "camera-4"]
}'
```

---

## 10. Sounds APIs

### Get Sound by ID
```bash
curl -X GET "$API_URL/sounds/alert" -o alert.mp3
```

### Get Significant Sound
```bash
curl -X GET "$API_URL/sounds/significant" -o significant.mp3
```

### Get Routine Sound
```bash
curl -X GET "$API_URL/sounds/routine" -o routine.mp3
```

---

## 11. Status & Utilities

### Health Check
```bash
curl -X GET "$API_URL/status"
```

### Status Check (with tracking)
```bash
curl -X POST "$API_URL/status/check" \
-H 'Content-Type: application/json' \
-d '{
    "client_name": "mobile-app"
}'
```

---

## Complete Workflow Examples

### Example 1: Create Camera and Send Notification

```bash
#!/bin/bash
API_URL="https://aidevicechat.preview.emergentagent.com/api"
USER_EMAIL="menibl1111@gmail.com"

# Step 1: Create camera
echo "Creating camera..."
CAMERA_RESPONSE=$(curl -s -X POST "$API_URL/devices" \
-H 'Content-Type: application/json' \
-d '{
    "name": "New Entrance Camera",
    "type": "camera",
    "user_id": "'$USER_EMAIL'",
    "location": "Main Entrance"
}')

CAMERA_ID=$(echo $CAMERA_RESPONSE | jq -r '.id')
echo "Camera created with ID: $CAMERA_ID"

# Step 2: Send notification
echo "Sending notification..."
curl -X POST "$API_URL/push/send" \
-H 'Content-Type: application/json' \
-d '{
    "user_id": "'$USER_EMAIL'",
    "device_id": "'$CAMERA_ID'",
    "title": "Camera Online",
    "body": "New camera is now active",
    "sound_id": "alert"
}'

echo "Done!"
```

### Example 2: Chat with AI and Get Response

```bash
#!/bin/bash
API_URL="https://aidevicechat.preview.emergentagent.com/api"
USER_EMAIL="menibl1111@gmail.com"
CAMERA_ID="d9325867-371a-4d08-98bd-aeeee866a348"

# Send message
curl -X POST "$API_URL/chat/send?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
    "device_id": "'$CAMERA_ID'",
    "message": "What do you see in the camera right now?",
    "sender": "user"
}' | jq '.'
```

### Example 3: Update Camera Monitoring Instructions

```bash
#!/bin/bash
API_URL="https://aidevicechat.preview.emergentagent.com/api"
USER_EMAIL="menibl1111@gmail.com"
CAMERA_ID="d9325867-371a-4d08-98bd-aeeee866a348"

# Update camera prompt
curl -X PUT "$API_URL/camera/prompt/$USER_EMAIL/$CAMERA_ID" \
-H 'Content-Type: application/json' \
-d '{
    "instructions": "watch for delivery trucks and notify immediately"
}' | jq '.'
```

### Example 4: List All Cameras and Send Notification to Each

```bash
#!/bin/bash
API_URL="https://aidevicechat.preview.emergentagent.com/api"
USER_EMAIL="menibl1111@gmail.com"

# Get all cameras
CAMERAS=$(curl -s "$API_URL/devices/$USER_EMAIL")

# Send notification to each camera
echo "$CAMERAS" | jq -r '.[] | .id' | while read CAMERA_ID; do
    CAMERA_NAME=$(echo "$CAMERAS" | jq -r ".[] | select(.id==\"$CAMERA_ID\") | .name")
    echo "Sending notification to: $CAMERA_NAME"
    
    curl -s -X POST "$API_URL/push/send" \
    -H 'Content-Type: application/json' \
    -d '{
        "user_id": "'$USER_EMAIL'",
        "device_id": "'$CAMERA_ID'",
        "title": "System Check",
        "body": "Testing notification for '$CAMERA_NAME'",
        "sound_id": "routine"
    }' | jq -r '.message'
    
    sleep 1
done

echo "All notifications sent!"
```

---

## Quick Reference Table

| Category | Endpoint | Method | Purpose |
|----------|----------|--------|---------|
| Auth | `/auth/register` | POST | Register new user |
| Auth | `/auth/login` | POST | Login user |
| Auth | `/auth/enable-2fa` | POST | Enable 2FA |
| Auth | `/auth/verify-2fa` | POST | Verify 2FA code |
| Auth | `/auth/me` | GET | Get current user |
| Devices | `/devices` | POST | Create device |
| Devices | `/devices/{user_id}` | GET | List devices |
| Devices | `/devices/{device_id}` | PUT | Update device |
| Devices | `/devices/{device_id}` | DELETE | Delete device |
| Chat | `/chat/send` | POST | Send chat message |
| Chat | `/chat/{user}/{device}` | GET | Get chat history |
| Chat | `/chat/image-direct` | POST | AI image analysis |
| Notifications | `/notifications/{user}` | GET | Get notifications |
| Push | `/push/send` | POST | Send push notification |
| Push | `/push/subscribe` | POST | Subscribe to push |
| Files | `/files/upload` | POST | Upload file |
| Files | `/files/{file_id}` | GET | Download file |
| AI Settings | `/chat/settings/{user}/{device}` | GET/POST/PUT | Manage AI settings |
| Camera Prompt | `/camera/prompt/{user}/{device}` | GET/PUT | Manage camera prompts |
| Missions | `/missions/{user_id}` | GET | List missions |
| Missions | `/missions` | POST | Create mission |
| Sounds | `/sounds/{sound_id}` | GET | Get notification sound |
| Status | `/status` | GET | Health check |

---

## Testing Tips

### Use jq for Pretty Output
```bash
curl -s "$API_URL/devices/$USER_EMAIL" | jq '.'
```

### Save Response to Variable
```bash
RESPONSE=$(curl -s "$API_URL/devices/$USER_EMAIL")
echo $RESPONSE | jq '.[] | .name'
```

### Check HTTP Status Code
```bash
curl -w "%{http_code}" -s -o /dev/null "$API_URL/status"
```

### Verbose Output (Debug)
```bash
curl -v "$API_URL/status"
```

### Save Response to File
```bash
curl -s "$API_URL/devices/$USER_EMAIL" > devices.json
```

---

All commands are ready to use! Just replace the placeholder values with your actual data.
