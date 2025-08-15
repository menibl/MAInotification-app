# Device Chat - Mobile PWA for IoT Communication

A production-ready Progressive Web App (PWA) that enables real-time chat with IoT devices, push notifications, and AI-powered device conversations using OpenAI's GPT models.

![Mobile PWA](https://img.shields.io/badge/Mobile-PWA-blue)
![OpenAI](https://img.shields.io/badge/AI-OpenAI_GPT--5--nano-green)
![WebSocket](https://img.shields.io/badge/Real--time-WebSocket-orange)
![Push Notifications](https://img.shields.io/badge/Push-Notifications-red)

## 🚀 Features

### 🤖 AI-Powered Device Chat
- **Live AI conversations** with IoT devices using OpenAI GPT-5-nano
- **Device-specific AI personalities** (cameras act as security assistants, sensors as monitoring assistants)
- **Complete chat history** stored in JSON format per device
- **Real-time responses** via WebSocket connections

### 📱 Mobile-First PWA
- **Progressive Web App** - Installable on mobile devices
- **Offline-ready** with service worker caching
- **Touch-optimized** interface with 44px minimum touch targets
- **Responsive design** optimized for 390x844 mobile viewport

### 🔔 Push Notifications
- **Web Push Protocol** with VAPID authentication
- **Rich notifications** with images, actions, and custom data
- **Device-specific notifications** with automatic categorization
- **Real-time delivery** even when app is closed

### 🛠 Complete Device Management
- **Custom device IDs** - Create devices with your own ID format
- **Bulk operations** - Update multiple devices simultaneously
- **Device metadata** - Location, description, settings, status tracking
- **Data preservation** during ID updates

## 🏗 Architecture

### Backend (FastAPI + WebSocket + MongoDB)
- **FastAPI** - Modern Python API framework
- **WebSocket** - Real-time bidirectional communication
- **MongoDB** - Document storage for devices, messages, and history
- **OpenAI Integration** - GPT-5-nano for intelligent responses
- **Push Notifications** - Web Push Protocol implementation

### Frontend (React PWA)
- **React 19** - Modern React with concurrent features
- **Tailwind CSS** - Utility-first styling
- **Service Worker** - Offline functionality and push notifications
- **WebSocket Client** - Real-time communication with auto-reconnection

## 📋 Prerequisites

- **Node.js** 18+ and Yarn
- **Python** 3.8+ and pip
- **MongoDB** (local or cloud)
- **OpenAI API Key** (for AI chat functionality)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd device-chat

# Quick environment setup
chmod +x setup-env.sh
./setup-env.sh
```

### 2. Configure Environment
Edit the created `.env` files with your credentials:
- **OpenAI API Key** in `backend/.env`
- **VAPID Keys** in `backend/.env` (generate with `web-push generate-vapid-keys`)
- **Backend URL** in `frontend/.env`

### 3. Install Dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Frontend
cd frontend
yarn install
```

### 4. Start Services
```bash
# Backend (from /backend directory)
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend (from /frontend directory)  
yarn start
```

## ⚙️ Environment Setup

### Backend (.env)
```env
# MongoDB Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="your_database_name"
CORS_ORIGINS="*"

# VAPID Keys for Push Notifications
VAPID_PRIVATE_KEY="your-vapid-private-key"
VAPID_PUBLIC_KEY="your-vapid-public-key"
VAPID_EMAIL="mailto:your-email@domain.com"

# OpenAI API Configuration
OPENAI_API_KEY="your-openai-api-key-here"
```

### Frontend (.env)
```env
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# WebSocket port for development
WDS_SOCKET_PORT=3000
```

## 🎯 Core APIs

### 🤖 AI Chat
```bash
# Send message and get AI response
POST /api/chat/send?user_id={user_id}
{
  "device_id": "your-device-id",
  "message": "Hello AI, what can you do?",
  "sender": "user"
}

# Get JSON chat history
GET /api/chat/{user_id}/{device_id}/history
```

### 🔔 Push Notifications
```bash
# Send push notification
POST /api/push/send
{
  "user_id": "user123",
  "device_id": "device123",
  "title": "Alert Title",
  "body": "Notification message",
  "image": "https://example.com/image.jpg"
}
```

### 📱 Device Management
```bash
# Create device with custom ID
POST /api/devices/create-with-id?device_id=YOUR_ID&name=Device+Name&type=camera&user_id=user123

# Update device ID with data preservation
PUT /api/devices/{old_device_id}/update-id?new_device_id=NEW_ID&preserve_data=true

# Bulk update devices
PUT /api/devices/bulk-update
{
  "device_updates": [
    {
      "device_id": "device1",
      "updates": {"status": "online", "location": "Kitchen"}
    }
  ]
}

# Delete all user devices
DELETE /api/devices/user/{user_id}/delete-all?confirm_deletion=true
```

## 🧠 AI Personalities

The system includes device-specific AI personalities:

- **Camera**: Security-focused assistant for monitoring and alerts
- **Sensor**: Data-focused assistant for environmental monitoring  
- **Doorbell**: Visitor detection and door security assistant
- **Default**: General smart device assistant

Each personality uses tailored system prompts to provide relevant, context-aware responses.

## 📊 Database Schema

### Devices
```javascript
{
  "id": "device-uuid-or-custom-id",
  "name": "Device Name",
  "type": "camera|sensor|doorbell|other",
  "user_id": "user-id",
  "status": "online|offline",
  "location": "Physical Location",
  "description": "Device Description",
  "settings": {}, // Custom JSON settings
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### Chat History (JSON per device)
```javascript
{
  "user_id": "user-id",
  "device_id": "device-id", 
  "history": [
    {
      "id": "message-id",
      "message": "Hello AI",
      "sender": "user|ai|device",
      "timestamp": "2025-01-15T10:30:00Z",
      "ai_response": true|false
    }
  ],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

## 🔧 Production Deployment

### Environment Variables for Production
- Update `REACT_APP_BACKEND_URL` to your production backend URL
- Use secure MongoDB connection string
- Generate production VAPID keys
- Use production OpenAI API key with appropriate rate limits

### Security Considerations
- Enable HTTPS for WebSocket (WSS) connections
- Configure CORS origins for production domains
- Implement rate limiting for API endpoints
- Secure MongoDB with authentication
- Monitor OpenAI API usage and costs

## 📱 PWA Installation

Users can install the app on mobile devices:
1. Open the app in mobile browser
2. Use "Add to Home Screen" option
3. App appears as native app icon
4. Works offline with service worker

## 🧪 Testing

The project includes comprehensive test scripts:

```bash
# Test AI chat functionality
python test_ai_chat.py

# Test device creation APIs
python test_device_creation_apis.py

# Test push notifications
python test_new_apis.py

# Test device-specific notifications
python test_device_notifications.py
```

## 🎯 Use Cases

Perfect for:
- **IoT Device Monitoring** - Security cameras, sensors, smart devices
- **Real-time Alerts** - Motion detection, temperature alerts, door sensors
- **AI-Powered Assistance** - Intelligent device conversations and insights
- **Mobile Management** - Manage devices from anywhere with PWA
- **Custom Device Integration** - Flexible device ID and metadata management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Live Demo**: [Your deployed URL]
- **API Documentation**: [Your API docs URL]
- **Issues**: [GitHub Issues URL]

---

**Built with ❤️ for IoT device communication and AI-powered assistance**

*Ready to deploy and scale for production IoT applications with intelligent device conversations.*
