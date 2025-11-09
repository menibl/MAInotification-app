from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Tuple
import uuid
from datetime import datetime
import asyncio
import aiofiles
import shutil
from pywebpush import webpush, WebPushException
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType, ImageContent
import requests
import base64
from io import BytesIO
import jwt
import bcrypt
import pyotp


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Backend URL for file serving
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')

# Create uploads directory
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret-change')
JWT_ALG = 'HS256'
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
OAUTH_GOOGLE_REDIRECT_URI = os.environ.get('OAUTH_GOOGLE_REDIRECT_URI')


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

async def get_ai_chat_instance(device_type: str, session_id: str, has_images: bool = False, user_id: str = None, device_id: str = None):
    """Get AI chat instance for device type, with vision support if images are present"""
    
    # Try to get custom settings first
    custom_settings = None
    if user_id and device_id:
        custom_settings = await db.chat_settings.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
    
    if custom_settings:
        # Use custom settings
        system_message = custom_settings["system_message"]
        model = custom_settings["model"]
        print(f"DEBUG: Using custom chat settings - Role: {custom_settings['role_name']}")
    else:
        # Use default personality
        personality = AI_PERSONALITIES.get(device_type, AI_PERSONALITIES["default"])
        system_message = personality["system_message"]
        model = personality["model"]
        print(f"DEBUG: Using default personality for {device_type}")
    
    # Use vision model if images are present - updated to use current model
    if has_images:
        model = "gpt-4o"
        print(f"DEBUG: Switching to vision model: {model}")
    
    chat = LlmChat(
        api_key=os.environ.get('OPENAI_API_KEY'),
        session_id=session_id,
        system_message=system_message
    ).with_model("openai", model)
    
    return chat

async def download_image_as_base64(url: str) -> Optional[str]:
    """Download an image from URL and convert to base64"""
    try:
        response = requests.get(url, timeout=10, stream=True)
        if response.status_code == 200:
            # Get content type to determine format
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                return None
            
            # Read image data
            image_data = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                image_data.write(chunk)
            
            # Convert to base64
            image_data.seek(0)
            image_base64 = base64.b64encode(image_data.getvalue()).decode('utf-8')
            return image_base64
        return None
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
        return None

async def create_vision_message(message: str, file_contents_for_ai: List[Dict], media_urls: List[str]) -> tuple:
    """Create a UserMessage with proper image attachments for vision models"""
    
    file_attachments = []
    vision_text_parts = [message]
    
    # Process uploaded image files
    for file_content in file_contents_for_ai:
        if file_content['type'] == 'image' and 'file_url' in file_content:
            # For uploaded image files, convert to base64 for OpenAI
            try:
                # Convert the URL to local file path
                file_id = file_content['file_url'].split('/')[-1]
                file_record = await db.file_uploads.find_one({"id": file_id})
                if file_record and Path(file_record["file_path"]).exists():
                    # Read file and convert to base64
                    async with aiofiles.open(file_record["file_path"], 'rb') as f:
                        image_data = await f.read()
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        
                        image_content = ImageContent(image_base64=image_base64)
                        file_attachments.append(image_content)
                        vision_text_parts.append(f"\n[Uploaded Image: {file_content['filename']}]")
            except Exception as e:
                print(f"Failed to process uploaded image {file_content['filename']}: {e}")
                vision_text_parts.append(f"\n[Image Upload Error: Could not process {file_content['filename']}]")
        else:
            # For non-image files, add text description
            vision_text_parts.append(f"\n{file_content['content']}")
    
    # Process image URLs
    for url in media_urls:
        if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
            # Download and convert image to base64
            image_base64 = await download_image_as_base64(url)
            if image_base64:
                try:
                    image_content = ImageContent(image_base64=image_base64)
                    file_attachments.append(image_content)
                    vision_text_parts.append(f"\n[Image from URL: {url}]")
                except Exception as e:
                    print(f"Failed to create ImageContent for {url}: {e}")
                    vision_text_parts.append(f"\n[Image URL Error: Could not process {url}]")
            else:
                vision_text_parts.append(f"\n[Image URL: {url} - Could not download for analysis]")
        else:
            vision_text_parts.append(f"\n[Media URL: {url}]")
    
    # Combine all text parts
    enhanced_message = "\n".join(vision_text_parts)
    
    print(f"DEBUG: Created vision message with {len(file_attachments)} image attachments")
    return enhanced_message, file_attachments

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
    device_id: str  # Now required (camera ID)
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    image: Optional[str] = None
    video_url: Optional[str] = None
    sound_id: Optional[str] = None  # e.g., 'significant', 'alert'
    sound_url: Optional[str] = None  # absolute URL to an audio file
    data: Optional[Dict[str, Any]] = None  # should include at least device_id; now may include camera_id
    actions: Optional[List[Dict[str, str]]] = None
    require_interaction: Optional[bool] = False
    # Extended metadata fields
    camera_id: Optional[str] = None  # Camera ID (same as device_id usually)
    camera_name: Optional[str] = None  # Camera display name
    mission_id: Optional[str] = None  # Mission ID
    mission_name: Optional[str] = None  # Mission display name
    user_email: Optional[str] = None  # User email
    image_url: Optional[str] = None  # Image URL (alias for image)
    rtmp_code: Optional[str] = None  # RTMP stream code/URL

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_id: str
    message: str
    media_url: Optional[str] = None
    media_urls: Optional[List[str]] = None  # Support multiple media URLs
    file_attachments: Optional[List[Dict[str, Any]]] = None  # List of file info: {filename, file_path, file_type, file_size}
    referenced_messages: Optional[List[str]] = None  # List of message IDs being referenced/quoted
    sender: str  # 'user', 'device', or 'ai'
    ai_response: bool = False  # True if this is an AI-generated response
    # New unified metadata fields
    camera_id: Optional[str] = None
    mission_id: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    sound_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatMessageCreate(BaseModel):
    device_id: str
    message: str
    media_url: Optional[str] = None
    media_urls: Optional[List[str]] = None  # Support multiple media URLs
    referenced_messages: Optional[List[str]] = None
    file_ids: Optional[List[str]] = None
    sender: str = "user"
    # New unified metadata (optional in request; server will fill defaults)
    camera_id: Optional[str] = None
    mission_id: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    sound_id: Optional[str] = None

class ChatSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_id: str
    role_name: str = "AI Assistant"
    system_message: str
    instructions: Optional[str] = None
    model: str = "gpt-5-nano"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ChatSettingsCreate(BaseModel):
    role_name: str
    system_message: str
    instructions: Optional[str] = None
    model: str = "gpt-5-nano"

class ChatSettingsUpdate(BaseModel):
    role_name: Optional[str] = None
    system_message: Optional[str] = None
    instructions: Optional[str] = None
    model: Optional[str] = None

class DirectImageChat(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_id: str
    image_data: str  # base64 encoded image
    question: Optional[str] = None
    ai_response: str
    display_in_chat: bool  # Whether to display in chat or just log
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DirectImageChatCreate(BaseModel):
    device_id: str
    image_data: Optional[str] = None  # base64 encoded
    image_url: Optional[str] = None   # URL to image
    media_urls: Optional[List[str]] = None  # Multiple image URLs for analysis
    video_url: Optional[str] = None   # Optional event video URL to store/show
    question: Optional[str] = None
    # Unified metadata
    camera_id: Optional[str] = None
    mission_id: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    image_url_single: Optional[str] = None  # alias in case clients send this
    sound_id: Optional[str] = None

class CameraPrompt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_id: str
    prompt_text: str
    instructions: str  # What the user wants to look for
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CameraPromptCreate(BaseModel):
    instructions: str  # User's description of what to look for

class CameraPromptCommand(BaseModel):
    user_id: str
    device_id: str
    message: str

class CameraPromptFixCommand(BaseModel):
    user_id: str
    device_id: str
    message: str
    referenced_messages: Optional[List[str]] = None

class RoleChangeCommand(BaseModel):
    user_id: str
    device_id: str
    message: str

class FileUpload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: str
    file_path: str
    file_type: str
    file_size: int
    user_id: str
    device_id: Optional[str] = None
    message_id: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

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
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: Optional[str] = None
    totp_enabled: bool = False
    totp_secret: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class Enable2FAResponse(BaseModel):
    otpauth_url: str
    secret: str

class Verify2FARequest(BaseModel):
    email: str
    code: str



class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_id: str
    type: str  # 'message', 'alert', 'media'
    content: str
    media_url: Optional[str] = None
    read: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # Extended metadata fields
    camera_id: Optional[str] = None  # Camera ID
    camera_name: Optional[str] = None  # Camera display name
    mission_id: Optional[str] = None  # Mission ID
    mission_name: Optional[str] = None  # Mission display name
    user_email: Optional[str] = None  # User email
    video_url: Optional[str] = None  # Video URL
    image_url: Optional[str] = None  # Image URL
    rtmp_code: Optional[str] = None  # RTMP stream code/URL

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
# Auth helpers

def create_jwt(email: str) -> str:
    payload = {
        'sub': email,
        'email': email,
        'iat': int(datetime.utcnow().timestamp()),
        'exp': int((datetime.utcnow()).timestamp()) + 60*60*24*7
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

async def get_user_by_email(email: str) -> Optional[dict]:
    return await db.users.find_one({ 'email': email.lower() })

async def ensure_user(email: str) -> dict:
    user = await get_user_by_email(email)
    if user:
        return user
    doc = User(email=email.lower()).dict()
    await db.users.insert_one(doc)
    return doc

@api_router.post('/auth/register')
async def auth_register(req: RegisterRequest):
    email = req.email.strip().lower()
    existing = await get_user_by_email(email)
    if existing:
        return { 'success': False, 'error': 'Email already registered' }
    pw_hash = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(email=email, password_hash=pw_hash)
    await db.users.insert_one(user.dict())
    token = create_jwt(email)
    return { 'success': True, 'token': token, 'email': email }

@api_router.post('/auth/login')
async def auth_login(req: LoginRequest):
    email = req.email.strip().lower()
    user = await get_user_by_email(email)
    if not user or not user.get('password_hash'):
        return { 'success': False, 'error': 'Invalid credentials' }
    if not bcrypt.checkpw(req.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return { 'success': False, 'error': 'Invalid credentials' }
    if user.get('totp_enabled'):
        # 2FA required, return partial
        return { 'success': True, 'requires_2fa': True, 'email': email }
    token = create_jwt(email)
    return { 'success': True, 'token': token, 'email': email }

@api_router.post('/auth/enable-2fa')
async def enable_2fa(email: str):
    # Create secret and return otpauth URL
    user = await ensure_user(email)
    if user.get('totp_enabled') and user.get('totp_secret'):
        secret = user['totp_secret']
    else:
        secret = pyotp.random_base32()
        await db.users.update_one({'email': email}, {'$set': { 'totp_secret': secret }}, upsert=True)
    totp = pyotp.TOTP(secret)
    otpauth_url = totp.provisioning_uri(name=email, issuer_name='MAI Focus')
    return Enable2FAResponse(otpauth_url=otpauth_url, secret=secret)

@api_router.post('/auth/verify-2fa')
async def verify_2fa(req: Verify2FARequest):
    user = await get_user_by_email(req.email.strip().lower())
    if not user or not user.get('totp_secret'):
        return { 'success': False, 'error': '2FA not initialized' }
    totp = pyotp.TOTP(user['totp_secret'])
    if not totp.verify(req.code, valid_window=1):
        return { 'success': False, 'error': 'Invalid code' }
    # Mark enabled
    await db.users.update_one({'email': user['email']}, {'$set': { 'totp_enabled': True }})
    token = create_jwt(user['email'])
    return { 'success': True, 'token': token, 'email': user['email'] }

@api_router.get('/auth/me')
async def auth_me(token: Optional[str] = None):
    try:
        t = token or ''
        if not t:
            return { 'authenticated': False }
        data = jwt.decode(t, JWT_SECRET, algorithms=[JWT_ALG])
        return { 'authenticated': True, 'email': data.get('email') }
    except Exception:
        return { 'authenticated': False }

# Google OAuth minimal endpoints (start and callback)
from urllib.parse import urlencode

@api_router.get('/oauth/google/start')
async def google_start():
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': OAUTH_GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'online',
        'prompt': 'select_account'
    }
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    return RedirectResponse(url)

@api_router.get('/oauth/google/callback')
async def google_callback(code: str):
    # Exchange code
    token_resp = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': OAUTH_GOOGLE_REDIRECT_URI
    }, timeout=10)
    if token_resp.status_code != 200:
        return JSONResponse({ 'success': False, 'error': 'Token exchange failed' }, status_code=400)
    tokens = token_resp.json()
    id_token = tokens.get('id_token')
    # Parse id_token (naive, skipping signature verification in MVP)
    try:
        data = jwt.decode(id_token, options={ 'verify_signature': False, 'verify_aud': False, 'verify_iss': False })
        email = data.get('email')
        if not email:
            return JSONResponse({ 'success': False, 'error': 'No email in token' }, status_code=400)
        await ensure_user(email)
        token = create_jwt(email)
        # Redirect back to frontend with token/email so the SPA can store it
        return RedirectResponse(url=f"/?token={token}&email={email}")
    except Exception as e:
        return JSONResponse({ 'success': False, 'error': str(e) }, status_code=400)



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
        "video_url": notification.video_url,
        "sound_id": notification.sound_id,
        "sound_url": notification.sound_url,
        "data": notification.data or {},
        "actions": notification.actions or [],
        "requireInteraction": notification.require_interaction,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Ensure deep-link info and extended metadata is present in data
    try:
        if not isinstance(payload["data"], dict):
            payload["data"] = {}
        payload["data"].setdefault("device_id", notification.device_id)
        # include camera_id if present in data or infer from device_id
        payload['data']['camera_id'] = notification.camera_id or notification.device_id
        if notification.video_url:
            payload["data"]["video_url"] = notification.video_url
        # Add extended metadata to payload data
        if notification.camera_name:
            payload["data"]["camera_name"] = notification.camera_name
        if notification.mission_id:
            payload["data"]["mission_id"] = notification.mission_id
        if notification.mission_name:
            payload["data"]["mission_name"] = notification.mission_name
        if notification.user_email:
            payload["data"]["user_email"] = notification.user_email
        if notification.image_url:
            payload["data"]["image_url"] = notification.image_url
        if notification.rtmp_code:
            payload["data"]["rtmp_code"] = notification.rtmp_code
    except Exception as _:
        pass
    
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
            device_id=notification.device_id,
            type='push',
            content=f"{notification.title}: {notification.body}",
            media_url=notification.video_url or notification.image,
            read=False,
            timestamp=datetime.utcnow(),
            # Extended metadata
            camera_id=notification.camera_id or notification.device_id,
            camera_name=notification.camera_name,
            mission_id=notification.mission_id,
            mission_name=notification.mission_name,
            user_email=notification.user_email,
            video_url=notification.video_url,
            image_url=notification.image_url or notification.image,
            rtmp_code=notification.rtmp_code
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
async def send_chat_message(user_id: str, message_data: ChatMessageCreate):
    """Send a chat message with optional file attachments, media URLs, and message references"""
    
    try:
        # Extract data from the model
        device_id = message_data.device_id
        message = message_data.message
        sender = message_data.sender
        referenced_messages = message_data.referenced_messages
        file_ids = message_data.file_ids
        media_urls = message_data.media_urls or []
        if message_data.media_url:  # Support single media_url for backward compatibility
            media_urls.append(message_data.media_url)
        
        # Helper function to detect if URL/file is an image
        def is_image_content(url: str = None, file_type: str = None, filename: str = None) -> bool:
            if file_type and file_type.startswith('image/'):
                return True
            if url or filename:
                content = url or filename
                return any(content.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'])
            return False
        
        # Detect if we have images (for vision model selection)
        has_images = False
        # Process file attachments if provided
        file_attachments = []
        file_contents_for_ai = []
        
        if file_ids:
            print(f"DEBUG: Processing {len(file_ids)} file IDs: {file_ids}")
            for file_id in file_ids:
                file_record = await db.file_uploads.find_one({"id": file_id})
                if file_record:
                    print(f"DEBUG: Found file record for {file_id}: {file_record['original_filename']}")
                    file_info = {
                        "file_id": file_record["id"],
                        "filename": file_record["original_filename"],
                        "file_type": file_record["file_type"],
                        "file_size": file_record["file_size"],
                        "url": f"/api/files/{file_record['id']}"
                    }
                    file_attachments.append(file_info)
                    
                    # Check if this file is an image
                    if is_image_content(file_type=file_record["file_type"], filename=file_record["original_filename"]):
                        has_images = True
                    
                    # Try to read file content for AI analysis
                    file_path = Path(file_record["file_path"])
                    print(f"DEBUG: File path: {file_path}, exists: {file_path.exists()}")
                    if file_path.exists():
                        try:
                            # Handle different file types
                            if file_record["file_type"].startswith("text/") or file_record["original_filename"].endswith((".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".xml", ".csv")):
                                print(f"DEBUG: Reading text file: {file_record['original_filename']}")
                                # Read text files directly
                                async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = await f.read()
                                    print(f"DEBUG: Read {len(content)} characters from file")
                                    # Limit content size to prevent token overflow (max ~8000 characters)
                                    if len(content) > 8000:
                                        content = content[:8000] + "\n... [Content truncated due to length]"
                                    file_contents_for_ai.append({
                                        "filename": file_record["original_filename"],
                                        "type": "text",
                                        "content": content
                                    })
                            elif file_record["file_type"].startswith("image/"):
                                print(f"DEBUG: Processing image file: {file_record['original_filename']}")
                                # For images with vision model, provide the file path/URL
                                file_contents_for_ai.append({
                                    "filename": file_record["original_filename"],
                                    "type": "image",
                                    "content": f"[IMAGE FILE: {file_record['original_filename']} uploaded by user]",
                                    "file_url": f"{BACKEND_URL}/api/files/{file_record['id']}"
                                })
                            else:
                                print(f"DEBUG: Processing other file type: {file_record['original_filename']}")
                                # For other file types, provide basic info
                                file_contents_for_ai.append({
                                    "filename": file_record["original_filename"],
                                    "type": "other",
                                    "content": f"[FILE: {file_record['original_filename']} - {file_record['file_type']} - {file_record['file_size']} bytes. Note: I cannot directly read this file type, but I can discuss it based on your description or filename.]"
                                })
                        except Exception as e:
                            print(f"DEBUG: Error reading file {file_record['original_filename']}: {str(e)}")
                            # If file reading fails, still provide basic info
                            file_contents_for_ai.append({
                                "filename": file_record["original_filename"],
                                "type": "error",
                                "content": f"[FILE: {file_record['original_filename']} - Could not read content: {str(e)}]"
                            })
                else:
                    print(f"DEBUG: File record not found for ID: {file_id}")
            
        # Compute unified metadata defaults
        def is_video_url_fn(u: str) -> bool:
            return any(u.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.webm', '.mkv'])
        def is_image_url_fn(u: str) -> bool:
            return any(u.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'])

        first_image = None
        first_video = None
        for u in media_urls:
            if not first_image and is_image_url_fn(u):
                first_image = u
            if not first_video and is_video_url_fn(u):
                first_video = u
        # Load device settings for defaults
        device_for_defaults = await db.devices.find_one({"id": device_id})
        dev_settings = (device_for_defaults or {}).get('settings', {}) if device_for_defaults else {}

        req_camera_id = (message_data.camera_id if hasattr(message_data, 'camera_id') else None) or device_id
        req_mission_id = (message_data.mission_id if hasattr(message_data, 'mission_id') else None) or None
        req_title_user = (message_data.title if hasattr(message_data, 'title') else None) or 'User'
        req_body_user = (message_data.body if hasattr(message_data, 'body') else None) or message
        req_image_url = (message_data.image_url if hasattr(message_data, 'image_url') else None) or first_image
        req_video_url = (message_data.video_url if hasattr(message_data, 'video_url') else None) or first_video
        req_sound_id = (message_data.sound_id if hasattr(message_data, 'sound_id') else None) or dev_settings.get('default_sound_id')

        print(f"DEBUG: Final file_contents_for_ai: {len(file_contents_for_ai)} items")
        
        # Check media URLs for images
        if media_urls:
            print(f"DEBUG: Checking media URLs for images: {media_urls}")
            for url in media_urls:
                is_img = is_image_content(url=url)
                print(f"DEBUG: URL {url} is image: {is_img}")
                if is_img:
                    has_images = True
                    print("DEBUG: Found image URL, setting has_images=True")
                    break
        
        print(f"DEBUG: Final has_images value: {has_images}")
        
        # Check for camera prompt and role/instruction change commands before processing
        camera_prompt_result = await parse_camera_prompt_text(user_id, device_id, message)
        role_change_result = await parse_role_change_command(RoleChangeCommand(
            user_id=user_id,
            device_id=device_id,
            message=message
        ))
        
        # Store user message
        user_chat_msg = ChatMessage(
            user_id=user_id,
            device_id=device_id,
            message=message,
            sender=sender,
            media_urls=media_urls if media_urls else None,
            file_attachments=file_attachments if file_attachments else None,
            referenced_messages=referenced_messages,
            # unified metadata
            camera_id=req_camera_id,
            mission_id=req_mission_id,
            title=req_title_user,
            body=req_body_user,
            image_url=req_image_url,
            video_url=req_video_url,
            sound_id=req_sound_id
        )
        await db.chat_messages.insert_one(user_chat_msg.dict())
        
        # If camera prompt update was detected (preferred per user), return confirmation and skip AI
        if camera_prompt_result.get("success") and camera_prompt_result.get("settings_updated"):
            confirmation_msg = ChatMessage(
                user_id=user_id,
                device_id=device_id,
                message=camera_prompt_result["confirmation_message"],
                sender="system",
                ai_response=False
            )
            await db.chat_messages.insert_one(confirmation_msg.dict())
            
            return {
                "success": True,
                "message_id": user_chat_msg.id,
                "camera_prompt_changed": True,
                "ai_response": {
                    "message": camera_prompt_result["confirmation_message"],
                    "message_id": confirmation_msg.id,
                    "detected": "camera_prompt_change",
                    "new_instructions": camera_prompt_result.get("instructions")
                }
            }

        # If role change was detected, return confirmation and skip AI processing
        if role_change_result["success"] and role_change_result["settings_updated"]:
            confirmation_msg = ChatMessage(
                user_id=user_id,
                device_id=device_id,
                message=role_change_result["confirmation_message"],
                sender="ai",
                ai_response=True
            )
            await db.chat_messages.insert_one(confirmation_msg.dict())
            
            return {
                "success": True,
                "message_id": user_chat_msg.id,
                "role_changed": True,
                "ai_response": {
                    "message": role_change_result["confirmation_message"],
                    "message_id": confirmation_msg.id,
                    "detected": role_change_result["detected"],
                    "new_role": role_change_result.get("new_role"),
                    "new_instructions": role_change_result.get("new_instructions")
                }
            }
        
        # Get device info for AI personality
        device = await db.devices.find_one({"id": device_id})
        if not device:
            return {"success": False, "error": "Device not found"}
        
        device_type = device.get("type", "default")
        session_id = f"{user_id}_{device_id}"
        
        # Get chat history for context
        history = await get_chat_history(user_id, device_id)
        
        # Prepare context for AI if there are referenced messages
        context_messages = []
        if referenced_messages:
            for ref_msg_id in referenced_messages:
                ref_msg = await db.chat_messages.find_one({"id": ref_msg_id})
                if ref_msg:
                    context_messages.append({
                        "id": ref_msg["id"],
                        "message": ref_msg["message"],
                        "sender": ref_msg["sender"],
                        "timestamp": ref_msg.get("timestamp", ""),
                        "file_attachments": ref_msg.get("file_attachments", [])
                    })
        
        # Generate AI response with context
        try:
            ai_chat = await get_ai_chat_instance(device_type, session_id, has_images, user_id, device_id)
            
            # Build enhanced prompt with context
            enhanced_message = message
            if context_messages:
                context_text = "Previous messages being referenced:\n"
                for ctx_msg in context_messages:
                    context_text += f"- [{ctx_msg['sender']}]: {ctx_msg['message']}\n"
                    if ctx_msg.get('file_attachments'):
                        for attachment in ctx_msg['file_attachments']:
                            context_text += f"  📎 {attachment['filename']} ({attachment['file_type']})\n"
                    if ctx_msg.get('media_urls'):
                        for url in ctx_msg['media_urls']:
                            context_text += f"  🔗 {url}\n"
                enhanced_message = f"{context_text}\nCurrent message: {message}"
            
            # Create the user message with proper vision support
            if has_images:
                print("DEBUG: Using vision model with images detected")
                # Use vision-specific message creation
                vision_message, file_attachments_for_vision = await create_vision_message(
                    enhanced_message, 
                    file_contents_for_ai, 
                    media_urls
                )
                
                user_message = UserMessage(
                    text=vision_message,
                    file_contents=file_attachments_for_vision if file_attachments_for_vision else None
                )
            else:
                print("DEBUG: Using text-only model")
                # Standard text-only message
                text_content = enhanced_message
                
                # Include actual file contents for AI analysis (text files)
                if file_contents_for_ai:
                    file_content_text = "\n\nAttached files with content:\n"
                    for file_content in file_contents_for_ai:
                        file_content_text += f"\n📎 **{file_content['filename']}** ({file_content['type']} file):\n"
                        if file_content['type'] == 'text':
                            file_content_text += f"```\n{file_content['content']}\n```\n"
                        else:
                            file_content_text += f"{file_content['content']}\n"
                    text_content += file_content_text
                elif file_attachments:
                    # Fallback to just metadata if content reading failed
                    file_list = "\n\nAttached files:\n"
                    for attachment in file_attachments:
                        file_list += f"📎 {attachment['filename']} ({attachment['file_type']}, {attachment['file_size']} bytes)\n"
                    text_content += file_list
                
                # Include media URLs
                if media_urls:
                    media_content = "\n\nMedia URLs shared:\n"
                    for url in media_urls:
                        if is_image_content(url=url):
                            media_content += f"🖼️ Image: {url}\n"
                        elif any(url.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.webm', '.mkv']):
                            media_content += f"🎥 Video: {url}\n"
                        else:
                            media_content += f"🔗 Media: {url}\n"
                    text_content += media_content
                
                user_message = UserMessage(text=text_content)
            
            print(f"DEBUG: Sending message to AI with has_images={has_images}")
            ai_response = await ai_chat.send_message(user_message)
            
            # Build AI metadata
            ai_title = 'AI Analysis'
            ai_body = ai_response
            ai_image_url = first_image or req_image_url
            ai_video_url = first_video or req_video_url
            ai_sound_id = req_sound_id  # keep same sound by default
            
            # Store AI response as chat message
            ai_chat_msg = ChatMessage(
                user_id=user_id,
                device_id=device_id,
                message=ai_response,
                sender="ai",
                ai_response=True,
                camera_id=req_camera_id,
                mission_id=req_mission_id,
                title=ai_title,
                body=ai_body,
                image_url=ai_image_url,
                video_url=ai_video_url,
                sound_id=ai_sound_id
            )
            await db.chat_messages.insert_one(ai_chat_msg.dict())


            # Send push for significant AI response when images were involved
            try:
                if has_images:
                    low = (ai_response or '').lower()
                    significant = not any(kw in low for kw in [
                        'no_display', 'routine', 'no significant', 'nothing significant', 'no notable'
                    ])
                    if significant:
                        # Choose an image for the notification
                        notif_image = None
                        if media_urls:
                            # Prefer the first media url
                            notif_image = media_urls[0]
                        else:
                            # Look for first image attachment url
                            if file_attachments:
                                for att in file_attachments:
                                    if att.get('file_type', '').startswith('image/') and att.get('url'):
                                        notif_image = att['url']
                                        break
                        title = f"{device.get('name', device_id)}: Significant activity"
                        body = ai_response if len(ai_response) <= 180 else ai_response[:177] + '...'
                        push_req = PushNotificationRequest(
                            user_id=user_id,
                            device_id=device_id,
                            title=title,
                            body=body,
                            image=notif_image,
                            video_url=notif_image if notif_image and any(notif_image.lower().endswith(ext) for ext in [".mp4", ".mov", ".webm", ".mkv"]) else None,
                            data={
                                "user_id": user_id,
                                "device_id": device_id,
                                "type": "ai_analysis",
                                "analysis_type": "significant",
                                "message_id": ai_chat_msg.id
                            },
                            require_interaction=True
                        )
                        await send_push_notification(push_req)
            except Exception as e:
                logging.warning(f"Failed to send push for chat AI response: {e}")
            
            # Update chat history with both messages
            history.extend([
                {
                    "id": user_chat_msg.id,
                    "message": message,
                    "sender": sender,
                    "file_attachments": file_attachments,
                    "referenced_messages": referenced_messages,
                    "timestamp": user_chat_msg.timestamp.isoformat()
                },
                {
                    "id": ai_chat_msg.id,
                    "message": ai_response,
                    "sender": "ai",
                    "timestamp": ai_chat_msg.timestamp.isoformat()
                }
            ])
            
            # Store updated history
            await store_chat_history(user_id, device_id, history)
            
            # Send AI response via WebSocket if connected
            if user_id in manager.active_connections:
                await manager.send_personal_message({
                    "type": "ai_response",
                    "device_id": device_id,
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

# Direct Image Chat API
@api_router.post("/chat/image-direct")
async def send_image_directly_to_chat(user_id: str, image_chat: DirectImageChatCreate):
    """Send image(s) directly to chat with optional question.
    Supports base64 image_data, single image_url, or multiple media_urls (image URLs).
    AI decides whether to display in chat based on camera prompt and content."""
    
    try:
        device_id = image_chat.device_id
        
        # Get device info
        device = await db.devices.find_one({"id": device_id})
        if not device:
            return {"success": False, "error": "Device not found"}
        
        # Get current camera prompt for this device
        camera_prompt = await db.camera_prompts.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        # Build AI query
        device_type = device.get("type", "default")
        session_id = f"{user_id}_{device_id}_direct"
        
        # Use vision model for image analysis
        ai_chat = await get_ai_chat_instance(device_type, session_id, has_images=True, user_id=user_id, device_id=device_id)
        
        # Create enhanced prompt with camera instructions
        base_message = image_chat.question or "Analyze this image from the camera."
        
        if camera_prompt:
            enhanced_message = f"""
Camera Monitoring Instructions: {camera_prompt['prompt_text']}

User's current search focus: {camera_prompt['instructions']}

Image Analysis Request: {base_message}

Based on the camera monitoring instructions above, analyze this image and determine:
1. Does this image contain something relevant to what we're monitoring for?
2. If YES: Provide a detailed analysis with specific observations
3. If NO: Simply respond with 'NO_DISPLAY' and I will only log this for record keeping

Be thorough in your analysis when something relevant is detected.
"""
        else:
            enhanced_message = f"""
Analyze this security camera image: {base_message}

Determine if this shows anything significant that should be brought to the user's attention.
If this is routine/normal activity, respond with 'NO_DISPLAY'.
If this shows something noteworthy, provide detailed analysis.
"""
        
        # Convert base64 image or URL for vision analysis
        try:
            from emergentintegrations.llm.chat import ImageContent
            
            image_contents = []
            if image_chat.image_data:
                # Use provided base64 data
                image_contents.append(ImageContent(image_base64=image_chat.image_data))
            
            # Handle single image_url
            if image_chat.image_url:
                image_base64 = await download_image_as_base64(image_chat.image_url)
                if image_base64:
                    image_contents.append(ImageContent(image_base64=image_base64))
                else:
                    return {"success": False, "error": "Failed to download image from image_url"}
            
            # Handle multiple media_urls (image URLs)
            if image_chat.media_urls:
                for url in image_chat.media_urls:
                    if not url:
                        continue
                    image_base64 = await download_image_as_base64(url)
                    if image_base64:
                        image_contents.append(ImageContent(image_base64=image_base64))
                    else:
                        print(f"WARN: Could not download image from {url}")
            
            if not image_contents:
                return {"success": False, "error": "Provide at least one image via image_data, image_url, or media_urls"}
            
            user_message = UserMessage(
                text=enhanced_message,
                file_contents=image_contents
            )
            
            print("DEBUG: Sending direct image to AI with vision model")
            ai_response = await ai_chat.send_message(user_message)
            
            # Determine if should display in chat
            display_in_chat = not ai_response.strip().startswith('NO_DISPLAY')
            
            if not display_in_chat:
                ai_response = "Image logged for monitoring - no significant activity detected."
            
            # Store the direct image chat record
            direct_chat = DirectImageChat(
                user_id=user_id,
                device_id=device_id,
                image_data=image_chat.image_data or f"URL:{image_chat.image_url}",
                question=image_chat.question,
                ai_response=ai_response,
                display_in_chat=display_in_chat
            )
            
            # unified metadata for direct image flow
            req_camera_id = image_chat.camera_id or device_id
            req_mission_id = image_chat.mission_id or None
            req_title_user = image_chat.title or 'User'
            req_body_user = image_chat.body or (image_chat.question or '📸 Image(s) sent for analysis')
            req_image_url = image_chat.image_url or (image_chat.media_urls[0] if (image_chat.media_urls) else None)
            req_video_url = image_chat.video_url or None
            # device default sound
            dev = await db.devices.find_one({"id": device_id})
            req_sound_id = image_chat.sound_id or ((dev or {}).get('settings', {}) or {}).get('default_sound_id')

            await db.direct_image_chats.insert_one(direct_chat.dict())
            
            # If should display in chat, also add to regular chat messages
            if display_in_chat:
                # Add user message to chat
                media_urls_to_store = []
                if image_chat.image_url:
                    media_urls_to_store.append(image_chat.image_url)
                if image_chat.media_urls:
                    media_urls_to_store.extend([u for u in image_chat.media_urls if u])
                
                user_chat_msg = ChatMessage(
                    user_id=user_id,
                    device_id=device_id,
                    message=image_chat.question or "📸 Image(s) sent for analysis",
                    sender="user",
                    media_urls=media_urls_to_store if media_urls_to_store else None,
                    camera_id=req_camera_id,
                    mission_id=req_mission_id,
                    title=req_title_user,
                    body=req_body_user,
                    image_url=req_image_url,
                    video_url=req_video_url,
                    sound_id=req_sound_id
                )
                await db.chat_messages.insert_one(user_chat_msg.dict())
                
                # Build AI metadata
                ai_title = 'AI Analysis'
                ai_body = ai_response
                ai_image_url = req_image_url
                ai_video_url = req_video_url
                ai_sound_id = req_sound_id
                
                # Add AI response to chat
                ai_chat_msg = ChatMessage(
                    user_id=user_id,
                    device_id=device_id,
                    message=ai_response,
                    sender="ai",
                    ai_response=True,
                    camera_id=req_camera_id,
                    mission_id=req_mission_id,
                    title=ai_title,
                    body=ai_body,
                    image_url=ai_image_url,
                    video_url=ai_video_url,
                    sound_id=ai_sound_id
                )
                await db.chat_messages.insert_one(ai_chat_msg.dict())
                
                # If a video_url was provided, store as a notification so UI can show it as latest event
                if image_chat.video_url:
                    try:
                        video_notif = Notification(
                            user_id=user_id,
                            device_id=device_id,
                            type='media',
                            content='Event video',
                            media_url=image_chat.video_url
                        )
                        await db.notifications.insert_one(video_notif.dict())
                    except Exception as e:
                        logging.warning(f"Failed to store video_url notification: {e}")
                
                # Send push notification for significant activity
                try:
                  title = f"{device.get('name', device_id)}: Significant activity"
                  body = ai_response if len(ai_response) <= 180 else ai_response[:177] + '...'
                  # Prefer first provided URL for notification image if available
                  notif_image = None
                  if image_chat.image_url:
                      notif_image = image_chat.image_url
                  elif image_chat.media_urls and len(image_chat.media_urls) > 0:
                      notif_image = image_chat.media_urls[0]
                  push_req = PushNotificationRequest(
                      user_id=user_id,
                      device_id=device_id,
                      title=title,
                      body=body,
                      image=notif_image,
                      video_url=notif_image if notif_image and any(notif_image.lower().endswith(ext) for ext in [".mp4", ".mov", ".webm", ".mkv"]) else None,
                      data={
                          "user_id": user_id,
                          "device_id": device_id,
                          "type": "ai_analysis",
                          "analysis_type": "significant",
                          "message_id": ai_chat_msg.id,
                          "video_url": image_chat.video_url if image_chat.video_url else (image_chat.media_urls[0] if (image_chat.media_urls and any(image_chat.media_urls[0].lower().endswith(ext) for ext in [".mp4", ".mov", ".webm", ".mkv"])) else None)
                      },
                      require_interaction=True
                  )
                  await send_push_notification(push_req)
                except Exception as e:
                  logging.warning(f"Failed to send push notification for displayed_in_chat: {e}")
            
            return {
                "success": True,
                "displayed_in_chat": display_in_chat,
                "ai_response": ai_response,
                "message_id": direct_chat.id,
                "analysis_type": "significant" if display_in_chat else "routine"
            }
            
        except Exception as e:
            print(f"ERROR: Vision analysis failed: {e}")
            return {"success": False, "error": f"Vision analysis failed: {str(e)}"}
            
    except Exception as e:
        print(f"ERROR: Direct image chat failed: {e}")
        return {"success": False, "error": str(e)}

# Camera Prompt Management API
@api_router.get("/camera/prompt/{user_id}/{device_id}")
async def get_camera_prompt(user_id: str, device_id: str):
    """Get current camera monitoring prompt"""
    
    prompt = await db.camera_prompts.find_one({
        "user_id": user_id,
        "device_id": device_id
    })
    
    if not prompt:
        return {
            "user_id": user_id,
            "device_id": device_id,
            "prompt_text": "General security monitoring",
            "instructions": "Monitor for any unusual or suspicious activity",
            "is_default": True
        }
    
    return {
        "user_id": prompt["user_id"],
        "device_id": prompt["device_id"],
        "prompt_text": prompt["prompt_text"],
        "instructions": prompt["instructions"],
        "updated_at": prompt["updated_at"],
        "is_default": False
    }

@api_router.put("/camera/prompt/{user_id}/{device_id}")
async def update_camera_prompt(user_id: str, device_id: str, prompt_create: CameraPromptCreate):
    """Update camera monitoring prompt based on user instructions"""
    
    try:
        # Get device info for context
        device = await db.devices.find_one({"id": device_id})
        device_type = device.get("type", "camera") if device else "camera"
        device_name = device.get("name", device_id) if device else device_id
        
        # Generate appropriate prompt based on user instructions
        ai_generated_prompt = f"""
You are monitoring {device_name} ({device_type}) for the following:
{prompt_create.instructions}

When analyzing images from this camera, focus specifically on:
- Detecting: {prompt_create.instructions}
- Context: Security monitoring for {device_type}
- Alert level: Report anything relevant to the monitoring criteria
- Ignore: Routine activity not related to the search criteria

Provide detailed analysis when criteria are met, or respond with 'NO_DISPLAY' for routine activity.
"""
        
        # Check if prompt exists
        existing_prompt = await db.camera_prompts.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        if existing_prompt:
            # Update existing
            await db.camera_prompts.update_one(
                {"user_id": user_id, "device_id": device_id},
                {"$set": {
                    "prompt_text": ai_generated_prompt,
                    "instructions": prompt_create.instructions,
# Missions data models and APIs
                }}
            )
        else:
            # Create new
            new_prompt = CameraPrompt(
                user_id=user_id,
                device_id=device_id,
                prompt_text=ai_generated_prompt,
                instructions=prompt_create.instructions
            )
            await db.camera_prompts.insert_one(new_prompt.dict())
        
        return {
            "success": True,
            "message": "Camera monitoring prompt updated successfully",
            "prompt_text": ai_generated_prompt,
            "instructions": prompt_create.instructions
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

class MissionCreate(BaseModel):
    user_id: str
    mission_name: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    camera_ids: Optional[List[str]] = None

@api_router.post("/missions")
async def create_or_update_mission(m: MissionCreate):
    try:
        existing = await db.missions.find_one({"user_id": m.user_id, "mission_name": m.mission_name})
        payload = {
            "user_id": m.user_id,
            "mission_name": m.mission_name,
            "description": m.description,
            "settings": m.settings or {},
            "camera_ids": m.camera_ids or [],
            "updated_at": datetime.utcnow()
        }
        if existing:
            await db.missions.update_one({"_id": existing["_id"]}, {"$set": payload})
            doc = await db.missions.find_one({"_id": existing["_id"]})
        else:
            payload["created_at"] = datetime.utcnow()
            await db.missions.insert_one(payload)
            doc = await db.missions.find_one({"user_id": m.user_id, "mission_name": m.mission_name})
        doc["id"] = str(doc.get("_id")) if doc else None
        doc.pop("_id", None)
        return {"success": True, "mission": doc}
    except Exception as e:
        return {"success": False, "error": str(e)}

@api_router.get("/missions/{user_id}")
async def list_missions(user_id: str):
    items = []
    async for doc in db.missions.find({"user_id": user_id}).sort("mission_name", 1):
        doc["id"] = str(doc.get("_id"))
        doc.pop("_id", None)
        items.append(doc)
    return {"success": True, "missions": items}

class AssignCamerasRequest(BaseModel):
    camera_ids: List[str]

@api_router.put("/missions/assign-cameras")
async def assign_cameras_to_mission(user_id: str, mission_name: str, req: AssignCamerasRequest):
    try:
        res = await db.missions.update_one(
            {"user_id": user_id, "mission_name": mission_name},
            {"$set": {"camera_ids": req.camera_ids, "updated_at": datetime.utcnow()}},
            upsert=False
        )
        if res.matched_count == 0:
            return {"success": False, "error": "Mission not found"}
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@api_router.delete("/missions")
async def delete_mission(user_id: str, mission_name: str):
    try:
        await db.missions.delete_one({"user_id": user_id, "mission_name": mission_name})
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Mission chat fan-out and aggregated history
class MissionChatSend(BaseModel):
    mission_name: str
    message: str
    media_url: Optional[str] = None
    media_urls: Optional[List[str]] = None
    referenced_messages: Optional[List[str]] = None
    file_ids: Optional[List[str]] = None
    # Unified metadata (optional)
    camera_id: Optional[str] = None  # ignored for fan-out
    mission_id: Optional[str] = None  # stays null per user decision
    title: Optional[str] = None
    body: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    sound_id: Optional[str] = None

@api_router.post("/chat/mission/send")
async def mission_chat_send(user_id: str, payload: MissionChatSend):
    try:
        mission = await db.missions.find_one({"user_id": user_id, "mission_name": payload.mission_name})
        if not mission:
            return {"success": False, "error": "Mission not found"}
        camera_ids = mission.get("camera_ids", [])
        media_urls = payload.media_urls or ([payload.media_url] if payload.media_url else [])

        # Create mission-level summary message (uses device_id as synthetic value)
        mission_device_id = f"mission:{payload.mission_name}"
        summary = ChatMessage(
            user_id=user_id,
            device_id=mission_device_id,
            message=payload.message,
            sender="user",
            media_urls=media_urls if media_urls else None,
            camera_id=None,
            mission_id=None,
            title=payload.title or "User",
            body=payload.body or payload.message,
            image_url=payload.image_url or (media_urls[0] if media_urls else None),
            video_url=payload.video_url,
            sound_id=payload.sound_id
        )
        await db.chat_messages.insert_one(summary.dict())

        # Fan-out: create a user message per camera; AI generation is not triggered here to avoid recursion
        per_camera = []
        for cam in camera_ids:
            msg = ChatMessage(
                user_id=user_id,
                device_id=cam,
                message=payload.message,
                sender="user",
                media_urls=media_urls if media_urls else None,
                camera_id=cam,
                mission_id=None,
                title=payload.title or "User",
                body=payload.body or payload.message,
                image_url=payload.image_url or (media_urls[0] if media_urls else None),
                video_url=payload.video_url,
                sound_id=payload.sound_id
            )
            await db.chat_messages.insert_one(msg.dict())
            per_camera.append({"camera_id": cam, "message_id": msg.id})

        return {
            "success": True,
            "mission_name": payload.mission_name,
            "mission_message_id": summary.id,
            "fan_out_count": len(per_camera),
            "per_camera": per_camera
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@api_router.get("/chat/mission/{user_id}/{mission_name}")
async def mission_chat_history(user_id: str, mission_name: str, limit: int = 100):
    mission = await db.missions.find_one({"user_id": user_id, "mission_name": mission_name})
    if not mission:
        return {"success": False, "error": "Mission not found"}
    camera_ids = mission.get("camera_ids", [])
    ids = [f"mission:{mission_name}"] + camera_ids
    cursor = db.chat_messages.find({"user_id": user_id, "device_id": {"$in": ids}}).sort("timestamp", -1).limit(limit)
    items = [doc async for doc in cursor]
    # Normalize id and remove _id if exists
    for it in items:
        it.pop("_id", None)
    return {"success": True, "messages": list(reversed(items))}

# Global chat
class GlobalChatSend(BaseModel):
    message: str
    media_url: Optional[str] = None
    media_urls: Optional[List[str]] = None
    referenced_messages: Optional[List[str]] = None
    file_ids: Optional[List[str]] = None
    title: Optional[str] = None
    body: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    sound_id: Optional[str] = None

@api_router.post("/chat/global/send")
async def global_chat_send(user_id: str, payload: GlobalChatSend):
    try:
        media_urls = payload.media_urls or ([payload.media_url] if payload.media_url else [])
        msg = ChatMessage(
            user_id=user_id,
            device_id="global",
            message=payload.message,
            sender="user",
            media_urls=media_urls if media_urls else None,
            camera_id=None,
            mission_id=None,
            title=payload.title or "User",
            body=payload.body or payload.message,
            image_url=payload.image_url or (media_urls[0] if media_urls else None),
            video_url=payload.video_url,
            sound_id=payload.sound_id
        )
        await db.chat_messages.insert_one(msg.dict())
        return {"success": True, "message_id": msg.id}
    except Exception as e:
        return {"success": False, "error": str(e)}

@api_router.get("/chat/global/{user_id}")
async def global_chat_history(user_id: str, limit: int = 100):
    cursor = db.chat_messages.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    items = [doc async for doc in cursor]
    for it in items:
        it.pop("_id", None)
    return {"success": True, "messages": list(reversed(items))}

async def parse_camera_prompt_text(user_id: str, device_id: str, message: str) -> Dict[str, Any]:
    """Detect natural language instructions to update camera prompt from a chat message.
    Returns a dict with keys: success, settings_updated, instructions, prompt_text, confirmation_message
    """
    import re

    text = (message or '').strip()
    lowered = text.lower()

    if not text:
        return {"success": False, "settings_updated": False}

    patterns = [
        r"monitor for\s+(.+)$",
        r"update camera prompt to\s+(.+)$",
        r"update prompt to\s+(.+)$",
        r"please monitor\s+(.+)$",
        r"look for\s+(.+)$",
        r"watch for\s+(.+)$",
    ]

    instructions = None
    for p in patterns:
        m = re.search(p, lowered)
        if m:
            instructions = m.group(1).strip()
            break

    if not instructions:
        # Fallback: if intent words exist, use the whole message as instructions
        if any(kw in lowered for kw in ["prompt", "monitor", "watch for", "look for"]):
            instructions = text

    if not instructions:
        return {"success": True, "settings_updated": False}

    # Apply update
    update_result = await update_camera_prompt(user_id, device_id, CameraPromptCreate(instructions=instructions))
    if not update_result.get("success"):
        return {"success": False, "settings_updated": False, "error": update_result.get("error", "Failed to update camera prompt")}

    confirmation = f"Camera monitoring updated. I will now monitor for: {instructions}"

    # Store a system confirmation message in chat
    try:
        system_msg = ChatMessage(
            user_id=user_id,
            device_id=device_id,
            message=confirmation,
            sender="system",
            ai_response=False
        )
        await db.chat_messages.insert_one(system_msg.dict())
        message_id = system_msg.id
    except Exception as e:
        logging.error(f"Failed to store camera prompt confirmation message: {e}")
        message_id = None

    return {
        "success": True,
        "settings_updated": True,
        "instructions": instructions,
        "prompt_text": update_result.get("prompt_text"),
        "confirmation_message": confirmation,
        "message_id": message_id
    }

@api_router.post("/camera/prompt/parse-command")
async def camera_prompt_parse_command(cmd: CameraPromptCommand):
    result = await parse_camera_prompt_text(cmd.user_id, cmd.device_id, cmd.message)
    return result

async def camera_prompt_fix_from_feedback(command: CameraPromptFixCommand) -> Dict[str, Any]:
    """Update camera monitoring prompt based on corrective feedback from user"""
    
    try:
        user_id = command.user_id
        device_id = command.device_id
        feedback_message = command.message
        
        # Get current camera prompt
        current_prompt = await db.camera_prompts.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        if not current_prompt:
            return {"success": False, "error": "No existing camera prompt found to update"}
        
        # Get device info for context
        device = await db.devices.find_one({"id": device_id})
        device_type = device.get("type", "camera") if device else "camera"
        device_name = device.get("name", device_id) if device else device_id
        
        # Get referenced AI message context if provided
        context_info = ""
        if command.referenced_messages:
            for msg_id in command.referenced_messages:
                ref_msg = await db.chat_messages.find_one({"id": msg_id})
                if ref_msg and ref_msg.get("sender") == "ai":
                    context_info = f"Previous AI analysis: {ref_msg['message'][:200]}..."
                    break
        
        # Use AI to analyze the feedback and update instructions
        session_id = f"prompt_fix_{user_id}_{device_id}"
        ai_chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=session_id,
            system_message="You are an AI assistant that helps refine camera monitoring instructions based on user feedback."
        ).with_model("openai", "gpt-4o-mini")
        
        analysis_prompt = f"""
Current camera monitoring instructions: {current_prompt['instructions']}

User feedback about the monitoring: {feedback_message}

{context_info}

Based on this corrective feedback, provide updated monitoring instructions that address the user's concerns. The instructions should be:
1. Clear and specific
2. Address the issues mentioned in the feedback
3. Maintain the core monitoring purpose
4. Be concise (1-2 sentences)

Respond with only the updated instructions, nothing else.
"""
        
        user_message = UserMessage(text=analysis_prompt)
        updated_instructions = await ai_chat.send_message(user_message)
        updated_instructions = updated_instructions.strip()
        
        # Update the camera prompt with new instructions
        update_result = await update_camera_prompt(user_id, device_id, CameraPromptCreate(instructions=updated_instructions))
        
        if not update_result.get("success"):
            return {"success": False, "error": "Failed to update camera prompt"}
        
        return {
            "success": True,
            "instructions": updated_instructions,
            "prompt_text": update_result.get("prompt_text"),
            "confirmation_message": f"Updated monitoring based on your feedback. New focus: {updated_instructions}"
        }
        
    except Exception as e:
        logging.error(f"Failed to process camera prompt fix: {e}")
        return {"success": False, "error": str(e)}

@api_router.post("/camera/prompt/fix-from-feedback")
async def camera_prompt_fix_endpoint(command: CameraPromptFixCommand):
    """API endpoint to fix camera prompt based on user feedback"""
    result = await camera_prompt_fix_from_feedback(command)
    return result

# Chat Settings Management APIs
@api_router.get("/chat/settings/{user_id}/{device_id}")
async def get_chat_settings(user_id: str, device_id: str):
    """Get current chat settings for a user-device combination"""
    
    settings = await db.chat_settings.find_one({
        "user_id": user_id, 
        "device_id": device_id
    })
    
    if not settings:
        # Return default settings based on device type
        device = await db.devices.find_one({"id": device_id})
        device_type = device.get("type", "default") if device else "default"
        
        default_personality = AI_PERSONALITIES.get(device_type, AI_PERSONALITIES["default"])
        
        return {
            "user_id": user_id,
            "device_id": device_id,
            "role_name": f"{device_type.title()} Assistant",
            "system_message": default_personality["system_message"],
            "instructions": None,
            "model": default_personality["model"],
            "is_default": True
        }
    
    return {
        "user_id": settings["user_id"],
        "device_id": settings["device_id"], 
        "role_name": settings["role_name"],
        "system_message": settings["system_message"],
        "instructions": settings.get("instructions"),
        "model": settings["model"],
        "is_default": False,
        "updated_at": settings["updated_at"]
    }

@api_router.put("/chat/settings/{user_id}/{device_id}")
async def update_chat_settings(user_id: str, device_id: str, settings_update: ChatSettingsUpdate):
    """Update chat settings for a user-device combination"""
    
    # Check if settings exist
    existing_settings = await db.chat_settings.find_one({
        "user_id": user_id,
        "device_id": device_id
    })
    
    if existing_settings:
        # Update existing settings
        update_data = {k: v for k, v in settings_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        await db.chat_settings.update_one(
            {"user_id": user_id, "device_id": device_id},
            {"$set": update_data}
        )
        
        updated_settings = await db.chat_settings.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
    else:
        # Create new settings
        device = await db.devices.find_one({"id": device_id})
        device_type = device.get("type", "default") if device else "default"
        default_personality = AI_PERSONALITIES.get(device_type, AI_PERSONALITIES["default"])
        
        new_settings = ChatSettings(
            user_id=user_id,
            device_id=device_id,
            role_name=settings_update.role_name or f"{device_type.title()} Assistant",
            system_message=settings_update.system_message or default_personality["system_message"],
            instructions=settings_update.instructions,
            model=settings_update.model or default_personality["model"]
        )
        
        await db.chat_settings.insert_one(new_settings.dict())
        updated_settings = new_settings.dict()
    
    return {
        "success": True,
        "message": "Chat settings updated successfully",
        "settings": {
            "role_name": updated_settings["role_name"],
            "system_message": updated_settings["system_message"],
            "instructions": updated_settings.get("instructions"),
            "model": updated_settings["model"]
        }
    }

@api_router.post("/chat/settings/parse-command")
async def parse_role_change_command(command: RoleChangeCommand):
    """Parse natural language commands to change AI role/instructions"""
    
    message = command.message.lower()
    user_id = command.user_id
    device_id = command.device_id

    # If user is giving corrective feedback about analysis, route to prompt-fix flow
    if any(k in message for k in ["wrong", "mistake", "incorrect", "should have", "shouldn't", "misclassified", "false positive", "false alarm", "it was"]) and len(message.split()) > 3:
        # Try to use the last AI message as context automatically
        last_ai = await db.chat_messages.find({"user_id": user_id, "device_id": device_id, "sender": "ai"}).sort("timestamp", -1).limit(1).to_list(1)
        last_ai_id = last_ai[0]["id"] if last_ai else None
        from fastapi.encoders import jsonable_encoder
        fix_payload = CameraPromptFixCommand(user_id=user_id, device_id=device_id, message=command.message, referenced_messages=[last_ai_id] if last_ai_id else None)
        fix_result = await camera_prompt_fix_from_feedback(fix_payload)
        if fix_result.get("success"):
            return {
                "success": True,
                "detected": "prompt_fix",
                "confirmation_message": f"Updated monitoring based on your feedback. New focus: {fix_result['instructions']}",
                "settings_updated": True,
                "new_instructions": fix_result.get("instructions")
            }

    # Patterns for role changes
    role_patterns = [
        r"change your role to (.+)",
        r"act as (.+)",
        r"you are now (.+)",
        r"become (.+)",
        r"your new role is (.+)",
        r"switch to (.+) mode",
        r"be a (.+)"
    ]
    
    # Patterns for instruction changes
    instruction_patterns = [
        r"change your instructions to (.+)",
        r"your new instructions are (.+)",
        r"follow these instructions: (.+)",
        r"new instructions: (.+)",
        r"update your instructions to (.+)"
    ]
    
    import re
    
    # Check for role changes
    for pattern in role_patterns:
        match = re.search(pattern, message)
        if match:
            new_role = match.group(1).strip()
            
            # Create appropriate system message for the role
            system_message = f"You are {new_role}. Be helpful and respond according to this role in all your interactions."
            
            # Update settings
            await update_chat_settings(user_id, device_id, ChatSettingsUpdate(
                role_name=new_role.title(),
                system_message=system_message
            ))
            
            return {
                "success": True,
                "detected": "role_change",
                "new_role": new_role.title(),
                "confirmation_message": f"I have changed my role to {new_role}. How can I help you in this new capacity?",
                "settings_updated": True
            }
    
    # Check for instruction changes
    for pattern in instruction_patterns:
        match = re.search(pattern, message)
        if match:
            new_instructions = match.group(1).strip()
            
            # Update settings
            await update_chat_settings(user_id, device_id, ChatSettingsUpdate(
                instructions=new_instructions,
                system_message=f"You are an AI assistant. Follow these specific instructions: {new_instructions}"
            ))
            
            return {
                "success": True,
                "detected": "instruction_change", 
                "new_instructions": new_instructions,
                "confirmation_message": f"I have updated my instructions. I will now: {new_instructions}",
                "settings_updated": True
            }
    
    # Check for reset commands
    reset_patterns = [
        r"reset your role",
        r"go back to default",
        r"reset to original",
        r"default mode",
        r"reset instructions"
    ]
    
    for pattern in reset_patterns:
        if re.search(pattern, message):
            # Get device type for default settings
            device = await db.devices.find_one({"id": device_id})
            device_type = device.get("type", "default") if device else "default"
            default_personality = AI_PERSONALITIES.get(device_type, AI_PERSONALITIES["default"])
            
            # Reset to default
            await update_chat_settings(user_id, device_id, ChatSettingsUpdate(
                role_name=f"{device_type.title()} Assistant",
                system_message=default_personality["system_message"],
                instructions=None,
                model=default_personality["model"]
            ))
            
            return {
                "success": True,
                "detected": "reset",
                "confirmation_message": f"I have reset to my default {device_type} assistant role.",
                "settings_updated": True
            }
    
    return {
        "success": False,
        "detected": "none",
        "message": "No role or instruction change command detected."
    }

# File Upload Endpoints
@api_router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    device_id: str = Form(None),
    message_id: str = Form(None)
):
    """Upload a file and return file information"""
    
    # Check file size (100MB limit)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes
    
    # Read file content to check size
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is 100MB, got {file_size / (1024*1024):.2f}MB")
    
    # Generate unique filename to avoid conflicts
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create user-specific upload directory
    user_upload_dir = UPLOADS_DIR / user_id
    user_upload_dir.mkdir(exist_ok=True)
    
    file_path = user_upload_dir / unique_filename
    
    try:
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create file record
        file_upload = FileUpload(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_type=file.content_type or 'application/octet-stream',
            file_size=file_size,
            user_id=user_id,
            device_id=device_id,
            message_id=message_id
        )
        
        # Store file info in database
        await db.file_uploads.insert_one(file_upload.dict())
        
        return {
            "success": True,
            "file_id": file_upload.id,
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_type": file.content_type,
            "file_size": file_size,
            "url": f"/api/files/{file_upload.id}"
        }
        
    except Exception as e:
        # Clean up file if database operation fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@api_router.get("/files/{file_id}")
async def get_file(file_id: str):
    """Serve uploaded file"""
    
    # Find file record
    file_record = await db.file_uploads.find_one({"id": file_id})
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(file_record["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=file_record["original_filename"],
        media_type=file_record["file_type"]
    )

@api_router.get("/files/user/{user_id}")
async def get_user_files(user_id: str):
    """Get all files uploaded by a user"""
    
    files = await db.file_uploads.find({"user_id": user_id}).to_list(1000)
    return [{
        "file_id": file_record["id"],
        "filename": file_record["original_filename"],
        "file_type": file_record["file_type"],
        "file_size": file_record["file_size"],
        "uploaded_at": file_record["uploaded_at"],
        "url": f"/api/files/{file_record['id']}"
    } for file_record in files]

@api_router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete an uploaded file"""
    
    # Find file record
    file_record = await db.file_uploads.find_one({"id": file_id})
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete file from disk
    file_path = Path(file_record["file_path"])
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    await db.file_uploads.delete_one({"id": file_id})
    
    return {"success": True, "message": "File deleted successfully"}


# Generated sound endpoints
import io
import struct
import math
import wave

@api_router.get("/sounds/{sound_id}")
async def get_sound(sound_id: str, duration: float = 0.35):
    """Generate a simple WAV tone for notification sounds.
    sound_id: one of ['significant','alert','routine']
    """
    sound_map = {
        'significant': 880.0,  # A5
        'alert': 660.0,        # E5
        'routine': 440.0       # A4
    }
    freq = sound_map.get(sound_id.lower(), 440.0)

    sample_rate = 44100
    n_samples = int(duration * sample_rate)
    volume = 0.5

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            # Simple sine wave
            val = int(volume * 32767 * math.sin(2 * math.pi * freq * t))
            wf.writeframes(struct.pack('<h', val))

    buffer.seek(0)
    headers = {
        'Content-Disposition': f'inline; filename="{sound_id}.wav"'
    }
    return StreamingResponse(buffer, media_type='audio/wav', headers=headers)

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