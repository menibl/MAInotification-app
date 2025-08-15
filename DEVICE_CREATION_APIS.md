# Device Creation & ID Management APIs

Two powerful new APIs for creating devices and managing their IDs with full data preservation.

---

## 🏗️ **API 1: Create Device with Custom ID**

Create a device with your own custom ID instead of auto-generated UUID.

### **Endpoint:**
```http
POST /api/devices/create-with-id
```

### **Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `device_id` | string | ✅ Yes | Your custom device ID |
| `name` | string | ✅ Yes | Device name |
| `type` | string | ✅ Yes | Device type (camera, sensor, etc.) |
| `user_id` | string | ✅ Yes | User ID who owns the device |
| `location` | string | ❌ No | Physical location |
| `description` | string | ❌ No | Device description |
| `settings` | object | ❌ No | Custom device settings (JSON) |
| `status` | string | ❌ No | Device status (default: "online") |

### **Examples:**

#### **cURL:**
```bash
curl -X POST "http://localhost:8001/api/devices/create-with-id" \
  -d "device_id=my-camera-001" \
  -d "name=Living Room Camera" \
  -d "type=camera" \
  -d "user_id=user123" \
  -d "location=Living Room" \
  -d "description=4K Security Camera with AI" \
  -d "status=online"
```

#### **JavaScript:**
```javascript
const response = await fetch('/api/devices/create-with-id', {
  method: 'POST',
  body: new URLSearchParams({
    device_id: 'my-camera-001',
    name: 'Living Room Camera',
    type: 'camera',
    user_id: 'user123',
    location: 'Living Room',
    description: '4K Security Camera with AI',
    status: 'online'
  })
});

const result = await response.json();
console.log(result);
```

#### **Python:**
```python
import requests

response = requests.post(
    'http://localhost:8001/api/devices/create-with-id',
    params={
        'device_id': 'my-camera-001',
        'name': 'Living Room Camera',
        'type': 'camera',
        'user_id': 'user123',
        'location': 'Living Room',
        'description': '4K Security Camera with AI',
        'status': 'online'
    }
)

result = response.json()
print(result)
```

### **Response:**
```json
{
  "success": true,
  "message": "Device created with ID: my-camera-001",
  "device": {
    "id": "my-camera-001",
    "name": "Living Room Camera",
    "type": "camera",
    "user_id": "user123",
    "status": "online",
    "location": "Living Room",
    "description": "4K Security Camera with AI",
    "settings": {},
    "last_seen": "2025-08-15T14:27:12.159000",
    "created_at": "2025-08-15T14:27:12.159000",
    "updated_at": "2025-08-15T14:27:12.159000"
  }
}
```

### **Error Response:**
```json
{
  "detail": "Device with ID 'my-camera-001' already exists"
}
```

---

## 🔄 **API 2: Update Device ID**

Change a device's ID while preserving all associated data (notifications, chat messages).

### **Endpoint:**
```http
PUT /api/devices/{old_device_id}/update-id
```

### **Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `old_device_id` | string | ✅ Yes | Current device ID (in URL path) |
| `new_device_id` | string | ✅ Yes | New device ID |
| `preserve_data` | boolean | ❌ No | Preserve notifications & messages (default: true) |

### **Examples:**

#### **cURL:**
```bash
curl -X PUT "http://localhost:8001/api/devices/old-camera-123/update-id?new_device_id=new-camera-456&preserve_data=true"
```

#### **JavaScript:**
```javascript
const response = await fetch('/api/devices/old-camera-123/update-id', {
  method: 'PUT',
  body: new URLSearchParams({
    new_device_id: 'new-camera-456',
    preserve_data: true
  })
});

const result = await response.json();
console.log(result);
```

#### **Python:**
```python
import requests

response = requests.put(
    'http://localhost:8001/api/devices/old-camera-123/update-id',
    params={
        'new_device_id': 'new-camera-456',
        'preserve_data': True
    }
)

result = response.json()
print(result)
```

### **Response:**
```json
{
  "success": true,
  "message": "Device ID updated from 'old-camera-123' to 'new-camera-456'",
  "old_device_id": "old-camera-123",
  "new_device_id": "new-camera-456",
  "data_preservation": {
    "notifications_updated": 15,
    "messages_updated": 8
  },
  "device": {
    "id": "new-camera-456",
    "name": "Living Room Camera",
    "type": "camera",
    "user_id": "user123",
    "status": "online",
    "location": "Living Room",
    "description": "4K Security Camera with AI",
    "settings": {},
    "last_seen": "2025-08-15T14:27:12.159000",
    "created_at": "2025-08-15T14:27:12.159000",
    "updated_at": "2025-08-15T14:35:45.891698"
  }
}
```

### **What Gets Updated:**
When `preserve_data=true` (default):
- ✅ **Device record** - New ID with all existing data
- ✅ **Notifications** - All notifications now reference new device ID  
- ✅ **Chat messages** - All chat messages now reference new device ID
- ✅ **Push subscriptions** - Continue to work with new device ID

---

## 🎯 **Use Cases**

### **Custom Device IDs:**
```bash
# Create devices with your own naming convention
POST /api/devices/create-with-id
device_id=CAM_LIVING_ROOM_001
device_id=SENSOR_KITCHEN_TEMP_01
device_id=DOORBELL_FRONT_MAIN
```

### **ID Migration:**
```bash
# Update devices from old system to new naming
PUT /api/devices/legacy-device-123/update-id?new_device_id=NEW_CAM_001

# Batch update multiple devices
PUT /api/devices/old-sensor-1/update-id?new_device_id=SENSOR_001
PUT /api/devices/old-sensor-2/update-id?new_device_id=SENSOR_002
```

### **System Integration:**
```python
# Create device with your system's ID format
def create_iot_device(hardware_id, device_info):
    response = requests.post('/api/devices/create-with-id', params={
        'device_id': f"IOT_{hardware_id}",
        'name': device_info['name'],
        'type': device_info['type'],
        'user_id': device_info['owner_id'],
        'location': device_info.get('location'),
        'settings': device_info.get('config', {})
    })
    return response.json()

# Update device ID when hardware changes
def migrate_device_id(old_hardware_id, new_hardware_id):
    old_id = f"IOT_{old_hardware_id}"
    new_id = f"IOT_{new_hardware_id}"
    
    response = requests.put(f'/api/devices/{old_id}/update-id', params={
        'new_device_id': new_id,
        'preserve_data': True
    })
    return response.json()
```

---

## ⚡ **Advanced Features**

### **Custom Settings Support:**
```bash
# Create device with complex settings
curl -X POST "/api/devices/create-with-id" \
  -d "device_id=advanced-camera-001" \
  -d "name=AI Security Camera" \
  -d "type=camera" \
  -d "user_id=user123" \
  -d "settings={'resolution': '4K', 'ai_detection': ['person', 'vehicle'], 'zones': [{'name': 'entrance', 'active': true}]}"
```

### **Batch Operations:**
```python
# Create multiple devices with custom IDs
devices_to_create = [
    {'device_id': 'CAM_001', 'name': 'Front Door Camera', 'type': 'camera'},
    {'device_id': 'CAM_002', 'name': 'Back Door Camera', 'type': 'camera'},
    {'device_id': 'SENS_001', 'name': 'Living Room Sensor', 'type': 'sensor'}
]

for device in devices_to_create:
    device['user_id'] = 'user123'
    response = requests.post('/api/devices/create-with-id', params=device)
    print(f"Created: {device['name']} - {response.json().get('success')}")
```

### **Data Migration:**
```python
# Migrate all devices from old ID format to new
def migrate_all_devices(user_id, old_prefix, new_prefix):
    # Get all user devices
    devices = requests.get(f'/api/devices/{user_id}').json()
    
    for device in devices:
        if device['id'].startswith(old_prefix):
            new_id = device['id'].replace(old_prefix, new_prefix)
            
            response = requests.put(
                f"/api/devices/{device['id']}/update-id",
                params={'new_device_id': new_id, 'preserve_data': True}
            )
            
            print(f"Migrated: {device['id']} → {new_id}")
```

---

## 🚨 **Error Handling**

### **Common Errors:**

#### **Device ID Already Exists:**
```json
{
  "detail": "Device with ID 'my-camera-001' already exists"
}
```

#### **Device Not Found:**
```json
{
  "detail": "Device with ID 'non-existent-device' not found"  
}
```

#### **Invalid Parameters:**
```json
{
  "detail": [
    {
      "loc": ["query", "device_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 📊 **API Testing**

### **Test Script Available:**
```bash
# Run comprehensive API tests
python /app/test_device_creation_apis.py
```

### **Manual Testing:**
```bash
# 1. Create device with custom ID
curl -X POST "http://localhost:8001/api/devices/create-with-id" \
  -d "device_id=test-device-001" \
  -d "name=Test Camera" \
  -d "type=camera" \
  -d "user_id=test-user"

# 2. Update device ID
curl -X PUT "http://localhost:8001/api/devices/test-device-001/update-id?new_device_id=updated-device-001"

# 3. Send notification to device
curl -X POST "http://localhost:8001/api/push/send" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "device_id": "updated-device-001", 
    "title": "Test Alert",
    "body": "Device ID update successful!"
  }'
```

---

## 🎉 **Ready for Production**

Both APIs are:
- ✅ **Fully tested** and working
- ✅ **Error handling** implemented
- ✅ **Data preservation** for ID updates
- ✅ **Validation** and conflict checking
- ✅ **Compatible** with existing notification system

**🚀 Start using these APIs immediately for your device management needs!**