# MAI Focus - Complete API Documentation

## Table of Contents
1. [Environment Variables](#environment-variables)
2. [Authentication APIs](#authentication-apis)
3. [Device Management APIs](#device-management-apis)
4. [Chat APIs](#chat-apis)
5. [Notification APIs](#notification-apis)
6. [Push Notification APIs](#push-notification-apis)
7. [File Upload APIs](#file-upload-apis)
8. [AI Settings APIs](#ai-settings-apis)
9. [Camera Prompt APIs](#camera-prompt-apis)
10. [Mission APIs](#mission-apis)
11. [Sounds APIs](#sounds-apis)
12. [WebSocket API](#websocket-api)
13. [Status & Utilities](#status--utilities)

---

## Environment Variables

### Backend Environment Variables (`/app/backend/.env`)

```bash
# MongoDB Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"

# CORS Configuration
CORS_ORIGINS="*"

# VAPID Keys for Push Notifications
VAPID_PRIVATE_KEY="your-vapid-private-key"
VAPID_PUBLIC_KEY="your-vapid-public-key"
VAPID_EMAIL="mailto:admin@device-chat.com"

# OpenAI API Configuration
OPENAI_API_KEY="sk-proj-..."

# JWT Authentication
JWT_SECRET="your-jwt-secret-key"

# Google OAuth (Optional)
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
OAUTH_GOOGLE_REDIRECT_URI="https://your-domain.com/api/oauth/google/callback"

# Backend URL (for file serving)
BACKEND_URL="http://localhost:8000"
```

### Frontend Environment Variables (`/app/frontend/.env`)

```bash
# Backend API URL
REACT_APP_BACKEND_URL=https://your-domain.com

# WebSocket Configuration (for development)
WDS_SOCKET_PORT=443

# VAPID Public Key (same as backend)
REACT_APP_VAPID_PUBLIC_KEY="your-vapid-public-key"
```

---

## Authentication APIs

### 1. Register User
**Endpoint:** `POST /api/auth/register`

**Description:** Create a new user account with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "email": "user@example.com"
}
```

---

### 2. Login User
**Endpoint:** `POST /api/auth/login`

**Description:** Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response (No 2FA):**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "email": "user@example.com"
}
```

**Response (2FA Required):**
```json
{
  "success": true,
  "requires_2fa": true,
  "email": "user@example.com"
}
```

---

### 3. Enable 2FA
**Endpoint:** `POST /api/auth/enable-2fa?email=user@example.com`

**Description:** Enable Two-Factor Authentication for an account.

**Query Parameters:**
- `email` (string, required): User email

**Response:**
```json
{
  "otpauth_url": "otpauth://totp/MAI%20Focus:user@example.com?secret=ABCD1234&issuer=MAI%20Focus",
  "secret": "ABCD1234EFGH5678"
}
```

---

### 4. Verify 2FA Code
**Endpoint:** `POST /api/auth/verify-2fa`

**Description:** Verify 2FA code and complete login.

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "email": "user@example.com"
}
```

---

### 5. Get Current User
**Endpoint:** `GET /api/auth/me?token=your-jwt-token`

**Description:** Get current authenticated user info.

**Query Parameters:**
- `token` (string, optional): JWT token

**Response:**
```json
{
  "authenticated": true,
  "email": "user@example.com"
}
```

---

### 6. Google OAuth Start
**Endpoint:** `GET /api/oauth/google/start`

**Description:** Initiate Google OAuth login flow. Redirects to Google.

**Response:** Redirects to Google OAuth consent screen.

---

### 7. Google OAuth Callback
**Endpoint:** `GET /api/oauth/google/callback?code=auth_code`

**Description:** Handle Google OAuth callback and create/login user.

**Query Parameters:**
- `code` (string, required): OAuth authorization code from Google

**Response:** Redirects to `/?token={jwt_token}&email={email}`

---

## Device Management APIs

### 1. Create Device
**Endpoint:** `POST /api/devices`

**Description:** Create a new device.

**Request Body:**
```json
{
  "name": "Security Camera 01",
  "type": "camera",
  "user_id": "user@example.com",
  "location": "Front Door",
  "description": "Main entrance camera",
  "settings": {
    "live_stream_url": "https://stream.example.com/camera1",
    "default_sound_id": "alert"
  }
}
```

**Response:**
```json
{
  "id": "abc123-def456",
  "name": "Security Camera 01",
  "type": "camera",
  "user_id": "user@example.com",
  "status": "online",
  "location": "Front Door",
  "description": "Main entrance camera",
  "settings": {...},
  "last_seen": "2025-01-09T10:48:38.123Z",
  "created_at": "2025-01-09T10:48:38.123Z",
  "updated_at": "2025-01-09T10:48:38.123Z"
}
```

---

### 2. Create Device with Custom ID
**Endpoint:** `POST /api/devices/create-with-id`

**Description:** Create a device with a specific ID.

**Query Parameters:**
- `device_id` (string, required): Custom device ID
- `name` (string, required): Device name
- `type` (string, required): Device type
- `user_id` (string, required): User ID
- `location` (string, optional): Device location
- `description` (string, optional): Device description
- `settings` (object, optional): Device settings
- `status` (string, optional): Device status (default: "online")

**Response:**
```json
{
  "success": true,
  "message": "Device created with ID: custom-id-123",
  "device": {...}
}
```

---

### 3. Get User Devices
**Endpoint:** `GET /api/devices/{user_id}`

**Description:** Get all devices for a user.

**Path Parameters:**
- `user_id` (string, required): User ID

**Response:**
```json
[
  {
    "id": "device-1",
    "name": "Camera 01",
    "type": "camera",
    "user_id": "user@example.com",
    "status": "online",
    ...
  },
  {
    "id": "device-2",
    "name": "Door Sensor",
    "type": "sensor",
    "user_id": "user@example.com",
    "status": "offline",
    ...
  }
]
```

---

### 4. Update Device
**Endpoint:** `PUT /api/devices/{device_id}`

**Description:** Update device information.

**Path Parameters:**
- `device_id` (string, required): Device ID

**Request Body:**
```json
{
  "name": "Updated Camera Name",
  "status": "offline",
  "location": "New Location",
  "settings": {
    "live_stream_url": "https://new-stream.example.com"
  }
}
```

**Response:**
```json
{
  "id": "device-1",
  "name": "Updated Camera Name",
  ...
}
```

---

### 5. Update Device Status
**Endpoint:** `PUT /api/devices/{device_id}/status?status=online`

**Description:** Update only the device status.

**Path Parameters:**
- `device_id` (string, required): Device ID

**Query Parameters:**
- `status` (string, required): New status ("online" or "offline")

**Response:**
```json
{
  "success": true
}
```

---

### 6. Update Device ID
**Endpoint:** `PUT /api/devices/{old_device_id}/update-id?new_device_id=new-id&preserve_data=true`

**Description:** Change a device's ID and optionally preserve related data.

**Path Parameters:**
- `old_device_id` (string, required): Current device ID

**Query Parameters:**
- `new_device_id` (string, required): New device ID
- `preserve_data` (boolean, optional): Whether to migrate chat/notification data (default: true)

**Response:**
```json
{
  "success": true,
  "message": "Device ID updated from 'old-id' to 'new-id'",
  "old_device_id": "old-id",
  "new_device_id": "new-id",
  "data_preservation": {
    "notifications_updated": 15,
    "messages_updated": 42
  },
  "device": {...}
}
```

---

### 7. Bulk Update Devices
**Endpoint:** `PUT /api/devices/bulk-update`

**Description:** Update multiple devices at once.

**Request Body:**
```json
{
  "device_updates": [
    {
      "device_id": "device-1",
      "updates": {
        "status": "online",
        "location": "New Location"
      }
    },
    {
      "device_id": "device-2",
      "updates": {
        "name": "Updated Name"
      }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "updated_count": 2,
  "failed_updates": [],
  "total_attempted": 2
}
```

---

### 8. Delete Device
**Endpoint:** `DELETE /api/devices/{device_id}`

**Description:** Delete a single device.

**Path Parameters:**
- `device_id` (string, required): Device ID

**Response:**
```json
{
  "success": true,
  "message": "Device deleted successfully"
}
```

---

### 9. Delete All User Devices
**Endpoint:** `DELETE /api/devices/user/{user_id}/delete-all?confirm_deletion=true&delete_notifications=true&delete_chat_messages=true`

**Description:** Delete all devices for a user and optionally related data.

**Path Parameters:**
- `user_id` (string, required): User ID

**Query Parameters:**
- `confirm_deletion` (boolean, required): Must be `true` to proceed
- `delete_notifications` (boolean, optional): Delete notifications (default: true)
- `delete_chat_messages` (boolean, optional): Delete chat messages (default: true)
- `delete_push_subscriptions` (boolean, optional): Delete push subscriptions (default: false)

**Response:**
```json
{
  "success": true,
  "message": "Successfully deleted all devices and related data",
  "user_id": "user@example.com",
  "deleted_devices": ["device-1", "device-2"],
  "deleted_count": 2,
  "related_data_deleted": {
    "devices": 2,
    "notifications": 50,
    "chat_messages": 150
  }
}
```

---

### 10. Delete All User Devices (Safe)
**Endpoint:** `DELETE /api/devices/user/{user_id}/delete-all-safe`

**Description:** Delete all devices but preserve all related data.

**Path Parameters:**
- `user_id` (string, required): User ID

**Response:**
```json
{
  "success": true,
  "message": "Successfully deleted 2 devices for user",
  "user_id": "user@example.com",
  "deleted_devices": ["device-1", "device-2"],
  "deleted_count": 2,
  "note": "Related data (notifications, messages) was preserved"
}
```

---

## Chat APIs

### 1. Send Chat Message
**Endpoint:** `POST /api/chat/send?user_id=user@example.com`

**Description:** Send a chat message with optional AI response, file attachments, media URLs, and message references.

**Query Parameters:**
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "device_id": "camera-1",
  "message": "What do you see in this image?",
  "sender": "user",
  "media_urls": ["https://example.com/image.jpg"],
  "file_ids": ["file-abc123"],
  "referenced_messages": ["msg-xyz789"],
  "camera_id": "camera-1",
  "mission_id": "mission-1",
  "title": "User Question",
  "body": "What do you see?",
  "image_url": "https://example.com/image.jpg",
  "video_url": "https://example.com/video.mp4",
  "sound_id": "alert"
}
```

**Response (Normal AI Response):**
```json
{
  "success": true,
  "message_id": "msg-user-123",
  "ai_response": {
    "message": "I can see a person approaching the front door...",
    "message_id": "msg-ai-456",
    "timestamp": "2025-01-09T10:48:38.123Z"
  }
}
```

**Response (Camera Prompt Updated):**
```json
{
  "success": true,
  "message_id": "msg-user-123",
  "camera_prompt_changed": true,
  "ai_response": {
    "message": "✅ Camera monitoring updated. I will now watch for: people entering restricted areas",
    "message_id": "msg-system-789",
    "detected": "camera_prompt_change",
    "new_instructions": "watch for people entering restricted areas"
  }
}
```

---

### 2. Get Chat Messages
**Endpoint:** `GET /api/chat/{user_id}/{device_id}`

**Description:** Get all chat messages between user and device.

**Path Parameters:**
- `user_id` (string, required): User ID
- `device_id` (string, required): Device ID

**Response:**
```json
[
  {
    "id": "msg-1",
    "user_id": "user@example.com",
    "device_id": "camera-1",
    "message": "Hello camera",
    "sender": "user",
    "ai_response": false,
    "timestamp": "2025-01-09T10:48:38.123Z"
  },
  {
    "id": "msg-2",
    "user_id": "user@example.com",
    "device_id": "camera-1",
    "message": "Hello! How can I help you today?",
    "sender": "ai",
    "ai_response": true,
    "timestamp": "2025-01-09T10:48:39.456Z"
  }
]
```

---

### 3. Get Chat History (Extended)
**Endpoint:** `GET /api/chat/{user_id}/{device_id}/history`

**Description:** Get extended chat history stored in chat_histories collection.

**Path Parameters:**
- `user_id` (string, required): User ID
- `device_id` (string, required): Device ID

**Response:**
```json
{
  "user_id": "user@example.com",
  "device_id": "camera-1",
  "history": [
    {
      "id": "msg-1",
      "message": "Hello",
      "sender": "user",
      "timestamp": "2025-01-09T10:48:38.123Z",
      "ai_response": false
    }
  ]
}
```

---

### 4. Delete Chat History
**Endpoint:** `DELETE /api/chat/{user_id}/{device_id}/history`

**Description:** Delete all chat history for a device.

**Path Parameters:**
- `user_id` (string, required): User ID
- `device_id` (string, required): Device ID

**Response:**
```json
{
  "success": true,
  "message": "Chat history deleted",
  "deleted_count": 42
}
```

---

### 5. Direct Image Analysis
**Endpoint:** `POST /api/chat/image-direct?user_id=user@example.com`

**Description:** Send image(s) directly for AI vision analysis without chat context.

**Query Parameters:**
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "device_id": "camera-1",
  "image_data": "base64-encoded-image-data",
  "image_url": "https://example.com/image.jpg",
  "media_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
  "video_url": "https://example.com/event-video.mp4",
  "question": "What do you see?",
  "camera_id": "camera-1",
  "mission_id": "mission-1",
  "title": "Motion Detected",
  "body": "Person at door",
  "sound_id": "significant"
}
```

**Response:**
```json
{
  "success": true,
  "ai_response": "I can see a person approaching the door carrying a package...",
  "displayed_in_chat": true,
  "message_id": "msg-abc123"
}
```

---

### 6. Mission Chat - Send
**Endpoint:** `POST /api/chat/mission/send?user_id=user@example.com`

**Description:** Send a message to all cameras in a mission (fan-out).

**Query Parameters:**
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "mission_id": "mission-1",
  "message": "All cameras, report status"
}
```

**Response:**
```json
{
  "success": true,
  "mission_id": "mission-1",
  "cameras_messaged": ["camera-1", "camera-2", "camera-3"],
  "message_ids": ["msg-1", "msg-2", "msg-3"]
}
```

---

### 7. Mission Chat - Get History
**Endpoint:** `GET /api/chat/mission/{user_id}/{mission_name}`

**Description:** Get aggregated chat history for all cameras in a mission.

**Path Parameters:**
- `user_id` (string, required): User ID
- `mission_name` (string, required): Mission name

**Response:**
```json
{
  "mission_name": "Building Security",
  "cameras": ["camera-1", "camera-2"],
  "messages": [
    {
      "id": "msg-1",
      "camera_id": "camera-1",
      "message": "Status: All clear",
      "sender": "ai",
      "timestamp": "2025-01-09T10:48:38.123Z"
    }
  ]
}
```

---

### 8. Global Chat - Send
**Endpoint:** `POST /api/chat/global/send?user_id=user@example.com`

**Description:** Send a message to global chat (visible across all missions).

**Query Parameters:**
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "message": "System-wide announcement: Testing in progress"
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "msg-global-123",
  "scope": "global"
}
```

---

### 9. Global Chat - Get History
**Endpoint:** `GET /api/chat/global/{user_id}`

**Description:** Get global chat history.

**Path Parameters:**
- `user_id` (string, required): User ID

**Response:**
```json
{
  "scope": "global",
  "messages": [
    {
      "id": "msg-1",
      "message": "System announcement",
      "sender": "user",
      "timestamp": "2025-01-09T10:48:38.123Z"
    }
  ]
}
```

---

## Notification APIs

### 1. Get User Notifications
**Endpoint:** `GET /api/notifications/{user_id}`

**Description:** Get all notifications for a user.

**Path Parameters:**
- `user_id` (string, required): User ID

**Response:**
```json
[
  {
    "id": "notif-1",
    "user_id": "user@example.com",
    "device_id": "camera-1",
    "type": "alert",
    "content": "Motion detected at front door",
    "media_url": "https://example.com/snapshot.jpg",
    "read": false,
    "timestamp": "2025-01-09T10:48:38.123Z"
  }
]
```

---

### 2. Get Device Notifications
**Endpoint:** `GET /api/notifications/{user_id}/device/{device_id}`

**Description:** Get all notifications for a specific device.

**Path Parameters:**
- `user_id` (string, required): User ID
- `device_id` (string, required): Device ID

**Response:**
```json
[
  {
    "id": "notif-1",
    "user_id": "user@example.com",
    "device_id": "camera-1",
    "type": "motion",
    "content": "Motion detected",
    "media_url": "https://example.com/snapshot.jpg",
    "read": false,
    "timestamp": "2025-01-09T10:48:38.123Z"
  }
]
```

---

### 3. Mark Notification as Read
**Endpoint:** `PUT /api/notifications/{notification_id}/read`

**Description:** Mark a notification as read.

**Path Parameters:**
- `notification_id` (string, required): Notification ID

**Response:**
```json
{
  "success": true
}
```

---

### 4. Simulate Device Notification
**Endpoint:** `POST /api/simulate/device-notification`

**Description:** Simulate a device sending a notification (for testing).

**Request Body:**
```json
{
  "device_id": "camera-1",
  "user_id": "user@example.com",
  "title": "Motion Detected",
  "body": "Person detected at front door",
  "image": "https://example.com/snapshot.jpg",
  "video_url": "https://example.com/event.mp4",
  "sound_id": "alert",
  "require_interaction": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notification sent",
  "notification_id": "notif-abc123"
}
```

---

## Push Notification APIs

### 1. Subscribe to Push Notifications
**Endpoint:** `POST /api/push/subscribe`

**Description:** Register a push subscription for web push notifications.

**Request Body:**
```json
{
  "user_id": "user@example.com",
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "BKj...base64...",
    "auth": "Ab9...base64..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Subscribed to push notifications",
  "subscription_id": "sub-abc123"
}
```

---

### 2. Unsubscribe from Push
**Endpoint:** `DELETE /api/push/unsubscribe/{user_id}?endpoint=https://fcm.googleapis.com/...`

**Description:** Remove push subscription(s).

**Path Parameters:**
- `user_id` (string, required): User ID

**Query Parameters:**
- `endpoint` (string, optional): Specific endpoint to remove (if omitted, removes all user subscriptions)

**Response:**
```json
{
  "success": true,
  "message": "Unsubscribed 1 subscription(s)",
  "deleted_count": 1
}
```

---

### 3. Send Push Notification
**Endpoint:** `POST /api/push/send`

**Description:** Send a push notification to all user's subscribed devices.

**Request Body:**
```json
{
  "user_id": "user@example.com",
  "device_id": "camera-1",
  "title": "Motion Alert",
  "body": "Person detected at front door",
  "icon": "/icon-192.png",
  "badge": "/badge.png",
  "image": "https://example.com/snapshot.jpg",
  "video_url": "https://example.com/event.mp4",
  "sound_id": "alert",
  "sound_url": "https://example.com/sounds/alert.mp3",
  "data": {
    "device_id": "camera-1",
    "camera_id": "camera-1",
    "custom_field": "value"
  },
  "actions": [
    {
      "action": "view",
      "title": "View"
    }
  ],
  "require_interaction": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sent 2 notifications, 0 failed",
  "sent_count": 2,
  "failed_count": 0,
  "total_subscriptions": 2
}
```

---

### 4. Get User Push Subscriptions
**Endpoint:** `GET /api/push/subscriptions/{user_id}`

**Description:** Get all push subscriptions for a user.

**Path Parameters:**
- `user_id` (string, required): User ID

**Response:**
```json
[
  {
    "id": "sub-1",
    "user_id": "user@example.com",
    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
    "keys": {
      "p256dh": "BKj...",
      "auth": "Ab9..."
    },
    "created_at": "2025-01-09T10:48:38.123Z"
  }
]
```

---

## File Upload APIs

### 1. Upload File
**Endpoint:** `POST /api/files/upload?user_id=user@example.com`

**Description:** Upload a file (supports up to 100MB).

**Query Parameters:**
- `user_id` (string, required): User ID

**Request:** Multipart form data
- `file` (file, required): File to upload
- `device_id` (string, optional): Associated device ID
- `message_id` (string, optional): Associated message ID

**Response:**
```json
{
  "success": true,
  "file_id": "file-abc123",
  "filename": "document.pdf",
  "file_type": "application/pdf",
  "file_size": 524288,
  "url": "/api/files/file-abc123"
}
```

---

### 2. Get File
**Endpoint:** `GET /api/files/{file_id}`

**Description:** Download/view an uploaded file.

**Path Parameters:**
- `file_id` (string, required): File ID

**Response:** File content with appropriate Content-Type header

---

### 3. Get User Files
**Endpoint:** `GET /api/files/user/{user_id}`

**Description:** Get all files uploaded by a user.

**Path Parameters:**
- `user_id` (string, required): User ID

**Response:**
```json
[
  {
    "id": "file-1",
    "filename": "stored-name.pdf",
    "original_filename": "document.pdf",
    "file_path": "/app/backend/uploads/user@example.com/stored-name.pdf",
    "file_type": "application/pdf",
    "file_size": 524288,
    "user_id": "user@example.com",
    "device_id": "camera-1",
    "uploaded_at": "2025-01-09T10:48:38.123Z"
  }
]
```

---

### 4. Delete File
**Endpoint:** `DELETE /api/files/{file_id}`

**Description:** Delete an uploaded file.

**Path Parameters:**
- `file_id` (string, required): File ID

**Response:**
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

---

## AI Settings APIs

### 1. Get Chat Settings
**Endpoint:** `GET /api/chat/settings/{user_id}/{device_id}`

**Description:** Get AI chat settings (role, personality) for a device.

**Path Parameters:**
- `user_id` (string, required): User ID
- `device_id` (string, required): Device ID

**Response:**
```json
{
  "id": "settings-1",
  "user_id": "user@example.com",
  "device_id": "camera-1",
  "role_name": "Security Guard AI",
  "system_message": "You are a security expert monitoring a camera...",
  "instructions": "Watch for suspicious activity",
  "model": "gpt-5-nano",
  "created_at": "2025-01-09T10:48:38.123Z",
  "updated_at": "2025-01-09T10:48:38.123Z"
}
```

---

### 2. Create Chat Settings
**Endpoint:** `POST /api/chat/settings/{user_id}/{device_id}`

**Description:** Create custom AI settings for a device.

**Path Parameters:**
- `user_id` (string, required): User ID
- `device_id` (string, required): Device ID

**Request Body:**
```json
{
  "role_name": "Security Guard AI",
  "system_message": "You are a security expert...",
  "instructions": "Watch for suspicious activity",
  "model": "gpt-5-nano"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Chat settings created",
  "settings_id": "settings-abc123"
}
```

---

### 3. Update Chat Settings
**Endpoint:** `PUT /api/chat/settings/{user_id}/{device_id}`

**Description:** Update AI settings for a device.

**Path Parameters:**
- `user_id` (string, required): User ID
- `device_id` (string, required): Device ID

**Request Body:**
```json
{
  "role_name": "Updated Role",
  "system_message": "Updated system message",
  "instructions": "Updated instructions",
  "model": "gpt-4o"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Chat settings updated"
}
```

---

### 4. Delete Chat Settings
**Endpoint:** `DELETE /api/chat/settings/{user_id}/{device_id}`

**Description:** Delete custom AI settings (reverts to default).

**Path Parameters:**
- `user_id` (string, required): User ID
- `device_id` (string, required): Device ID

**Response:**
```json
{
  "success": true,
  "message": "Chat settings deleted"
}
```

---

### 5. Parse Role Change Command
**Endpoint:** `POST /api/chat/parse-role-change`

**Description:** Parse natural language command to change AI role (e.g., "act as a detective").

**Request Body:**
```json
{
  "user_id": "user@example.com",
  "device_id": "camera-1",
  "message": "act as a detective looking for clues"
}
```

**Response:**
```json
{
  "success": true,
  "detected": "act_as",
  "new_role": "Detective",
  "new_instructions": "Looking for clues in the scene",
  "settings_updated": true,
  "confirmation_message": "✅ Role changed! I'm now acting as: Detective - Looking for clues in the scene"
}
```

---

## Camera Prompt APIs

### 1. Get Camera Prompt
**Endpoint:** `GET /api/camera/prompt/{user_id}/{device_id}`

**Description:** Get monitoring instructions for a camera.

**Path Parameters:**
- `user_id` (string, required): User ID
- `device_id` (string, required): Device ID

**Response:**
```json
{
  "id": "prompt-1",
  "user_id": "user@example.com",
  "device_id": "camera-1",
  "prompt_text": "Watch for people entering restricted areas",
  "instructions": "people entering restricted areas",
  "created_at": "2025-01-09T10:48:38.123Z",
  "updated_at": "2025-01-09T10:48:38.123Z"
}
```

---

### 2. Update Camera Prompt
**Endpoint:** `PUT /api/camera/prompt/{user_id}/{device_id}`

**Description:** Update monitoring instructions for a camera.

**Path Parameters:**
- `user_id` (string, required): User ID
- `device_id` (string, required): Device ID

**Request Body:**
```json
{
  "instructions": "watch for packages left unattended"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Camera prompt updated",
  "prompt": {
    "id": "prompt-1",
    "instructions": "watch for packages left unattended",
    ...
  }
}
```

---

### 3. Parse Camera Prompt Command
**Endpoint:** `POST /api/camera/prompt/parse`

**Description:** Parse natural language command to update monitoring (e.g., "watch for X").

**Request Body:**
```json
{
  "user_id": "user@example.com",
  "device_id": "camera-1",
  "message": "watch for vehicles parking after hours"
}
```

**Response:**
```json
{
  "success": true,
  "detected": true,
  "instructions": "vehicles parking after hours",
  "settings_updated": true,
  "confirmation_message": "✅ Camera monitoring updated. I will now watch for: vehicles parking after hours"
}
```

---

### 4. Fix from Feedback
**Endpoint:** `POST /api/camera/prompt/fix-from-feedback`

**Description:** Update camera monitoring based on corrective feedback.

**Request Body:**
```json
{
  "user_id": "user@example.com",
  "device_id": "camera-1",
  "message": "You missed the delivery truck. Watch for all large vehicles.",
  "referenced_messages": ["msg-123"]
}
```

**Response:**
```json
{
  "success": true,
  "feedback_applied": true,
  "updated_instructions": "all large vehicles including delivery trucks",
  "confirmation_message": "✅ Got it! I've updated my monitoring to better catch: all large vehicles including delivery trucks"
}
```

---

## Mission APIs

### 1. Get User Missions
**Endpoint:** `GET /api/missions/{user_id}`

**Description:** Get all missions for a user.

**Path Parameters:**
- `user_id` (string, required): User ID

**Response:**
```json
[
  {
    "id": "mission-1",
    "user_id": "user@example.com",
    "name": "Building Security",
    "description": "Monitor all building entrances",
    "camera_ids": ["camera-1", "camera-2", "camera-3"],
    "created_at": "2025-01-09T10:48:38.123Z",
    "updated_at": "2025-01-09T10:48:38.123Z"
  }
]
```

---

### 2. Create Mission
**Endpoint:** `POST /api/missions?user_id=user@example.com`

**Description:** Create a new mission.

**Query Parameters:**
- `user_id` (string, required): User ID

**Request Body:**
```json
{
  "name": "Parking Lot Security",
  "description": "Monitor parking lot entrances and exits",
  "camera_ids": ["camera-4", "camera-5"]
}
```

**Response:**
```json
{
  "success": true,
  "mission_id": "mission-abc123",
  "mission": {
    "id": "mission-abc123",
    "name": "Parking Lot Security",
    ...
  }
}
```

---

### 3. Assign Cameras to Mission
**Endpoint:** `POST /api/missions/assign-cameras`

**Description:** Assign or update cameras for a mission.

**Request Body:**
```json
{
  "user_id": "user@example.com",
  "mission_id": "mission-1",
  "camera_ids": ["camera-1", "camera-2", "camera-3"]
}
```

**Response:**
```json
{
  "success": true,
  "mission_id": "mission-1",
  "camera_ids": ["camera-1", "camera-2", "camera-3"]
}
```

---

## Sounds APIs

### 1. Get Sound by ID
**Endpoint:** `GET /api/sounds/{sound_id}`

**Description:** Get notification sound file.

**Path Parameters:**
- `sound_id` (string, required): Sound ID (e.g., "alert", "significant", "routine")

**Response:** Audio file (MP3) with appropriate Content-Type header

**Supported Sound IDs:**
- `alert` - Alert sound
- `significant` - Significant event sound
- `routine` - Routine notification sound
- Custom sounds if configured

---

## WebSocket API

### WebSocket Connection
**Endpoint:** `ws://your-domain.com/ws/{user_id}` or `wss://your-domain.com/ws/{user_id}`

**Description:** Real-time bidirectional communication (Note: Frontend currently uses Push + REST instead).

**Path Parameters:**
- `user_id` (string, required): User ID

**Message Types:**

**1. Ping/Pong (Keep-Alive):**
```json
// Client sends:
{ "type": "ping" }

// Server responds:
{ "type": "pong" }
```

**2. Chat Message:**
```json
// Client sends:
{
  "type": "chat",
  "device_id": "camera-1",
  "message": "Hello device"
}

// Server responds:
{
  "type": "message_sent",
  "message_id": "msg-123",
  "device_id": "camera-1"
}

// Then AI response:
{
  "type": "ai_response",
  "device_id": "camera-1",
  "message": "Hello! How can I help?",
  "message_id": "msg-456",
  "timestamp": "2025-01-09T10:48:38.123Z"
}
```

**3. Notification:**
```json
// Server sends:
{
  "type": "notification",
  "device_id": "camera-1",
  "title": "Motion Detected",
  "body": "Person at door",
  "media_url": "https://example.com/snapshot.jpg",
  "timestamp": "2025-01-09T10:48:38.123Z"
}
```

---

## Status & Utilities

### 1. Health Check
**Endpoint:** `GET /api/status`

**Description:** Check if API is running.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-01-09T10:48:38.123Z"
}
```

---

### 2. Status Check (with client tracking)
**Endpoint:** `POST /api/status/check`

**Description:** Record a client status check.

**Request Body:**
```json
{
  "client_name": "frontend-web-app"
}
```

**Response:**
```json
{
  "success": true,
  "client_name": "frontend-web-app",
  "timestamp": "2025-01-09T10:48:38.123Z"
}
```

---

## Data Models Reference

### Device Types
- `camera` - Security camera
- `sensor` - Environmental sensor
- `doorbell` - Smart doorbell
- `default` - Generic device

### Message Senders
- `user` - Message from user
- `ai` - AI-generated response
- `system` - System message/notification
- `device` - Message from physical device

### Notification Types
- `message` - Chat message
- `alert` - Alert notification
- `media` - Media notification
- `push` - Push notification

### AI Models
- `gpt-5-nano` - Default text model
- `gpt-4o` - Vision model (auto-selected for images)

### Sound IDs
- `alert` - Alert sound
- `significant` - Significant event
- `routine` - Routine notification
- Custom sound IDs from device settings

---

## Error Responses

All APIs follow consistent error response format:

```json
{
  "success": false,
  "error": "Error message description",
  "detail": "Additional error details (optional)"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid/missing token)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

---

## Rate Limits & Quotas

- **File Upload Limit:** 100MB per file
- **Push Subscriptions:** Unlimited per user
- **WebSocket Connections:** 1 per user
- **Chat Message Size:** ~8000 characters for file content context
- **Media URLs per message:** Unlimited (but consider performance)

---

## Best Practices

1. **Authentication:**
   - Always include JWT token in requests after login
   - Store token securely in localStorage/sessionStorage
   - Refresh token before expiration

2. **File Uploads:**
   - Use chunked uploads for large files
   - Check file size before upload
   - Handle upload progress for better UX

3. **Push Notifications:**
   - Request permission before subscribing
   - Handle subscription failures gracefully
   - Clean up subscriptions on logout

4. **Chat Messages:**
   - Include referenced messages for context
   - Use media_urls for external media
   - Batch file uploads before sending

5. **WebSocket (if used):**
   - Implement reconnection logic
   - Send ping messages to keep connection alive
   - Handle disconnect gracefully

6. **Error Handling:**
   - Always check `success` field in responses
   - Display user-friendly error messages
   - Log errors for debugging

---

## Quick Start Examples

### Register and Login
```bash
# Register
curl -X POST https://your-domain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure_pass"}'

# Login
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure_pass"}'
```

### Create Device and Send Message
```bash
# Create device
curl -X POST https://your-domain.com/api/devices \
  -H "Content-Type: application/json" \
  -d '{"name":"Camera 1","type":"camera","user_id":"user@example.com"}'

# Send chat message
curl -X POST 'https://your-domain.com/api/chat/send?user_id=user@example.com' \
  -H "Content-Type: application/json" \
  -d '{"device_id":"device-id","message":"Hello camera"}'
```

### Subscribe to Push Notifications
```javascript
// Frontend JavaScript
const registration = await navigator.serviceWorker.ready;
const subscription = await registration.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
});

const response = await fetch('/api/push/subscribe', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user@example.com',
    endpoint: subscription.endpoint,
    keys: {
      p256dh: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('p256dh')))),
      auth: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('auth'))))
    }
  })
});
```

---

## Support & Documentation

For additional help:
- Check `/app/API_REFERENCE.md` for more examples
- Review `/app/README.md` for setup instructions
- See `/app/SETUP.md` for deployment guide

---

**Version:** 1.0  
**Last Updated:** January 9, 2025  
**Base URL:** `https://your-domain.com/api`
