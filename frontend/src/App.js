import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { 
  MessageCircle, 
  Send, 
  Image, 
  Video,
  Bell,
  Settings,
  Home,
  ChevronLeft,
  Plus,
  MoreVertical,
  BellRing,
  Paperclip,
  X,
  Reply,
  Check,
  File
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

// Demo user ID - in real app this would come from authentication
const USER_ID = 'demo-user-123';

// VAPID public key for push notifications
const VAPID_PUBLIC_KEY = process.env.REACT_APP_VAPID_PUBLIC_KEY || 'BA819SOie93Pet6HTr4Iycak8THUOzAag7rRqO3iKx1dXKfWuBMoj-cuQTr65zPe8VSaewTFxcTgQx3rZHvHdOI';

// Utility function to convert VAPID key
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

// Utility Components
const LoadingSpinner = () => (
  <div className="flex justify-center items-center p-4">
    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
  </div>
);

const MediaViewer = ({ url, type }) => {
  if (!url) return null;
  
  if (type === 'image' || url.match(/\.(jpg|jpeg|png|gif|webp)$/i)) {
    return (
      <div className="max-w-full rounded-lg overflow-hidden">
        <img 
          src={url} 
          alt="Media content" 
          className="w-full h-auto max-h-64 object-cover"
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
      </div>
    );
  }
  
  if (type === 'video' || url.match(/\.(mp4|webm|ogg|mov)$/i)) {
    return (
      <div className="max-w-full rounded-lg overflow-hidden">
        <video 
          controls 
          className="w-full h-auto max-h-64"
          preload="metadata"
        >
          <source src={url} />
          Your browser does not support the video tag.
        </video>
      </div>
    );
  }
  
  // Fallback for unknown media types
  return (
    <a 
      href={url} 
      target="_blank" 
      rel="noopener noreferrer"
      className="text-blue-500 underline text-sm"
    >
      View Media
    </a>
  );
};

// Device List Component
const DeviceList = ({ devices, onSelectDevice, selectedDevice }) => {
  return (
    <div className="h-full bg-white">
      <div className="p-4 border-b bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-800">My Devices</h2>
      </div>
      <div className="overflow-y-auto">
        {devices.map(device => (
          <div
            key={device.id}
            onClick={() => onSelectDevice(device)}
            className={`p-4 border-b cursor-pointer transition-colors ${
              selectedDevice?.id === device.id 
                ? 'bg-blue-50 border-blue-200' 
                : 'hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${
                device.status === 'online' ? 'bg-green-500' : 'bg-gray-400'
              }`}></div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-800">{device.name}</h3>
                <p className="text-sm text-gray-500 capitalize">{device.type}</p>
              </div>
              <MessageCircle size={18} className="text-gray-400" />
            </div>
          </div>
        ))}
        {devices.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <MessageCircle size={48} className="mx-auto mb-4 text-gray-300" />
            <p>No devices found</p>
            <p className="text-sm mt-2">Add devices to start chatting</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Chat Interface Component
const ChatInterface = ({ device, messages, onSendMessage, isConnected, deviceNotifications, onMarkNotificationRead }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [referencedMessages, setReferencedMessages] = useState([]);
  const [multiSelectMode, setMultiSelectMode] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, deviceNotifications]);

  const handleSend = async () => {
    if ((inputMessage.trim() || selectedFiles.length > 0) && device) {
      await onSendMessage(device.id, inputMessage.trim(), selectedFiles, referencedMessages);
      setInputMessage('');
      setSelectedFiles([]);
      setReferencedMessages([]);
      setMultiSelectMode(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(prev => [...prev, ...files]);
    e.target.value = ''; // Reset input
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const toggleMessageReference = (messageId) => {
    if (multiSelectMode) {
      setReferencedMessages(prev => 
        prev.includes(messageId) 
          ? prev.filter(id => id !== messageId)
          : [...prev, messageId]
      );
    } else {
      setReferencedMessages([messageId]);
    }
  };

  const clearReferences = () => {
    setReferencedMessages([]);
    setMultiSelectMode(false);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (file) => {
    if (file.type.startsWith('image/')) return <Image size={16} />;
    if (file.type.startsWith('video/')) return <Video size={16} />;
    return <File size={16} />;
  };

  if (!device) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <MessageCircle size={48} className="mx-auto mb-4 text-gray-300" />
          <p>Select a device to start chatting</p>
        </div>
      </div>
    );
  }

  // Combine messages and notifications for this device, sorted by timestamp
  const allItems = [
    ...messages.map(msg => ({ ...msg, type: 'message' })),
    ...deviceNotifications.map(notif => ({ ...notif, type: 'notification' }))
  ].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b bg-gray-50 flex items-center space-x-3">
        <div className={`w-3 h-3 rounded-full ${
          device.status === 'online' ? 'bg-green-500' : 'bg-gray-400'
        }`}></div>
        <div className="flex-1">
          <h3 className="font-medium text-gray-800">{device.name}</h3>
          <p className="text-sm text-gray-500">
            {isConnected ? 'Connected' : 'Disconnected'} • {device.type}
          </p>
        </div>
        <MoreVertical size={20} className="text-gray-400" />
      </div>

      {/* Messages & Notifications */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {allItems.map(item => (
          <div key={`${item.type}-${item.id}`}>
            {item.type === 'message' ? (
              <div className={`flex ${item.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div 
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg space-y-2 relative cursor-pointer ${
                    referencedMessages.includes(item.id) 
                      ? 'ring-2 ring-blue-400' 
                      : ''
                  } ${
                    item.sender === 'user'
                      ? 'bg-blue-500 text-white'
                      : item.sender === 'ai'
                      ? 'bg-green-100 text-green-800 border border-green-200'
                      : item.sender === 'system'
                      ? 'bg-red-100 text-red-800 border border-red-200'
                      : 'bg-gray-200 text-gray-800'
                  }`}
                  onClick={() => toggleMessageReference(item.id)}
                >
                  {/* Reference indicator */}
                  {referencedMessages.includes(item.id) && (
                    <div className="absolute -top-1 -right-1 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
                      <Check size={10} className="text-white" />
                    </div>
                  )}
                  
                  {/* Reply indicator for quick reference mode */}
                  {!multiSelectMode && referencedMessages.includes(item.id) && (
                    <div className="absolute -top-2 -left-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                      <Reply size={12} className="text-white" />
                    </div>
                  )}

                  {item.sender === 'ai' && (
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-xs font-medium text-green-700">AI Assistant</span>
                    </div>
                  )}
                  {item.sender === 'system' && (
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                      <span className="text-xs font-medium text-red-700">System</span>
                    </div>
                  )}
                  
                  {/* Referenced messages preview */}
                  {item.referenced_messages && item.referenced_messages.length > 0 && (
                    <div className="mb-2 p-2 bg-black bg-opacity-10 rounded text-xs">
                      <Reply size={12} className="inline mr-1" />
                      Replying to {item.referenced_messages.length} message{item.referenced_messages.length > 1 ? 's' : ''}
                    </div>
                  )}
                  
                  <p className="text-sm">{item.message}</p>
                  
                  {/* File attachments */}
                  {item.file_attachments && item.file_attachments.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {item.file_attachments.map((file, idx) => (
                        <div key={idx} className="flex items-center space-x-2 p-2 bg-black bg-opacity-10 rounded text-xs">
                          {file.file_type.startsWith('image/') ? <Image size={12} /> :
                           file.file_type.startsWith('video/') ? <Video size={12} /> :
                           <File size={12} />}
                          <span>{file.filename}</span>
                          <span className="text-opacity-70">({formatFileSize(file.file_size)})</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {item.media_url && (
                    <MediaViewer url={item.media_url} />
                  )}
                  <p className={`text-xs ${
                    item.sender === 'user' ? 'text-blue-100' : 
                    item.sender === 'ai' ? 'text-green-600' :
                    item.sender === 'system' ? 'text-red-600' :
                    'text-gray-500'
                  }`}>
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex justify-center">
                <div 
                  className={`max-w-md px-4 py-3 rounded-lg border-l-4 cursor-pointer transition-colors ${
                    item.read 
                      ? 'bg-gray-50 border-gray-300' 
                      : 'bg-blue-50 border-blue-400'
                  }`}
                  onClick={() => !item.read && onMarkNotificationRead(item.id)}
                >
                  <div className="flex items-start space-x-3">
                    <Bell size={16} className={item.read ? 'text-gray-400' : 'text-blue-500'} />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-800">
                        Device Notification
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {item.content}
                      </p>
                      {item.media_url && (
                        <div className="mt-2">
                          <MediaViewer url={item.media_url} />
                        </div>
                      )}
                      <p className="text-xs text-gray-500 mt-2">
                        {new Date(item.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t bg-white">
        {/* Referenced messages preview */}
        {referencedMessages.length > 0 && (
          <div className="px-4 py-2 bg-blue-50 border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Reply size={14} className="text-blue-600" />
                <span className="text-sm text-blue-700">
                  {multiSelectMode ? 
                    `${referencedMessages.length} messages selected` : 
                    'Replying to message'}
                </span>
              </div>
              <button
                onClick={clearReferences}
                className="text-blue-600 hover:text-blue-800"
              >
                <X size={16} />
              </button>
            </div>
            <div className="flex items-center space-x-2 mt-1">
              <label className="flex items-center space-x-2 text-xs">
                <input
                  type="checkbox"
                  checked={multiSelectMode}
                  onChange={(e) => setMultiSelectMode(e.target.checked)}
                  className="w-3 h-3"
                />
                <span>Multi-select mode</span>
              </label>
            </div>
          </div>
        )}
        
        {/* File attachments preview */}
        {selectedFiles.length > 0 && (
          <div className="px-4 py-2 bg-gray-50 border-b">
            <div className="flex items-center space-x-2 mb-2">
              <Paperclip size={14} className="text-gray-600" />
              <span className="text-sm text-gray-700">{selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''} selected</span>
            </div>
            <div className="space-y-2">
              {selectedFiles.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-white rounded border">
                  <div className="flex items-center space-x-2">
                    {getFileIcon(file)}
                    <span className="text-sm truncate max-w-48">{file.name}</span>
                    <span className="text-xs text-gray-500">({formatFileSize(file.size)})</span>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="p-4">
          <div className="flex space-x-2">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              multiple
              className="hidden"
              accept="*/*"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-3 py-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
              title="Attach files"
            >
              <Paperclip size={18} />
            </button>
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSend}
              disabled={!inputMessage.trim() && selectedFiles.length === 0}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              <Send size={18} />
            </button>
          </div>
          {!isConnected && (
            <div className="text-xs text-gray-500 mt-2 text-center">
              💬 Chat via HTTP (WebSocket disconnected)
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Notifications Component
const NotificationsList = ({ notifications, devices, onMarkRead }) => {
  if (notifications.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <Bell size={48} className="mx-auto mb-4 text-gray-300" />
        <p>No notifications</p>
      </div>
    );
  }

  // Create device lookup map
  const deviceMap = devices.reduce((acc, device) => {
    acc[device.id] = device;
    return acc;
  }, {});

  return (
    <div className="space-y-2 p-4">
      {notifications.map(notification => {
        const device = deviceMap[notification.device_id];
        const deviceName = device ? device.name : notification.device_id;
        
        return (
          <div
            key={notification.id}
            className={`p-4 rounded-lg border ${
              notification.read ? 'bg-gray-50' : 'bg-blue-50 border-blue-200'
            }`}
            onClick={() => !notification.read && onMarkRead(notification.id)}
          >
            <div className="flex items-start space-x-3">
              <div className={`w-2 h-2 rounded-full mt-2 ${
                notification.read ? 'bg-gray-400' : 'bg-blue-500'
              }`}></div>
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <p className="text-sm font-medium text-gray-800">
                    {deviceName}
                  </p>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    device?.status === 'online' 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-gray-100 text-gray-700'
                  }`}>
                    {device?.type || 'device'}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {notification.content}
                </p>
                {notification.media_url && (
                  <div className="mt-2">
                    <MediaViewer url={notification.media_url} />
                  </div>
                )}
                <p className="text-xs text-gray-500 mt-2">
                  {new Date(notification.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Main App Component
const App = () => {
  const [currentView, setCurrentView] = useState('devices');
  const [devices, setDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [messages, setMessages] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [deviceNotifications, setDeviceNotifications] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pushSupported, setPushSupported] = useState(false);
  const [pushSubscribed, setPushSubscribed] = useState(false);
  const wsRef = useRef(null);

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    loadInitialData();
    checkPushSupport();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(`${WS_URL}/ws/${USER_ID}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        
        // Send ping periodically to keep connection alive
        const ping = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
        
        ws.pingInterval = ping;
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        if (ws.pingInterval) {
          clearInterval(ws.pingInterval);
        }
        
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setTimeout(connectWebSocket, 5000);
    }
  };

  const handleWebSocketMessage = (data) => {
    if (data.type === 'pong') return;
    
    if (data.type === 'ai_response' && selectedDevice?.id === data.device_id) {
      // Add AI response to current chat
      const aiMessage = {
        id: data.message_id || Date.now().toString(),
        user_id: USER_ID,
        device_id: data.device_id,
        message: data.message,
        sender: 'ai',
        ai_response: true,
        timestamp: data.timestamp || new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);
    }
    
    if (data.type === 'ai_error' && selectedDevice?.id === data.device_id) {
      // Show AI error message
      const errorMessage = {
        id: Date.now().toString(),
        user_id: USER_ID,
        device_id: data.device_id,
        message: `AI Assistant Error: ${data.error}`,
        sender: 'system',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
    
    // Handle different notification types
    if (data.type === 'message' && selectedDevice?.id === data.device_id) {
      // Add to current chat if viewing the device
      const newMessage = {
        id: Date.now().toString(),
        user_id: USER_ID,
        device_id: data.device_id,
        message: data.content,
        media_url: data.media_url,
        sender: 'device',
        timestamp: data.timestamp || new Date().toISOString()
      };
      setMessages(prev => [...prev, newMessage]);
    }
    
    // Always add to notifications
    const notification = {
      id: Date.now().toString(),
      user_id: USER_ID,
      device_id: data.device_id,
      type: data.type,
      content: data.content,
      media_url: data.media_url,
      read: false,
      timestamp: data.timestamp || new Date().toISOString()
    };
    setNotifications(prev => [notification, ...prev]);
  };

  const loadInitialData = async () => {
    try {
      console.log('Starting initial data load...');
      setLoading(true);
      
      // Add timeout to prevent infinite loading
      const loadPromises = [
        loadDevices(),
        loadNotifications()
      ];
      
      // Use Promise.allSettled to ensure we handle all outcomes
      const results = await Promise.allSettled(loadPromises);
      
      // Log results for debugging
      results.forEach((result, index) => {
        const taskName = index === 0 ? 'loadDevices' : 'loadNotifications';
        if (result.status === 'rejected') {
          console.error(`${taskName} failed:`, result.reason);
        } else {
          console.log(`${taskName} completed successfully`);
        }
      });
      
      console.log('Initial data load completed');
    } catch (error) {
      console.error('Failed to load initial data:', error);
    } finally {
      // Always set loading to false, regardless of API success/failure
      console.log('Setting loading to false');
      setLoading(false);
    }
  };

  const loadDevices = async () => {
    try {
      console.log('Loading devices...');
      const response = await axios.get(`${API}/devices/${USER_ID}`, { 
        timeout: 10000 // 10 second timeout
      });
      console.log('Devices loaded:', response.data.length, 'devices');
      setDevices(response.data);
    } catch (error) {
      console.error('Failed to load devices:', error);
      // Set empty devices array on error to allow app to continue
      setDevices([]);
    }
  };

  const loadNotifications = async () => {
    try {
      console.log('Loading notifications...');
      const response = await axios.get(`${API}/notifications/${USER_ID}`, { 
        timeout: 10000 // 10 second timeout
      });
      console.log('Notifications loaded:', response.data.length, 'notifications');
      setNotifications(response.data);
    } catch (error) {
      console.error('Failed to load notifications:', error);
      // Set empty notifications array on error to allow app to continue
      setNotifications([]);
    }
  };

  const loadChatMessages = async (deviceId) => {
    try {
      const response = await axios.get(`${API}/chat/${USER_ID}/${deviceId}`);
      setMessages(response.data);
      
      // Also load device-specific notifications
      const notifResponse = await axios.get(`${API}/notifications/${USER_ID}/device/${deviceId}`);
      setDeviceNotifications(notifResponse.data);
    } catch (error) {
      console.error('Failed to load chat messages:', error);
    }
  };

  const handleSelectDevice = (device) => {
    setSelectedDevice(device);
    setCurrentView('chat');
    loadChatMessages(device.id);
  };

  const handleSendMessage = async (deviceId, message) => {
    const newMessage = {
      id: Date.now().toString(),
      user_id: USER_ID,
      device_id: deviceId,
      message: message,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    
    try {
      // Optimistically add user message
      setMessages(prev => [...prev, newMessage]);
      
      // Send to backend for AI response
      const response = await axios.post(`${API}/chat/send?user_id=${USER_ID}`, {
        device_id: deviceId,
        message: message,
        sender: 'user'
      });
      
      if (response.data.success && response.data.ai_response) {
        // Add AI response to messages
        const aiMessage = {
          id: response.data.ai_response.message_id || Date.now().toString() + '_ai',
          user_id: USER_ID,
          device_id: deviceId,
          message: response.data.ai_response.message,
          sender: 'ai',
          ai_response: true,
          timestamp: new Date().toISOString()
        };
        
        // Add AI response after a brief delay for better UX
        setTimeout(() => {
          setMessages(prev => [...prev, aiMessage]);
        }, 500);
      }
      
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic message on error
      setMessages(prev => prev.filter(msg => msg.id !== newMessage.id));
      
      // Add error message
      const errorMessage = {
        id: Date.now().toString() + '_error',
        user_id: USER_ID,
        device_id: deviceId,
        message: 'Failed to send message. Please try again.',
        sender: 'system',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleMarkNotificationRead = async (notificationId) => {
    try {
      await axios.put(`${API}/notifications/${notificationId}/read`);
      setNotifications(prev => 
        prev.map(notif => 
          notif.id === notificationId 
            ? { ...notif, read: true }
            : notif
        )
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  // Push Notification Functions
  const checkPushSupport = () => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      setPushSupported(true);
      checkPushSubscription();
    } else {
      console.log('Push notifications not supported');
      setPushSupported(false);
    }
  };

  const checkPushSubscription = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      setPushSubscribed(!!subscription);
    } catch (error) {
      console.error('Error checking push subscription:', error);
    }
  };

  const requestNotificationPermission = async () => {
    if (!('Notification' in window)) {
      console.log('This browser does not support notifications');
      return false;
    }

    if (Notification.permission === 'granted') {
      return true;
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }

    return false;
  };

  const subscribeToPush = async () => {
    if (!pushSupported) {
      alert('Push notifications are not supported by your browser');
      return;
    }

    try {
      // Request notification permission
      const permissionGranted = await requestNotificationPermission();
      if (!permissionGranted) {
        alert('Notification permission denied');
        return;
      }

      // Get service worker registration
      const registration = await navigator.serviceWorker.ready;
      
      // Subscribe to push notifications
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      });

      // Send subscription to backend
      const subscriptionObject = {
        user_id: USER_ID,
        endpoint: subscription.endpoint,
        keys: {
          p256dh: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('p256dh')))),
          auth: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('auth'))))
        }
      };

      await axios.post(`${API}/push/subscribe`, subscriptionObject);
      setPushSubscribed(true);
      console.log('Successfully subscribed to push notifications');

    } catch (error) {
      console.error('Error subscribing to push notifications:', error);
      alert('Failed to subscribe to push notifications');
    }
  };

  const unsubscribeFromPush = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      
      if (subscription) {
        await subscription.unsubscribe();
        await axios.delete(`${API}/push/unsubscribe/${USER_ID}`);
        setPushSubscribed(false);
        console.log('Successfully unsubscribed from push notifications');
      }
    } catch (error) {
      console.error('Error unsubscribing from push notifications:', error);
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      {/* Mobile Navigation Header */}
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
        {currentView !== 'devices' && (
          <button
            onClick={() => {
              if (currentView === 'chat') {
                setCurrentView('devices');
                setSelectedDevice(null);
              } else {
                setCurrentView('devices');
              }
            }}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronLeft size={20} />
          </button>
        )}
        
        <h1 className="text-lg font-semibold text-gray-800">
          {currentView === 'devices' && 'Device Chat'}
          {currentView === 'chat' && selectedDevice?.name}
          {currentView === 'notifications' && 'Notifications'}
        </h1>
        
        <div className="flex items-center space-x-2">
          {pushSupported && (
            <button
              onClick={pushSubscribed ? unsubscribeFromPush : subscribeToPush}
              className={`p-2 hover:bg-gray-100 rounded-lg ${
                pushSubscribed ? 'text-green-600' : 'text-gray-400'
              }`}
              title={pushSubscribed ? 'Push notifications enabled' : 'Enable push notifications'}
            >
              <BellRing size={20} />
            </button>
          )}
          <button
            onClick={() => setCurrentView('notifications')}
            className="p-2 hover:bg-gray-100 rounded-lg relative"
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {currentView === 'devices' && (
          <DeviceList
            devices={devices}
            onSelectDevice={handleSelectDevice}
            selectedDevice={selectedDevice}
          />
        )}
        
        {currentView === 'chat' && (
          <ChatInterface
            device={selectedDevice}
            messages={messages}
            deviceNotifications={deviceNotifications}
            onSendMessage={handleSendMessage}
            onMarkNotificationRead={handleMarkNotificationRead}
            isConnected={isConnected}
          />
        )}
        
        {currentView === 'notifications' && (
          <div className="h-full overflow-y-auto">
            <NotificationsList
              notifications={notifications}
              devices={devices}
              onMarkRead={handleMarkNotificationRead}
            />
          </div>
        )}
      </div>

      {/* Connection Status */}
      {!isConnected && (
        <div className="bg-red-500 text-white px-4 py-2 text-sm text-center">
          Disconnected - Attempting to reconnect...
        </div>
      )}
    </div>
  );
};

export default App;