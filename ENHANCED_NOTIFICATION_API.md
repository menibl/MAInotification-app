# Enhanced Notification API - Complete Metadata Support

## Overview
Every notification now includes comprehensive metadata about the camera, mission, user, and media.

---

## Current API Fields

### Send Push Notification API

**Endpoint:** `POST /api/push/send`

### All Available Fields:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `user_id` | string | ✅ Yes | User ID (email) | `"menibl1111@gmail.com"` |
| `device_id` | string | ✅ Yes | Device/Camera ID | `"d9325867-371a-4d08-98bd-aeeee866a348"` |
| `title` | string | ✅ Yes | Notification title | `"Motion Detected"` |
| `body` | string | ✅ Yes | Notification message | `"Person at entrance"` |
| `camera_id` | string | ❌ No | Camera ID (defaults to device_id) | `"CAM-001"` |
| `camera_name` | string | ❌ No | Camera display name | `"Entrance Camera"` |
| `mission_id` | string | ❌ No | Mission ID | `"mission-abc123"` |
| `mission_name` | string | ❌ No | Mission display name | `"Building Security"` |
| `user_email` | string | ❌ No | User email | `"menibl1111@gmail.com"` |
| `video_url` | string | ❌ No | Event video URL | `"https://example.com/video.mp4"` |
| `image` | string | ❌ No | Snapshot image URL | `"https://example.com/image.jpg"` |
| `image_url` | string | ❌ No | Image URL (alias for image) | `"https://example.com/image.jpg"` |
| `rtmp_code` | string | ❌ No | RTMP stream URL/code | `"rtmp://server/live/stream123"` |
| `sound_id` | string | ❌ No | Sound type | `"alert"`, `"significant"`, `"routine"` |
| `sound_url` | string | ❌ No | Custom sound URL | `"https://example.com/sound.mp3"` |
| `icon` | string | ❌ No | Notification icon | `"/icon.png"` |
| `badge` | string | ❌ No | Badge icon | `"/badge.png"` |
| `data` | object | ❌ No | Additional custom data | `{"key": "value"}` |
| `actions` | array | ❌ No | Notification actions | `[{"action": "view", "title": "View"}]` |
| `require_interaction` | boolean | ❌ No | Keep notification visible | `true` or `false` |

---

## Complete Example with All Metadata

```bash
curl --location 'https://aidevicechat.preview.emergentagent.com/api/push/send' \
--header 'Content-Type: application/json' \
--data '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "title": "🔴 Motion Detected",
    "body": "Person detected at main entrance - Click to view",
    
    "camera_id": "CAM-ENTRANCE-001",
    "camera_name": "Entrance Camera",
    "mission_id": "mission-building-security",
    "mission_name": "Building Security",
    "user_email": "menibl1111@gmail.com",
    
    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "image": "https://picsum.photos/400/300",
    "image_url": "https://picsum.photos/400/300",
    "rtmp_code": "rtmp://stream.example.com/live/camera-entrance-001",
    
    "sound_id": "alert",
    "icon": "/manifest-icon-192.png",
    "badge": "/manifest-icon-192.png",
    "require_interaction": true
}'
```

---

## Minimal Example (Only Required Fields)

```bash
curl --location 'https://aidevicechat.preview.emergentagent.com/api/push/send' \
--header 'Content-Type: application/json' \
--data '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "title": "Alert",
    "body": "Motion detected"
}'
```

---

## Example with Camera & Mission Context

```bash
curl --location 'https://aidevicechat.preview.emergentagent.com/api/push/send' \
--header 'Content-Type: application/json' \
--data '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
    "title": "Parking Area Activity",
    "body": "Vehicle detected in restricted zone",
    
    "camera_id": "CAM-PARKING-01",
    "camera_name": "Parking Camera 01",
    "mission_id": "mission-parking-security",
    "mission_name": "Parking Security Patrol",
    
    "video_url": "https://example.com/events/parking-event-123.mp4",
    "image": "https://example.com/snapshots/parking-123.jpg",
    "rtmp_code": "rtmp://stream.company.com/live/parking-cam-01",
    
    "sound_id": "significant"
}'
```

---

## Example with RTMP Stream

```bash
curl --location 'https://aidevicechat.preview.emergentagent.com/api/push/send' \
--header 'Content-Type: application/json' \
--data '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "8fe5a91b-7c90-44e0-9c1d-dfeb113e10dd",
    "title": "Live Stream Alert",
    "body": "Suspicious activity - View live stream",
    
    "camera_name": "Camera 203",
    "rtmp_code": "rtmp://live.streaming.com/app/stream-key-203",
    
    "sound_id": "alert",
    "require_interaction": true
}'
```

---

## What Happens When You Send a Notification

### 1. **Push Notification Sent**
Browser receives push notification with all metadata in the `data` field:
```json
{
  "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
  "camera_id": "CAM-ENTRANCE-001",
  "camera_name": "Entrance Camera",
  "mission_id": "mission-building-security",
  "mission_name": "Building Security",
  "user_email": "menibl1111@gmail.com",
  "video_url": "https://example.com/video.mp4",
  "image_url": "https://example.com/image.jpg",
  "rtmp_code": "rtmp://stream.example.com/live/camera"
}
```

### 2. **Stored in Database**
Notification saved with all metadata in `notifications` collection:
```json
{
  "id": "notif-abc123",
  "user_id": "menibl1111@gmail.com",
  "device_id": "d9325867-371a-4d08-98bd-aeeee866a348",
  "type": "push",
  "content": "Motion Detected: Person at entrance",
  "camera_id": "CAM-ENTRANCE-001",
  "camera_name": "Entrance Camera",
  "mission_id": "mission-building-security",
  "mission_name": "Building Security",
  "user_email": "menibl1111@gmail.com",
  "video_url": "https://example.com/video.mp4",
  "image_url": "https://example.com/image.jpg",
  "media_url": "https://example.com/video.mp4",
  "rtmp_code": "rtmp://stream.example.com/live/camera",
  "read": false,
  "timestamp": "2025-01-09T12:34:56.789Z"
}
```

### 3. **Displayed in Notifications Page**
User sees notification with:
- Camera name
- Notification content
- Image preview (if provided)
- Timestamp
- "Go to chat →" button

### 4. **Click Navigation**
When user clicks:
- Opens chat for that camera
- Expands video panels
- Shows event video (if video_url provided)
- Shows live stream (if camera has live_stream_url or rtmp_code)

---

## Response Format

```json
{
  "success": true,
  "message": "Sent 1 notifications, 0 failed",
  "sent_count": 1,
  "failed_count": 0,
  "total_subscriptions": 1
}
```

---

## Automated Script - Send Notification with Full Metadata

Save as `send_notification.sh`:

```bash
#!/bin/bash

USER_EMAIL="menibl1111@gmail.com"
CAMERA_ID="d9325867-371a-4d08-98bd-aeeee866a348"
API_URL="https://aidevicechat.preview.emergentagent.com/api"

# Notification details
TITLE="Motion Alert"
BODY="Person detected at entrance"
CAMERA_NAME="Entrance Camera"
MISSION_ID="mission-001"
MISSION_NAME="Building Security"
VIDEO_URL="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
IMAGE_URL="https://picsum.photos/400/300"
RTMP_CODE="rtmp://stream.example.com/live/entrance"

# Send notification
curl -X POST "$API_URL/push/send" \
-H 'Content-Type: application/json' \
-d "{
    \"user_id\": \"$USER_EMAIL\",
    \"device_id\": \"$CAMERA_ID\",
    \"title\": \"$TITLE\",
    \"body\": \"$BODY\",
    \"camera_id\": \"$CAMERA_ID\",
    \"camera_name\": \"$CAMERA_NAME\",
    \"mission_id\": \"$MISSION_ID\",
    \"mission_name\": \"$MISSION_NAME\",
    \"user_email\": \"$USER_EMAIL\",
    \"video_url\": \"$VIDEO_URL\",
    \"image\": \"$IMAGE_URL\",
    \"image_url\": \"$IMAGE_URL\",
    \"rtmp_code\": \"$RTMP_CODE\",
    \"sound_id\": \"alert\",
    \"require_interaction\": true
}" | jq '.'

echo ""
echo "✅ Notification sent with complete metadata!"
```

**Usage:**
```bash
chmod +x send_notification.sh
./send_notification.sh
```

---

## Summary of Current vs Enhanced

### Before (What You Had):
```json
{
  "user_id": "...",
  "device_id": "...",
  "title": "...",
  "body": "...",
  "image": "...",
  "video_url": "...",
  "sound_id": "..."
}
```

### Now (What You Have):
```json
{
  "user_id": "...",
  "device_id": "...",
  "title": "...",
  "body": "...",
  
  // NEW: Camera metadata
  "camera_id": "...",
  "camera_name": "...",
  
  // NEW: Mission metadata
  "mission_id": "...",
  "mission_name": "...",
  
  // NEW: User metadata
  "user_email": "...",
  
  // NEW: Media URLs
  "video_url": "...",
  "image": "...",
  "image_url": "...",
  
  // NEW: RTMP stream
  "rtmp_code": "...",
  
  // Existing
  "sound_id": "..."
}
```

---

## Testing Your Cameras

### 1. Get Your Camera IDs
```bash
curl -s 'https://aidevicechat.preview.emergentagent.com/api/devices/menibl1111@gmail.com' | jq '.[] | {id, name}'
```

### 2. Send Test Notification with Full Metadata
```bash
# Replace CAMERA_ID with your actual camera ID
curl -X POST 'https://aidevicechat.preview.emergentagent.com/api/push/send' \
-H 'Content-Type: application/json' \
-d '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "YOUR_CAMERA_ID",
    "title": "Test with Full Metadata",
    "body": "Testing all fields",
    "camera_name": "My Camera",
    "mission_name": "Test Mission",
    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "image": "https://picsum.photos/400/300",
    "rtmp_code": "rtmp://test.stream/live",
    "sound_id": "alert"
}'
```

---

## All Fields Are Stored and Available

When you retrieve notifications via:
```bash
GET /api/notifications/{user_id}
```

Each notification includes ALL the metadata you sent:
- camera_id
- camera_name
- mission_id
- mission_name
- user_email
- video_url
- image_url
- rtmp_code

This data is preserved in the database and can be used by your frontend or other services!
