# New APIs Documentation - Device Chat PWA

Two powerful new APIs have been added to the Device Chat PWA:

## 🔔 Push Notification API

Send real-time push notifications to users' mobile devices even when the app is closed.

### Features
- Web Push Protocol support with VAPID keys
- Rich notifications with images, actions, and custom data
- Automatic subscription management
- Handles invalid subscriptions cleanup
- Works with PWA service worker

### Endpoints

#### 1. Subscribe to Push Notifications
```http
POST /api/push/subscribe
Content-Type: application/json

{
  "user_id": "user123",
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "BDgJHFHHDHg789H...",
    "auth": "auth123key..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Subscribed to push notifications",
  "subscription_id": "uuid-subscription-id"
}
```

#### 2. Send Push Notification ⭐ **Main API**
```http
POST /api/push/send
Content-Type: application/json

{
  "user_id": "user123",
  "title": "Device Alert",
  "body": "Motion detected at front door",
  "icon": "/manifest-icon-192.png",
  "badge": "/manifest-icon-192.png", 
  "image": "https://example.com/camera-image.jpg",
  "data": {
    "device_id": "camera-01",
    "timestamp": "2025-01-15T10:30:00Z",
    "priority": "high"
  },
  "actions": [
    {"action": "view", "title": "View Camera"},
    {"action": "dismiss", "title": "Dismiss"}
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

#### 3. Get User Push Subscriptions
```http
GET /api/push/subscriptions/{user_id}
```

#### 4. Unsubscribe from Push Notifications
```http
DELETE /api/push/unsubscribe/{user_id}?endpoint=optional
```

### Usage Examples

#### Python Example:
```python
import requests

# Send push notification
response = requests.post('https://your-api.com/api/push/send', json={
    "user_id": "user123",
    "title": "Security Alert",
    "body": "Motion detected in living room",
    "image": "https://camera.example.com/snapshot.jpg",
    "data": {"device_id": "camera-living-room"}
})

print(response.json())
```

#### JavaScript Example:
```javascript
// Send push notification
const response = await fetch('/api/push/send', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user123',
    title: 'Temperature Alert',
    body: 'Temperature is above 85°F',
    data: { device_id: 'temp-sensor-01' }
  })
});

const result = await response.json();
console.log(result);
```

#### cURL Example:
```bash
curl -X POST "https://your-api.com/api/push/send" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "title": "Door Alert",
    "body": "Front door opened",
    "data": {"device_id": "door-sensor-01"}
  }'
```

---

## 📱 Device Update APIs

Efficiently update single or multiple devices with new information.

### Enhanced Device Model
Devices now support additional fields:
- `location`: Physical location of device
- `description`: Device description
- `settings`: Custom device settings (JSON object)
- `updated_at`: Last update timestamp

### Endpoints

#### 1. Update Single Device
```http
PUT /api/devices/{device_id}
Content-Type: application/json

{
  "name": "Living Room Camera",
  "status": "online",
  "location": "Living Room",
  "description": "4K security camera with night vision",
  "settings": {
    "resolution": "4K",
    "night_vision": true,
    "motion_detection": true,
    "recording_enabled": false
  }
}
```

**Response:**
```json
{
  "id": "device-uuid",
  "name": "Living Room Camera",
  "type": "camera",
  "user_id": "user123",
  "status": "online",
  "location": "Living Room",
  "description": "4K security camera with night vision",
  "settings": {
    "resolution": "4K",
    "night_vision": true,
    "motion_detection": true,
    "recording_enabled": false
  },
  "last_seen": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-10T09:00:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

#### 2. Bulk Update Devices ⭐ **Main API**
```http
PUT /api/devices/bulk-update
Content-Type: application/json

{
  "device_updates": [
    {
      "device_id": "camera-01",
      "updates": {
        "status": "online",
        "settings": {"motion_detection": true}
      }
    },
    {
      "device_id": "sensor-01", 
      "updates": {
        "name": "Kitchen Temperature Sensor",
        "location": "Kitchen",
        "description": "WiFi temperature and humidity sensor"
      }
    },
    {
      "device_id": "door-01",
      "updates": {
        "status": "offline",
        "settings": {"battery_level": 25}
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
  "failed_updates": [
    {
      "error": "Device not found",
      "device_id": "door-01"
    }
  ],
  "total_attempted": 3
}
```

#### 3. Delete Device
```http
DELETE /api/devices/{device_id}
```

### Usage Examples

#### Python Example:
```python
import requests

# Bulk update devices
response = requests.put('https://your-api.com/api/devices/bulk-update', json={
    "device_updates": [
        {
            "device_id": "camera-living-room",
            "updates": {
                "status": "online",
                "settings": {"recording": True, "resolution": "1080p"}
            }
        },
        {
            "device_id": "sensor-kitchen",
            "updates": {
                "location": "Kitchen",
                "description": "Smart temperature sensor"
            }
        }
    ]
})

result = response.json()
print(f"Updated {result['updated_count']} devices")
```

#### JavaScript Example:
```javascript
// Update single device
const response = await fetch('/api/devices/camera-01', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Updated Camera Name',
    location: 'Front Door',
    settings: { night_vision: true }
  })
});

const updatedDevice = await response.json();
console.log(updatedDevice);
```

#### cURL Example:
```bash
# Bulk update devices
curl -X PUT "https://your-api.com/api/devices/bulk-update" \
  -H "Content-Type: application/json" \
  -d '{
    "device_updates": [
      {
        "device_id": "sensor-01",
        "updates": {
          "status": "online",
          "location": "Bedroom"
        }
      }
    ]
  }'
```

---

## 🔧 Integration Examples

### Home Automation System Integration
```python
import requests
import json

class DeviceChatAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
    
    def send_device_alert(self, user_id, device_name, message, image_url=None):
        """Send push notification for device alert"""
        payload = {
            "user_id": user_id,
            "title": f"{device_name} Alert",
            "body": message,
            "image": image_url,
            "data": {"device_name": device_name}
        }
        
        response = requests.post(f"{self.api_url}/push/send", json=payload)
        return response.json()
    
    def update_device_status(self, device_id, status, additional_data=None):
        """Update device status and settings"""
        updates = {"status": status}
        if additional_data:
            updates.update(additional_data)
            
        payload = {
            "device_updates": [{
                "device_id": device_id,
                "updates": updates
            }]
        }
        
        response = requests.put(f"{self.api_url}/devices/bulk-update", json=payload)
        return response.json()

# Usage
api = DeviceChatAPI("https://your-api.com")

# Send motion detection alert
api.send_device_alert(
    user_id="homeowner123",
    device_name="Front Door Camera",
    message="Motion detected at 2:30 PM",
    image_url="https://camera.example.com/snapshot.jpg"
)

# Update multiple device statuses
api.update_device_status("camera-01", "online", {
    "settings": {"recording": True},
    "location": "Front Door"
})
```

### IoT Device Integration
```javascript
// IoT device sending data and triggering notifications
class IoTDevice {
    constructor(deviceId, userId, apiUrl) {
        this.deviceId = deviceId;
        this.userId = userId;
        this.apiUrl = apiUrl;
    }
    
    async sendAlert(title, message, data = {}) {
        const response = await fetch(`${this.apiUrl}/push/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: this.userId,
                title: title,
                body: message,
                data: { device_id: this.deviceId, ...data }
            })
        });
        
        return response.json();
    }
    
    async updateStatus(status, settings = {}) {
        const response = await fetch(`${this.apiUrl}/devices/${this.deviceId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                status: status,
                settings: settings,
                last_seen: new Date().toISOString()
            })
        });
        
        return response.json();
    }
}

// Usage
const sensor = new IoTDevice('temp-sensor-01', 'user123', 'https://api.example.com/api');

// Temperature alert
sensor.sendAlert('Temperature Alert', 'Temperature exceeded 85°F', {
    temperature: 87,
    humidity: 65
});

// Update sensor status
sensor.updateStatus('online', {
    temperature: 72,
    humidity: 55,
    battery_level: 85
});
```

---

## 🚀 Deployment Notes

### Environment Variables Required:
```env
# Backend .env file
VAPID_PRIVATE_KEY="your-vapid-private-key"
VAPID_PUBLIC_KEY="your-vapid-public-key"  
VAPID_EMAIL="mailto:admin@yourapp.com"
```

### Generate VAPID Keys:
```bash
# Install web-push CLI
npm install -g web-push

# Generate VAPID keys
web-push generate-vapid-keys
```

### Frontend Configuration:
- Update VAPID_PUBLIC_KEY in App.js
- Ensure service worker is properly registered
- Test push notification permissions

---

## 📊 API Testing

Both APIs have been thoroughly tested:

### Push Notification API:
✅ Subscription management  
✅ Send notifications with rich content  
✅ Handle invalid subscriptions  
✅ Unsubscribe functionality  

### Device Update API:
✅ Single device updates  
✅ Bulk device updates  
✅ Error handling for missing devices  
✅ Device deletion  

### Live Testing:
- **Backend URL**: http://localhost:8001
- **Test Script**: `/app/backend/test_new_apis.py`
- **All tests passing**: ✅

---

## 🎯 Use Cases

### Push Notifications:
- **Security alerts** with camera snapshots
- **Device status changes** (online/offline)
- **Sensor threshold alerts** (temperature, motion, etc.)
- **System maintenance notifications**
- **Battery low warnings**

### Device Updates:
- **IoT device provisioning** - bulk setup of new devices
- **Status synchronization** - update multiple device states
- **Configuration management** - push settings to devices
- **Location tracking** - update device physical locations
- **Metadata management** - descriptions, tags, categories

---

**🎉 Ready for Production Use!**

Both APIs are fully functional, tested, and ready for integration with your IoT systems and mobile applications.