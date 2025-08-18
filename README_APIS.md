# Device Chat Platform API Reference

Base URL
- All backend routes are prefixed with /api
- Frontend must use REACT_APP_BACKEND_URL to call backend

Auth/IDs
- user_id is passed as a path or query parameter (no auth layer in this MVP)
- device_id identifies a device belonging to a user

WebSocket
- GET /api/ws/{user_id}
  - Real-time channel for notifications and AI responses

Devices
- POST /api/devices
  - Create a device
  - Body: { name, type, user_id, location?, description?, settings? }
  - Returns: Device

- POST /api/devices/create-with-id
  - Create device with custom ID
  - Query: device_id, name, type, user_id, location?, description?, settings?, status?
  - Returns: { success, message, device }

- PUT /api/devices/{old_device_id}/update-id
  - Migrate device to new ID (optionally preserve related data)
  - Query: new_device_id, preserve_data=true|false
  - Returns: migration summary

- GET /api/devices/{user_id}
  - List devices for user

- PUT /api/devices/{device_id}/status
  - Update device status
  - Query: status

- PUT /api/devices/{device_id}
  - Update device information
  - Body: DeviceUpdate

- PUT /api/devices/bulk-update
  - Bulk update devices
  - Body: { device_updates: [ { device_id, updates: {...} } ] }

- DELETE /api/devices/{device_id}
  - Delete one device

- DELETE /api/devices/user/{user_id}/delete-all
  - Danger: delete devices and optionally notifications/messages/subscriptions
  - Query: delete_notifications=true|false, delete_chat_messages=true|false, delete_push_subscriptions=true|false, confirm_deletion=true

- DELETE /api/devices/user/{user_id}/delete-all-safe
  - Safe delete only devices

Push Notifications
- POST /api/push/subscribe
  - Body: { user_id, endpoint, keys: { p256dh, auth } }

- DELETE /api/push/unsubscribe/{user_id}
  - Query: endpoint? (optional to remove just one)

- POST /api/push/send
  - Body: { user_id, device_id, title, body, icon?, badge?, image?, data?, actions?, require_interaction? }

- GET /api/push/subscriptions/{user_id}
  - List push subscriptions for a user

Notifications (history)
- GET /api/notifications/{user_id}
  - Query: limit=50, unread_only=false

- GET /api/notifications/{user_id}/device/{device_id}
  - Query: limit=50, unread_only=false

- PUT /api/notifications/{notification_id}/read
  - Mark as read

- POST /api/simulate/device-notification
  - Query: user_id, device_id, message, media_url?, notification_type?=message

Chat
- POST /api/chat/send?user_id=...
  - Body: {
      device_id, message, sender='user', file_ids?, media_url?, media_urls?, referenced_messages?
    }
  - Text-only and vision supported. If images are present (file_ids of images or media_urls), vision model is used.
  - Returns: { success, message_id, ai_response: { message, message_id } } or confirmation when settings changed
  - Side effects:
    - Natural camera prompt updates in-text are detected; confirmation stored as a system message and AI call skipped
    - Role/instruction changes are detected via parse-command; confirmation stored and AI call skipped
    - Push notification sent when images are involved and AI response is significant

- GET /api/chat/{user_id}/{device_id}
  - Query: limit=50
  - Returns last messages in chronological order

- GET /api/chat/{user_id}/{device_id}/history
  - Returns JSON chat history for the device

- DELETE /api/chat/{user_id}/{device_id}/history
  - Clear chat history

Direct Image Analysis
- POST /api/chat/image-direct?user_id=...
  - Body: { device_id, image_data?, image_url?, media_urls?, question? }
  - At least one of image_data, image_url, media_urls required
  - Returns: { success, displayed_in_chat, ai_response, message_id, analysis_type }
  - Side effects:
    - If displayed_in_chat=true, the user image entry and AI analysis are stored in chat
    - Push notification is sent for significant analyses

Camera Prompt Management
- GET /api/camera/prompt/{user_id}/{device_id}
- PUT /api/camera/prompt/{user_id}/{device_id}
  - Body: { instructions }

- POST /api/camera/prompt/parse-command
  - Body: { user_id, device_id, message }
  - Parses natural language like: "monitor for ...", "look for ..." and updates prompt
  - Stores a system confirmation message

- POST /api/camera/prompt/fix-from-feedback
  - Body: { user_id, device_id, message, referenced_messages? }
  - When user says an analysis is wrong and explains, generates better instructions and updates prompt
  - Stores a system confirmation message

Chat Settings (AI Role/Instructions)
- GET /api/chat/settings/{user_id}/{device_id}
- PUT /api/chat/settings/{user_id}/{device_id}
  - Body: { role_name?, system_message?, instructions?, model? }

- POST /api/chat/settings/parse-command
  - Body: { user_id, device_id, message }
  - Natural language changes like: "act as ...", "change your instructions to ...", "reset to default"

Files
- POST /api/files/upload (multipart/form-data)
  - Fields: file, user_id, device_id?, message_id?
  - Returns: { success, file_id, url, ... }

- GET /api/files/{file_id}
  - Serves uploaded file

- GET /api/files/user/{user_id}
  - Lists user files

- DELETE /api/files/{file_id}
  - Deletes file and DB record

Root/Status
- GET /api/
- POST /api/status
- GET /api/status

Important behaviors & rules
- All backend endpoints must be called via {REACT_APP_BACKEND_URL}/api/... from the frontend
- MongoDB URL is taken from backend/.env MONGO_URL
- Web Push requires VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_EMAIL set in backend/.env
- Vision model uses OpenAI via emergentintegrations with base64 image conversion
- Object IDs are UUIDs for JSON safety