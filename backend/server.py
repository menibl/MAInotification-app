from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
import asyncio
import aiofiles
import shutil
from pywebpush import webpush, WebPushException
from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create uploads directory
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_devices: Dict[str, List[str]] = {}  # user_id -> device_ids
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logging.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        logging.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                logging.error(f"Error sending message to {user_id}: {e}")
                self.disconnect(user_id)
                return False
        return False
    
    async def broadcast_to_user_devices(self, message: dict, user_id: str):
        """Send notification to user from their devices"""
        success = await self.send_personal_message(message, user_id)
        if success:
            # Store notification in database
            notification = Notification(
                user_id=user_id,
                device_id=message.get('device_id', 'unknown'),
                type=message.get('type', 'message'),
                content=message.get('content', ''),
                media_url=message.get('media_url'),
                timestamp=datetime.utcnow()
            )
            await db.notifications.insert_one(notification.dict())

manager = ConnectionManager()

# AI Chat personalities based on device type
AI_PERSONALITIES = {
    "camera": {
        "system_message": "You are an AI assistant for a security camera device. You help monitor and report on security activities. You can analyze images, report motion detection, and provide security insights. Be helpful and security-focused in your responses.",
        "model": "gpt-5-nano"
    },
    "sensor": {
        "system_message": "You are an AI assistant for a sensor device. You help monitor environmental conditions and provide data insights. You can analyze sensor readings, report threshold alerts, and explain environmental patterns. Be analytical and data-focused in your responses.",
        "model": "gpt-5-nano"  
    },
    "doorbell": {
        "system_message": "You are an AI assistant for a smart doorbell device. You help with visitor detection, package monitoring, and door security. You can identify visitors, announce arrivals, and provide door-related security insights. Be friendly but security-conscious in your responses.",
        "model": "gpt-5-nano"
    },
    "default": {
        "system_message": "You are an AI assistant for a smart device. You help monitor device status, analyze data, and provide helpful insights about device functionality. Be helpful and informative in your responses.",
        "model": "gpt-5-nano"
    }
}

async def get_ai_chat_instance(device_type: str, session_id: str):
    """Get AI chat instance for device type"""
    personality = AI_PERSONALITIES.get(device_type, AI_PERSONALITIES["default"])
    
    chat = LlmChat(
        api_key=os.environ.get('OPENAI_API_KEY'),
        session_id=session_id,
        system_message=personality["system_message"]
    ).with_model("openai", personality["model"])
    
    return chat

async def store_chat_history(user_id: str, device_id: str, messages: List[Dict[str, Any]]):
    """Store or update chat history in MongoDB"""
    try:
        # Find existing chat history
        existing = await db.chat_histories.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        if existing:
            # Update existing history
            await db.chat_histories.update_one(
                {"user_id": user_id, "device_id": device_id},
                {
                    "$set": {
                        "history": messages,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        else:
            # Create new chat history
            chat_history = ChatHistory(
                user_id=user_id,
                device_id=device_id,
                history=messages
            )
            await db.chat_histories.insert_one(chat_history.dict())
            
        logging.info(f"Stored chat history for user {user_id}, device {device_id}")
        
    except Exception as e:
        logging.error(f"Failed to store chat history: {e}")

async def get_chat_history(user_id: str, device_id: str) -> List[Dict[str, Any]]:
    """Get chat history from MongoDB"""
    try:
        history_doc = await db.chat_histories.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        if history_doc:
            return history_doc.get("history", [])
        return []
        
    except Exception as e:
        logging.error(f"Failed to get chat history: {e}")
        return []

# Define Models
class Device(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # camera, sensor, etc.
    user_id: str
    status: str = "online"
    location: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DeviceCreate(BaseModel):
    name: str
    type: str
    user_id: str
    location: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class BulkDeviceUpdate(BaseModel):
    device_updates: List[Dict[str, Any]]  # List of {device_id: str, updates: DeviceUpdate}

class PushSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    endpoint: str
    keys: Dict[str, str]  # p256dh and auth keys
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PushSubscriptionCreate(BaseModel):
    user_id: str
    endpoint: str
    keys: Dict[str, str]

class PushNotificationRequest(BaseModel):
    user_id: str
    device_id: str  # Now required
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    image: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, str]]] = None
    require_interaction: Optional[bool] = False

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_id: str
    message: str
    media_url: Optional[str] = None
    sender: str  # 'user', 'device', or 'ai'
    ai_response: bool = False  # True if this is an AI-generated response
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatMessageCreate(BaseModel):
    device_id: str
    message: str
    media_url: Optional[str] = None
    sender: str = "user"

class AIPersonality(BaseModel):
    device_type: str
    system_message: str
    model: str = "gpt-5-nano"
    
class ChatHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_id: str
    history: List[Dict[str, Any]] = []  # JSON array of chat messages
    ai_personality: Optional[AIPersonality] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_id: str
    type: str  # 'message', 'alert', 'media'
    content: str
    media_url: Optional[str] = None
    read: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data.get('type') == 'ping':
                await websocket.send_text(json.dumps({'type': 'pong'}))
            elif message_data.get('type') == 'chat':
                # Handle chat message from user to device with AI response
                device_id = message_data['device_id']
                user_message = message_data['message']
                
                # Store user message
                chat_msg = ChatMessage(
                    user_id=user_id,
                    device_id=device_id,
                    message=user_message,
                    sender='user'
                )
                await db.chat_messages.insert_one(chat_msg.dict())
                
                # Send user message confirmation
                await websocket.send_text(json.dumps({
                    'type': 'message_sent',
                    'message_id': chat_msg.id,
                    'device_id': device_id
                }))
                
                # Generate AI response
                try:
                    device = await db.devices.find_one({"id": device_id})
                    if device:
                        device_type = device.get("type", "default")
                        session_id = f"{user_id}_{device_id}"
                        
                        ai_chat = await get_ai_chat_instance(device_type, session_id)
                        user_msg = UserMessage(text=user_message)
                        ai_response = await ai_chat.send_message(user_msg)
                        
                        # Store AI response
                        ai_chat_msg = ChatMessage(
                            user_id=user_id,
                            device_id=device_id,
                            message=ai_response,
                            sender="ai",
                            ai_response=True
                        )
                        await db.chat_messages.insert_one(ai_chat_msg.dict())
                        
                        # Send AI response via WebSocket
                        await websocket.send_text(json.dumps({
                            'type': 'ai_response',
                            'device_id': device_id,
                            'message': ai_response,
                            'message_id': ai_chat_msg.id,
                            'timestamp': ai_chat_msg.timestamp.isoformat()
                        }))
                        
                        # Update chat history
                        history = await get_chat_history(user_id, device_id)
                        history.extend([
                            {
                                "id": chat_msg.id,
                                "message": user_message,
                                "sender": "user",
                                "timestamp": chat_msg.timestamp.isoformat(),
                                "ai_response": False
                            },
                            {
                                "id": ai_chat_msg.id,
                                "message": ai_response,
                                "sender": "ai",
                                "timestamp": ai_chat_msg.timestamp.isoformat(), 
                                "ai_response": True
                            }
                        ])
                        await store_chat_history(user_id, device_id, history)
                        
                except Exception as ai_error:
                    logging.error(f"WebSocket AI response error: {ai_error}")
                    await websocket.send_text(json.dumps({
                        'type': 'ai_error',
                        'device_id': device_id,
                        'error': str(ai_error)
                    }))
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# Device Management Endpoints
@api_router.post("/devices", response_model=Device)
async def create_device(device: DeviceCreate):
    device_obj = Device(**device.dict())
    await db.devices.insert_one(device_obj.dict())
    return device_obj

@api_router.post("/devices/create-with-id")
async def create_device_with_custom_id(
    device_id: str,
    name: str,
    type: str,
    user_id: str,
    location: Optional[str] = None,
    description: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
    status: str = "online"
):
    """Create a device with a custom ID"""
    
    # Check if device ID already exists
    existing = await db.devices.find_one({"id": device_id})
    if existing:
        raise HTTPException(status_code=400, detail=f"Device with ID '{device_id}' already exists")
    
    # Create device with custom ID
    device_obj = Device(
        id=device_id,
        name=name,
        type=type,
        user_id=user_id,
        location=location,
        description=description,
        settings=settings or {},
        status=status,
        last_seen=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    await db.devices.insert_one(device_obj.dict())
    return {
        "success": True,
        "message": f"Device created with ID: {device_id}",
        "device": device_obj
    }

@api_router.put("/devices/{old_device_id}/update-id")
async def update_device_id(
    old_device_id: str,
    new_device_id: str,
    preserve_data: bool = True
):
    """Update a device's ID by creating new record and optionally preserving data"""
    
    # Check if old device exists
    old_device = await db.devices.find_one({"id": old_device_id})
    if not old_device:
        raise HTTPException(status_code=404, detail=f"Device with ID '{old_device_id}' not found")
    
    # Check if new device ID already exists
    existing_new = await db.devices.find_one({"id": new_device_id})
    if existing_new:
        raise HTTPException(status_code=400, detail=f"Device with ID '{new_device_id}' already exists")
    
    # Create new device with updated ID
    new_device_data = old_device.copy()
    new_device_data["id"] = new_device_id
    new_device_data["updated_at"] = datetime.utcnow()
    
    # Remove the MongoDB _id field so it gets a new one
    if "_id" in new_device_data:
        del new_device_data["_id"]
    
    try:
        # Insert new device
        await db.devices.insert_one(new_device_data)
        
        if preserve_data:
            # Update related data (notifications, chat messages) to use new device ID
            # Update notifications
            notifications_result = await db.notifications.update_many(
                {"device_id": old_device_id},
                {"$set": {"device_id": new_device_id}}
            )
            
            # Update chat messages
            messages_result = await db.chat_messages.update_many(
                {"device_id": old_device_id},
                {"$set": {"device_id": new_device_id}}
            )
            
            data_updated = {
                "notifications_updated": notifications_result.modified_count,
                "messages_updated": messages_result.modified_count
            }
        else:
            data_updated = {
                "notifications_updated": 0,
                "messages_updated": 0,
                "note": "Data preservation was disabled"
            }
        
        # Delete old device
        await db.devices.delete_one({"id": old_device_id})
        
        return {
            "success": True,
            "message": f"Device ID updated from '{old_device_id}' to '{new_device_id}'",
            "old_device_id": old_device_id,
            "new_device_id": new_device_id,
            "data_preservation": data_updated,
            "device": Device(**new_device_data)
        }
        
    except Exception as e:
        # If anything fails, try to clean up
        await db.devices.delete_one({"id": new_device_id})
        raise HTTPException(status_code=500, detail=f"Failed to update device ID: {str(e)}")

@api_router.get("/devices/{user_id}", response_model=List[Device])
async def get_user_devices(user_id: str):
    devices = await db.devices.find({"user_id": user_id}).to_list(100)
    return [Device(**device) for device in devices]

@api_router.put("/devices/{device_id}/status")
async def update_device_status(device_id: str, status: str):
    result = await db.devices.update_one(
        {"id": device_id},
        {"$set": {"status": status, "last_seen": datetime.utcnow(), "updated_at": datetime.utcnow()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"success": True}

@api_router.put("/devices/{device_id}", response_model=Device)
async def update_device(device_id: str, updates: DeviceUpdate):
    """Update a single device with new information"""
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.devices.update_one(
        {"id": device_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Return updated device
    device = await db.devices.find_one({"id": device_id})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return Device(**device)

@api_router.put("/devices/bulk-update")
async def bulk_update_devices(bulk_update: BulkDeviceUpdate):
    """Update multiple devices at once"""
    updated_count = 0
    failed_updates = []
    
    for device_update in bulk_update.device_updates:
        device_id = device_update.get("device_id")
        updates = device_update.get("updates", {})
        
        if not device_id:
            failed_updates.append({"error": "Missing device_id", "data": device_update})
            continue
            
        # Prepare update data
        update_data = {k: v for k, v in updates.items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await db.devices.update_one(
                {"id": device_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                updated_count += 1
            else:
                failed_updates.append({"error": "Device not found", "device_id": device_id})
                
        except Exception as e:
            failed_updates.append({"error": str(e), "device_id": device_id})
    
    return {
        "success": True,
        "updated_count": updated_count,
        "failed_updates": failed_updates,
        "total_attempted": len(bulk_update.device_updates)
    }

@api_router.delete("/devices/{device_id}")
async def delete_device(device_id: str):
    """Delete a device"""
    result = await db.devices.delete_one({"id": device_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"success": True, "message": "Device deleted successfully"}

@api_router.delete("/devices/user/{user_id}/delete-all")
async def delete_all_user_devices(
    user_id: str, 
    delete_notifications: bool = True,
    delete_chat_messages: bool = True,
    delete_push_subscriptions: bool = False,
    confirm_deletion: bool = False
):
    """Delete all devices for a user and optionally related data"""
    
    if not confirm_deletion:
        raise HTTPException(
            status_code=400, 
            detail="This operation requires confirmation. Set confirm_deletion=true to proceed."
        )
    
    # Get all devices for the user first (for reporting)
    devices = await db.devices.find({"user_id": user_id}).to_list(1000)
    device_count = len(devices)
    device_ids = [device["id"] for device in devices]
    
    if device_count == 0:
        return {
            "success": True,
            "message": "No devices found for user",
            "deleted_count": 0,
            "related_data_deleted": {}
        }
    
    deleted_data = {}
    
    try:
        # Delete all devices
        devices_result = await db.devices.delete_many({"user_id": user_id})
        deleted_data["devices"] = devices_result.deleted_count
        
        # Delete related data if requested
        if delete_notifications:
            notifications_result = await db.notifications.delete_many({"user_id": user_id})
            deleted_data["notifications"] = notifications_result.deleted_count
        
        if delete_chat_messages:
            messages_result = await db.chat_messages.delete_many({"user_id": user_id})
            deleted_data["chat_messages"] = messages_result.deleted_count
        
        if delete_push_subscriptions:
            subscriptions_result = await db.push_subscriptions.delete_many({"user_id": user_id})
            deleted_data["push_subscriptions"] = subscriptions_result.deleted_count
        
        return {
            "success": True,
            "message": f"Successfully deleted all devices and related data for user {user_id}",
            "user_id": user_id,
            "deleted_devices": device_ids,
            "deleted_count": device_count,
            "related_data_deleted": deleted_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete devices: {str(e)}"
        )

@api_router.delete("/devices/user/{user_id}/delete-all-safe")
async def delete_all_user_devices_safe(user_id: str):
    """Safe delete - only removes devices, preserves all related data"""
    
    # Get all devices for the user first (for reporting)
    devices = await db.devices.find({"user_id": user_id}).to_list(1000)
    device_count = len(devices)
    device_ids = [device["id"] for device in devices]
    
    if device_count == 0:
        return {
            "success": True,
            "message": "No devices found for user",
            "deleted_count": 0
        }
    
    try:
        # Only delete devices, preserve all related data
        devices_result = await db.devices.delete_many({"user_id": user_id})
        
        return {
            "success": True,
            "message": f"Successfully deleted {devices_result.deleted_count} devices for user {user_id}",
            "user_id": user_id,
            "deleted_devices": device_ids,
            "deleted_count": devices_result.deleted_count,
            "note": "Related data (notifications, messages) was preserved"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete devices: {str(e)}"
        )

# Push Notification Endpoints
@api_router.post("/push/subscribe")
async def subscribe_to_push(subscription: PushSubscriptionCreate):
    """Subscribe user to push notifications"""
    # Check if subscription already exists
    existing = await db.push_subscriptions.find_one({
        "user_id": subscription.user_id,
        "endpoint": subscription.endpoint
    })
    
    if existing:
        return {"success": True, "message": "Subscription already exists", "subscription_id": existing["id"]}
    
    # Create new subscription
    push_sub = PushSubscription(**subscription.dict())
    await db.push_subscriptions.insert_one(push_sub.dict())
    
    return {"success": True, "message": "Subscribed to push notifications", "subscription_id": push_sub.id}

@api_router.delete("/push/unsubscribe/{user_id}")
async def unsubscribe_from_push(user_id: str, endpoint: Optional[str] = None):
    """Unsubscribe user from push notifications"""
    query = {"user_id": user_id}
    if endpoint:
        query["endpoint"] = endpoint
    
    result = await db.push_subscriptions.delete_many(query)
    
    return {
        "success": True,
        "message": f"Unsubscribed {result.deleted_count} subscription(s)",
        "deleted_count": result.deleted_count
    }

@api_router.post("/push/send")
async def send_push_notification(notification: PushNotificationRequest):
    """Send push notification to user's subscribed devices"""
    
    # Get user's push subscriptions
    subscriptions = await db.push_subscriptions.find({"user_id": notification.user_id}).to_list(100)
    
    if not subscriptions:
        return {"success": False, "message": "No push subscriptions found for user"}
    
    sent_count = 0
    failed_count = 0
    
    # Prepare notification payload
    payload = {
        "title": notification.title,
        "body": notification.body,
        "icon": notification.icon or "/manifest-icon-192.png",
        "badge": notification.badge or "/manifest-icon-192.png",
        "image": notification.image,
        "data": notification.data or {},
        "actions": notification.actions or [],
        "requireInteraction": notification.require_interaction,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # VAPID keys from environment variables
    vapid_private_key = os.environ.get('VAPID_PRIVATE_KEY')
    vapid_public_key = os.environ.get('VAPID_PUBLIC_KEY')
    vapid_email = os.environ.get('VAPID_EMAIL', 'mailto:admin@device-chat.com')
    
    if not vapid_private_key or not vapid_public_key:
        logging.warning("VAPID keys not configured properly")
        return {
            "success": False,
            "message": "Push notifications not configured. Please set VAPID keys in environment variables.",
            "sent_count": 0,
            "failed_count": len(subscriptions),
            "total_subscriptions": len(subscriptions)
        }
    
    # Send to all subscriptions
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription["endpoint"],
                    "keys": subscription["keys"]
                },
                data=json.dumps(payload),
                vapid_private_key=vapid_private_key,
                vapid_claims={
                    "sub": vapid_email
                }
            )
            sent_count += 1
            
        except WebPushException as e:
            logging.error(f"Failed to send push notification: {e}")
            failed_count += 1
            
            # Remove invalid subscriptions
            if e.response and e.response.status_code == 410:
                await db.push_subscriptions.delete_one({"id": subscription["id"]})
                logging.info(f"Removed invalid subscription: {subscription['id']}")
                
        except Exception as e:
            logging.error(f"Unexpected error sending push notification: {e}")
            failed_count += 1
    
    # Store notification in database for history (regardless of push success)
    try:
        notification_record = Notification(
            user_id=notification.user_id,
            device_id=notification.device_id,  # Use the required device_id
            type='push',
            content=f"{notification.title}: {notification.body}",
            media_url=notification.image,
            read=False,
            timestamp=datetime.utcnow()
        )
        await db.notifications.insert_one(notification_record.dict())
        logging.info(f"Stored notification in database for user {notification.user_id}, device {notification.device_id}")
    except Exception as e:
        logging.error(f"Failed to store notification in database: {e}")
    
    return {
        "success": sent_count > 0,
        "message": f"Sent {sent_count} notifications, {failed_count} failed",
        "sent_count": sent_count,
        "failed_count": failed_count,
        "total_subscriptions": len(subscriptions)
    }

@api_router.get("/push/subscriptions/{user_id}")
async def get_user_push_subscriptions(user_id: str):
    """Get all push subscriptions for a user"""
    subscriptions = await db.push_subscriptions.find({"user_id": user_id}).to_list(100)
    return [PushSubscription(**sub) for sub in subscriptions]

# Chat Endpoints
@api_router.post("/chat/send")
async def send_chat_message(user_id: str, message: ChatMessageCreate):
    try:
        # Store user message
        user_chat_msg = ChatMessage(
            user_id=user_id,
            **message.dict()
        )
        await db.chat_messages.insert_one(user_chat_msg.dict())
        
        # Get device info for AI personality
        device = await db.devices.find_one({"id": message.device_id})
        if not device:
            return {"success": False, "error": "Device not found"}
        
        device_type = device.get("type", "default")
        session_id = f"{user_id}_{message.device_id}"
        
        # Get chat history for context
        history = await get_chat_history(user_id, message.device_id)
        
        # Generate AI response
        try:
            ai_chat = await get_ai_chat_instance(device_type, session_id)
            user_message = UserMessage(text=message.message)
            ai_response = await ai_chat.send_message(user_message)
            
            # Store AI response as chat message
            ai_chat_msg = ChatMessage(
                user_id=user_id,
                device_id=message.device_id,
                message=ai_response,
                sender="ai",
                ai_response=True
            )
            await db.chat_messages.insert_one(ai_chat_msg.dict())
            
            # Update chat history with both messages
            history.extend([
                {
                    "id": user_chat_msg.id,
                    "message": message.message,
                    "sender": "user",
                    "timestamp": user_chat_msg.timestamp.isoformat(),
                    "ai_response": False
                },
                {
                    "id": ai_chat_msg.id,
                    "message": ai_response,
                    "sender": "ai", 
                    "timestamp": ai_chat_msg.timestamp.isoformat(),
                    "ai_response": True
                }
            ])
            
            # Store updated history
            await store_chat_history(user_id, message.device_id, history)
            
            # Send AI response via WebSocket if connected
            if user_id in manager.active_connections:
                await manager.send_personal_message({
                    "type": "ai_response",
                    "device_id": message.device_id,
                    "message": ai_response,
                    "message_id": ai_chat_msg.id,
                    "timestamp": ai_chat_msg.timestamp.isoformat()
                }, user_id)
            
            return {
                "success": True, 
                "message_id": user_chat_msg.id,
                "ai_response": {
                    "message": ai_response,
                    "message_id": ai_chat_msg.id
                }
            }
            
        except Exception as ai_error:
            logging.error(f"AI response failed: {ai_error}")
            return {
                "success": True, 
                "message_id": user_chat_msg.id,
                "ai_response": {
                    "message": f"Sorry, I'm having trouble responding right now. Error: {str(ai_error)}",
                    "error": True
                }
            }
        
    except Exception as e:
        logging.error(f"Failed to send chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/chat/{user_id}/{device_id}", response_model=List[ChatMessage])
async def get_chat_messages(user_id: str, device_id: str, limit: int = 50):
    messages = await db.chat_messages.find({
        "user_id": user_id,
        "device_id": device_id
    }).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Reverse to get chronological order
    messages.reverse()
    return [ChatMessage(**msg) for msg in messages]

@api_router.get("/chat/{user_id}/{device_id}/history")
async def get_chat_history_json(user_id: str, device_id: str):
    """Get JSON chat history for a specific device"""
    history = await get_chat_history(user_id, device_id)
    
    # Also get the full document info
    history_doc = await db.chat_histories.find_one({
        "user_id": user_id,
        "device_id": device_id
    })
    
    return {
        "success": True,
        "user_id": user_id,
        "device_id": device_id,
        "history": history,
        "message_count": len(history),
        "created_at": history_doc.get("created_at") if history_doc else None,
        "updated_at": history_doc.get("updated_at") if history_doc else None
    }

@api_router.delete("/chat/{user_id}/{device_id}/history")
async def clear_chat_history(user_id: str, device_id: str):
    """Clear chat history for a specific device"""
    try:
        # Delete from chat_histories collection
        await db.chat_histories.delete_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        # Delete from chat_messages collection
        result = await db.chat_messages.delete_many({
            "user_id": user_id,
            "device_id": device_id
        })
        
        return {
            "success": True,
            "message": f"Cleared chat history for device {device_id}",
            "deleted_messages": result.deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Notification Endpoints
@api_router.get("/notifications/{user_id}", response_model=List[Notification])
async def get_notifications(user_id: str, limit: int = 50, unread_only: bool = False):
    query = {"user_id": user_id}
    if unread_only:
        query["read"] = False
        
    notifications = await db.notifications.find(query).sort("timestamp", -1).limit(limit).to_list(limit)
    return [Notification(**notif) for notif in notifications]

@api_router.get("/notifications/{user_id}/device/{device_id}", response_model=List[Notification])
async def get_device_notifications(user_id: str, device_id: str, limit: int = 50, unread_only: bool = False):
    """Get notifications for a specific device"""
    query = {"user_id": user_id, "device_id": device_id}
    if unread_only:
        query["read"] = False
        
    notifications = await db.notifications.find(query).sort("timestamp", -1).limit(limit).to_list(limit)
    return [Notification(**notif) for notif in notifications]

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    result = await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}

# Simulate device sending notification (for testing)
@api_router.post("/simulate/device-notification")
async def simulate_device_notification(
    user_id: str,
    device_id: str,  
    message: str,
    media_url: Optional[str] = None,
    notification_type: str = "message"
):
    """Simulate a device sending a notification to user"""
    notification_data = {
        'type': notification_type,
        'device_id': device_id,
        'content': message,
        'media_url': media_url,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Send via WebSocket
    success = await manager.broadcast_to_user_devices(notification_data, user_id)
    
    # Also store as chat message if it's a message type
    if notification_type == "message":
        chat_msg = ChatMessage(
            user_id=user_id,
            device_id=device_id,
            message=message,
            media_url=media_url,
            sender='device'
        )
        await db.chat_messages.insert_one(chat_msg.dict())
    
    return {"success": success, "message": "Notification sent" if success else "User not connected"}

# Original endpoints
@api_router.get("/")
async def root():
    return {"message": "Device Chat API - WebSocket enabled"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()