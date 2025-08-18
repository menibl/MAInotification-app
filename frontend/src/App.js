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
const ChatInterface = ({ device, messages, onSendMessage, isConnected, deviceNotifications, onMarkNotificationRead, reloadChat }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [mediaUrls, setMediaUrls] = useState(['']);
  const [showMediaInput, setShowMediaInput] = useState(false);
  const [referencedMessages, setReferencedMessages] = useState([]);
  const [selectedNotifications, setSelectedNotifications] = useState([]);
  const [multiSelectMode, setMultiSelectMode] = useState(false);
  const [currentRole, setCurrentRole] = useState('');
  const [showRoleSettings, setShowRoleSettings] = useState(false);
  const [cameraPrompt, setCameraPrompt] = useState('');
  const [showPromptSettings, setShowPromptSettings] = useState(false);
  const [promptInstructions, setPromptInstructions] = useState('');
  const [overrideVideoUrl, setOverrideVideoUrl] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const imageInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, deviceNotifications]);

  useEffect(() => {
    // Listen to SW postMessage for navigation with context (video_url)
    const onMessage = (event) => {
      if (event?.data?.type === 'navigate_to_device') {
        // Only apply if relevant device
        if (!device || event.data.device_id === device.id) {
          const vid = event.data.video_url;
          if (vid && isVideoUrl(vid)) {
            setOverrideVideoUrl(vid);
          }
        }
      }
    };
    navigator.serviceWorker?.addEventListener('message', onMessage);
    return () => navigator.serviceWorker?.removeEventListener('message', onMessage);
  }, [device]);

  useEffect(() => {
    // Load current role when device changes
    if (device) {
      loadCurrentRole();
    }
  }, [device]);

  useEffect(() => {
    // Load current role and camera prompt when device changes
    if (device) {
      loadCurrentRole();
      loadCameraPrompt();
    }
  }, [device]);

  const loadCurrentRole = async () => {
    if (!device) return;
    
    try {
      const response = await axios.get(`${API}/chat/settings/${USER_ID}/${device.id}`);
      setCurrentRole(response.data.role_name);
    } catch (error) {
      console.error('Failed to load current role:', error);
      setCurrentRole('AI Assistant');
    }
  };

  const loadCameraPrompt = async () => {
    if (!device) return;
    
    try {
      const response = await axios.get(`${API}/camera/prompt/${USER_ID}/${device.id}`);
      setCameraPrompt(response.data.prompt_text);
      setPromptInstructions(response.data.instructions);
    } catch (error) {
      console.error('Failed to load camera prompt:', error);
      setCameraPrompt('General security monitoring');
    }
  };

  const updateCameraPrompt = async (instructions) => {
    if (!device) return;
    
    try {
      const response = await axios.put(`${API}/camera/prompt/${USER_ID}/${device.id}`, {
        instructions: instructions
      });
      
      if (response.data.success) {
        setCameraPrompt(response.data.prompt_text);
        setPromptInstructions(instructions);
        setShowPromptSettings(false);
      }
    } catch (error) {
      console.error('Failed to update camera prompt:', error);
    }
  };

  const handleDirectImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file || !device) return;
    
    // Convert to base64
    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64 = e.target.result.split(',')[1]; // Remove data:image/...;base64, prefix
      
      try {
        const response = await axios.post(`${API}/chat/image-direct?user_id=${USER_ID}`, {
          device_id: device.id,
          image_data: base64,
          question: null // No question, let AI analyze based on camera prompt
        });
        
        if (response.data.success) {
          console.log(`Image analysis: ${response.data.analysis_type}`);
          if (response.data.displayed_in_chat) {
            // Reload messages to show new chat entries
            console.log('Image displayed in chat');
            if (typeof reloadChat === 'function') {
              reloadChat();
            }
          } else {
            console.log('Image logged but not displayed - routine activity');
          }
        }
      } catch (error) {
        console.error('Failed to send direct image:', error);
      }
    };
    
    reader.readAsDataURL(file);
    event.target.value = ''; // Reset input
  };

  const handleDirectImageUrl = async () => {
    const url = prompt('Enter image URL:');
    if (!url || !device) return;
    
    try {
      const response = await axios.post(`${API}/chat/image-direct?user_id=${USER_ID}`, {
        device_id: device.id,
        image_url: url,
        question: null
      });
      
      if (response.data.success) {
        console.log(`Image URL analysis: ${response.data.analysis_type}`);
        if (response.data.displayed_in_chat) {
          console.log('Image URL displayed in chat');
          if (typeof reloadChat === 'function') {
            reloadChat();
          }
        } else {
          console.log('Image URL logged but not displayed - routine activity');
        }
      }
    } catch (error) {
      console.error('Failed to send direct image URL:', error);
      alert('Failed to analyze image from URL. Please check the URL.');
    }
  };

  const handleSend = async () => {
    // 1) Corrective-feedback auto-detection to improve monitoring prompt before sending to AI
    if (device && inputMessage.trim()) {
      const loweredFull = inputMessage.trim().toLowerCase();
      const feedbackHint = /(wrong|mistake|incorrect|should have|shouldn't|misclassified|false positive|false alarm|it was)/;
      if (feedbackHint.test(loweredFull) && inputMessage.trim().split(/\s+/).length > 3) {
        try {
          const res = await axios.post(`${API}/camera/prompt/fix-from-feedback`, {
            user_id: USER_ID,
            device_id: device.id,
            message: inputMessage.trim(),
            // Try to reference the latest AI message for context
            referenced_messages: (messages.slice().reverse().find(m => m.device_id === device.id && m.sender === 'ai')?.id) ? [messages.slice().reverse().find(m => m.device_id === device.id && m.sender === 'ai').id] : []
          });
          if (res.data.success) {
            // Refresh chat and header prompt
            if (typeof reloadChat === 'function') {
              await reloadChat();
            }
            await loadCameraPrompt();
            // Clear inputs and selections as per preference
            setInputMessage('');
            setSelectedFiles([]);
            setMediaUrls(['']);
            setShowMediaInput(false);
            setReferencedMessages([]);
            setSelectedNotifications([]);
            setMultiSelectMode(false);
            return; // Stop here; do not send to AI
          }
        } catch (e) {
          console.error('Prompt fix from feedback failed', e);
          // Fallthrough to normal send if this fails
        }
      }
    }

    // 2) Natural-language camera prompt update (no AI response), per user preference
    // Natural-language camera prompt update (no AI response), per user preference
    if (device && inputMessage.trim()) {
      const lowered = inputMessage.trim().toLowerCase();
      if (/(monitor for|update camera prompt to|update prompt to|please monitor|look for|watch for)/.test(lowered)) {
        try {
          const res = await axios.post(`${API}/camera/prompt/parse-command`, {
            user_id: USER_ID,
            device_id: device.id,
            message: inputMessage.trim(),
          });
          if (res.data.success && res.data.settings_updated) {
            // Refresh chat and header prompt
            if (typeof reloadChat === 'function') {
              await reloadChat();
            }
            await loadCameraPrompt();
            // Clear inputs and selections
            setInputMessage('');
            setSelectedFiles([]);
            setMediaUrls(['']);
            setShowMediaInput(false);
            setReferencedMessages([]);
            setSelectedNotifications([]);
            setMultiSelectMode(false);
            return; // Do not send to AI
          }
        } catch (e) {
          console.error('Camera prompt update failed', e);
        }
      }
    }

    const validMediaUrls = mediaUrls.filter(url => url.trim() !== '');
    
    // Add notification media URLs to mediaUrls if any notifications are selected
    const notificationMediaUrls = selectedNotifications
      .filter(notif => notif.media_url)
      .map(notif => notif.media_url);
    
    const allMediaUrls = [...validMediaUrls, ...notificationMediaUrls];
    
    if ((inputMessage.trim() || selectedFiles.length > 0 || allMediaUrls.length > 0 || selectedNotifications.length > 0) && device) {
      // Build enhanced message including notification content
      let enhancedMessage = inputMessage.trim();
      
      if (selectedNotifications.length > 0) {
        const notificationContext = selectedNotifications.map(notif => 
          `[Notification from ${new Date(notif.timestamp).toLocaleString()}]: ${notif.content}`
        ).join('\n');
        
        enhancedMessage = enhancedMessage 
          ? `${enhancedMessage}\n\nReferencing notifications:\n${notificationContext}`
          : `Referencing notifications:\n${notificationContext}`;
      }
      
      // Clear input immediately for better UX
      setInputMessage('');
      setSelectedFiles([]);
      setMediaUrls(['']);
      setShowMediaInput(false);
      setReferencedMessages([]);
      setSelectedNotifications([]);
      setMultiSelectMode(false);

      // Send message
      await onSendMessage(device.id, enhancedMessage, selectedFiles, referencedMessages, allMediaUrls);
    }
  };

  const toggleNotificationSelection = (notification) => {
    setSelectedNotifications(prev => {
      const isAlreadySelected = prev.some(n => n.id === notification.id);
      if (isAlreadySelected) {
        return prev.filter(n => n.id !== notification.id);
      } else {
        return [...prev, notification];
      }
    });
  };

  const clearAllSelections = () => {
    setReferencedMessages([]);
    setSelectedNotifications([]);
    setMultiSelectMode(false);
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

  const addMediaUrl = () => {
    setMediaUrls(prev => [...prev, '']);
  };

  const updateMediaUrl = (index, value) => {
    setMediaUrls(prev => prev.map((url, i) => i === index ? value : url));
  };

  const removeMediaUrl = (index) => {
    setMediaUrls(prev => prev.filter((_, i) => i !== index));
    if (mediaUrls.length <= 1) {
      setShowMediaInput(false);
    }
  };

  const isValidUrl = (url) => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const isImageUrl = (url) => {
    return /\.(jpg|jpeg|png|gif|bmp|webp|svg)(\?.*)?$/i.test(url);
  };

  const isVideoUrl = (url) => {
    return /\.(mp4|avi|mov|webm|mkv)(\?.*)?$/i.test(url);
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

  // Determine latest video from notifications
  const latestVideoNotif = [...(deviceNotifications || [])]
    .filter(n => n && n.media_url && isVideoUrl(n.media_url))
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0];
  const latestVideoUrl = latestVideoNotif?.media_url || null;
  const liveStreamUrl = `https://www.maifocus.com/show/${device.id}`;

  // Combine messages and notifications for this device, sorted by timestamp
  const allItems = [
    ...messages.map(msg => ({ ...msg, type: 'message' })),
    ...deviceNotifications.map(notif => ({ ...notif, type: 'notification' }))
  ].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header (minimal) */}
      <div className="px-4 py-3 border-b bg-gray-50">
        <div className="flex items-center gap-2 text-gray-800 text-sm md:text-base truncate">
          <span className="font-semibold truncate">{device.name}</span>
          <span className="text-gray-400">•</span>
          <span className="truncate">{promptInstructions || 'General security monitoring'}</span>
        </div>
      </div>

      {/* Video Windows */}
      <div className="px-4 pt-3 pb-1 border-b bg-white">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded-lg border bg-black/5 p-2">
            <div className="text-xs text-gray-600 mb-1">Latest Event Video</div>
            {latestVideoUrl ? (
              <video key={latestVideoUrl} src={latestVideoUrl} controls className="w-full h-40 md:h-56 rounded-md bg-black" />
            ) : (
              <div className="w-full h-40 md:h-56 rounded-md bg-gray-100 flex items-center justify-center text-gray-400 text-sm">
                No recent video
              </div>
            )}
          </div>
          <div className="rounded-lg border bg-black/5 p-2">
            <div className="text-xs text-gray-600 mb-1">Live Stream</div>
            <iframe
              key={liveStreamUrl}
              src={liveStreamUrl}
              title="Live HLS Stream"
              className="w-full h-40 md:h-56 rounded-md border-0"
              allow="autoplay; encrypted-media; picture-in-picture"
              allowFullScreen
            />
          </div>
        </div>
      </div>

      {/* Prompt Settings Modal */}
      {showPromptSettings && (
        <div className="px-4 py-3 bg-yellow-50 border-b">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-yellow-800">Camera Monitoring Instructions</span>
            <button onClick={() => setShowPromptSettings(false)} className="text-yellow-600">
              <X size={16} />
            </button>
          </div>
          <div className="space-y-2">
            <textarea
              value={promptInstructions}
              onChange={(e) => setPromptInstructions(e.target.value)}
              placeholder="Tell me what you want to monitor for (e.g., 'people entering restricted areas', 'packages left unattended', 'vehicles in parking lot after hours')"
              className="w-full p-2 text-sm border border-yellow-300 rounded focus:outline-none focus:ring-2 focus:ring-yellow-500"
              rows="3"
            />
            <div className="flex items-center space-x-2">
              <button
                onClick={() => updateCameraPrompt(promptInstructions)}
                className="px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700"
              >
                Update Monitoring
              </button>
              <span className="text-xs text-yellow-600">AI will analyze images based on these instructions</span>
            </div>
          </div>
        </div>
      )}

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
                  
                  {/* Media URLs display */}
                  {item.media_urls && item.media_urls.length > 0 && (
                    <div className="mt-2 space-y-2">
                      {item.media_urls.map((url, idx) => (
                        <div key={idx} className="border rounded-lg overflow-hidden bg-black bg-opacity-5">
                          {/\.(jpg|jpeg|png|gif|bmp|webp|svg)(\?.*)?$/i.test(url) ? (
                            <div>
                              <img 
                                src={url} 
                                alt="Shared image"
                                className="w-full max-w-xs rounded"
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                  e.target.nextSibling.style.display = 'block';
                                }}
                              />
                              <div className="hidden p-2 text-xs">
                                🖼️ <a href={url} target="_blank" rel="noopener noreferrer" className="underline">View Image</a>
                              </div>
                            </div>
                          ) : /\.(mp4|avi|mov|webm|mkv)(\?.*)?$/i.test(url) ? (
                            <div>
                              <video 
                                controls 
                                className="w-full max-w-xs rounded"
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                  e.target.nextSibling.style.display = 'block';
                                }}
                              >
                                <source src={url} />
                                Your browser does not support the video tag.
                              </video>
                              <div className="hidden p-2 text-xs">
                                🎥 <a href={url} target="_blank" rel="noopener noreferrer" className="underline">View Video</a>
                              </div>
                            </div>
                          ) : (
                            <div className="p-2 text-xs">
                              🔗 <a href={url} target="_blank" rel="noopener noreferrer" className="underline">
                                {url.length > 50 ? url.substring(0, 50) + '...' : url}
                              </a>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  
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
                  className={`max-w-md px-4 py-3 rounded-lg border-l-4 cursor-pointer transition-colors relative ${
                    selectedNotifications.some(n => n.id === item.id)
                      ? 'bg-green-100 border-green-400 ring-2 ring-green-300'
                      : item.read 
                        ? 'bg-gray-50 border-gray-300 hover:bg-gray-100' 
                        : 'bg-blue-50 border-blue-400 hover:bg-blue-100'
                  }`}
                  onClick={() => {
                    if (!item.read) {
                      onMarkNotificationRead(item.id);
                    }
                    toggleNotificationSelection(item);
                  }}
                >
                  {/* Selection indicator */}
                  {selectedNotifications.some(n => n.id === item.id) && (
                    <div className="absolute -top-1 -right-1 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                      <Check size={12} className="text-white" />
                    </div>
                  )}
                  
                  <div className="flex items-start space-x-3">
                    <Bell size={16} className={
                      selectedNotifications.some(n => n.id === item.id) 
                        ? 'text-green-600' 
                        : item.read ? 'text-gray-400' : 'text-blue-500'
                    } />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-800">
                        Device Notification
                        {selectedNotifications.some(n => n.id === item.id) && (
                          <span className="ml-2 text-xs bg-green-200 text-green-800 px-2 py-1 rounded">
                            Selected for chat
                          </span>
                        )}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {item.content}
                      </p>
                      {item.media_url && (
                        <div className="mt-2 p-2 bg-white rounded border">
                          <div className="flex items-center space-x-2 text-xs text-gray-600">
                            <Image size={12} />
                            <span>Media: {item.media_url.substring(0, 30)}...</span>
                          </div>
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
        {/* Referenced messages and notifications preview */}
        {(referencedMessages.length > 0 || selectedNotifications.length > 0) && (
          <div className="px-4 py-2 bg-blue-50 border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Reply size={14} className="text-blue-600" />
                <span className="text-sm text-blue-700">
                  {referencedMessages.length > 0 && selectedNotifications.length > 0 
                    ? `${referencedMessages.length} messages + ${selectedNotifications.length} notifications selected`
                    : referencedMessages.length > 0
                      ? multiSelectMode ? `${referencedMessages.length} messages selected` : 'Replying to message'
                      : `${selectedNotifications.length} notification${selectedNotifications.length > 1 ? 's' : ''} selected`
                  }
                </span>
              </div>
              <button
                onClick={clearAllSelections}
                className="text-blue-600 hover:text-blue-800"
              >
                <X size={16} />
              </button>
            </div>
            
            {/* Show selected notifications preview */}
            {selectedNotifications.length > 0 && (
              <div className="mt-2 space-y-1">
                <div className="text-xs text-blue-600 font-medium">Selected Notifications:</div>
                {selectedNotifications.map((notif, index) => (
                  <div key={notif.id} className="flex items-center space-x-2 p-2 bg-white rounded text-xs">
                    <Bell size={10} className="text-blue-500" />
                    <span className="flex-1 truncate">{notif.content}</span>
                    {notif.media_url && (
                      <div className="flex items-center space-x-1 text-green-600">
                        <Image size={10} />
                        <span>+Media</span>
                      </div>
                    )}
                    <button
                      onClick={() => toggleNotificationSelection(notif)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            {referencedMessages.length > 0 && (
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
            )}
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
        
        {/* Media URLs preview */}
        {showMediaInput && (
          <div className="px-4 py-2 bg-blue-50 border-b">
            <div className="flex items-center space-x-2 mb-2">
              <Image size={14} className="text-blue-600" />
              <span className="text-sm text-blue-700">Media URLs (Images & Videos)</span>
            </div>
            <div className="space-y-2">
              {mediaUrls.map((url, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => updateMediaUrl(index, e.target.value)}
                    placeholder="https://example.com/image.jpg or video.mp4"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <div className="flex items-center space-x-1">
                    {url && isValidUrl(url) && (
                      <>
                        {isImageUrl(url) && <Image size={14} className="text-green-600" title="Image detected" />}
                        {isVideoUrl(url) && <Video size={14} className="text-purple-600" title="Video detected" />}
                        {!isImageUrl(url) && !isVideoUrl(url) && <File size={14} className="text-gray-600" title="Other media" />}
                      </>
                    )}
                  </div>
                  <button
                    onClick={() => removeMediaUrl(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
              <button
                onClick={addMediaUrl}
                className="flex items-center space-x-1 text-blue-600 hover:text-blue-800 text-sm"
              >
                <Plus size={14} />
                <span>Add another URL</span>
              </button>
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
            <button
              onClick={() => setShowMediaInput(!showMediaInput)}
              className={`px-3 py-2 rounded-lg ${
                showMediaInput 
                  ? 'text-blue-700 bg-blue-100 hover:bg-blue-200' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
              title="Add image/video URLs"
            >
              <Image size={18} />
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
              disabled={!inputMessage.trim() && selectedFiles.length === 0 && mediaUrls.filter(url => url.trim()).length === 0 && selectedNotifications.length === 0}
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
const NotificationsList = ({ notifications, devices, onMarkRead, onNavigateToDevice }) => {
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

  const handleNotificationClick = (notification) => {
    // Mark as read if unread
    if (!notification.read) {
      onMarkRead(notification.id);
    }
    
    // Navigate to device chat with this notification pre-selected
    const device = deviceMap[notification.device_id];
    if (device && onNavigateToDevice) {
      onNavigateToDevice(device, notification);
    }
  };

  return (
    <div className="space-y-2 p-4">
      {notifications.map(notification => {
        const device = deviceMap[notification.device_id];
        const deviceName = device ? device.name : notification.device_id;
        
        return (
          <div
            key={notification.id}
            className={`p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
              notification.read ? 'bg-gray-50 hover:bg-gray-100' : 'bg-blue-50 border-blue-200 hover:bg-blue-100'
            }`}
            onClick={() => handleNotificationClick(notification)}
          >
            <div className="flex items-start space-x-3">
              <div className={`w-2 h-2 rounded-full mt-2 ${
                notification.read ? 'bg-gray-400' : 'bg-blue-500'
              }`}></div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
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
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <MessageCircle size={12} />
                    <span>Go to chat</span>
                    <ChevronLeft size={12} className="rotate-180" />
                  </div>
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

  const handleNavigateToDeviceFromNotification = (device, notification) => {
    setSelectedDevice(device);
    setCurrentView('chat');
    loadChatMessages(device.id);
    
    // Store the notification to be pre-selected in chat
    // We'll use a timeout to ensure the chat interface has loaded first
    setTimeout(() => {
      // The ChatInterface component will need to handle this notification
      // For now, we'll just navigate - we can enhance this later
    }, 100);
  };

  const handleSendMessage = async (deviceId, message, files = [], referencedMessages = [], mediaUrls = []) => {
    try {
      // Upload files first if any
      const fileIds = [];
      if (files && files.length > 0) {
        for (const file of files) {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('user_id', USER_ID);
          formData.append('device_id', deviceId);
          
          const uploadResponse = await axios.post(`${API}/files/upload`, formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });
          
          if (uploadResponse.data.success) {
            fileIds.push(uploadResponse.data.file_id);
          }
        }
      }

      // Clean media URLs (remove empty ones)
      const validMediaUrls = mediaUrls.filter(url => url.trim() !== '');

      const newMessage = {
        id: Date.now().toString(),
        user_id: USER_ID,
        device_id: deviceId,
        message: message,
        sender: 'user',
        media_urls: validMediaUrls.length > 0 ? validMediaUrls : null,
        file_attachments: files.map((file, index) => ({
          file_id: fileIds[index] || '',
          filename: file.name,
          file_type: file.type,
          file_size: file.size,
          url: fileIds[index] ? `${API}/files/${fileIds[index]}` : ''
        })),
        referenced_messages: referencedMessages,
        timestamp: new Date().toISOString()
      };
      
      // Optimistically add user message
      setMessages(prev => [...prev, newMessage]);
      
      // Send to backend for AI response
      const requestData = {
        device_id: deviceId,
        message: message,
        sender: 'user',
        referenced_messages: referencedMessages.length > 0 ? referencedMessages : undefined,
        file_ids: fileIds.length > 0 ? fileIds : undefined,
        media_urls: validMediaUrls.length > 0 ? validMediaUrls : undefined
      };
      
      const response = await axios.post(`${API}/chat/send?user_id=${USER_ID}`, requestData, {
        headers: {
          'Content-Type': 'application/json',
        },
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
            reloadChat={() => selectedDevice && loadChatMessages(selectedDevice.id)}
          />
        )}
        
        {currentView === 'notifications' && (
          <div className="h-full overflow-y-auto">
            <NotificationsList
              notifications={notifications}
              devices={devices}
              onMarkRead={handleMarkNotificationRead}
              onNavigateToDevice={handleNavigateToDeviceFromNotification}
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