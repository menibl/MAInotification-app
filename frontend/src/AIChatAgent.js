import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, X, Code, AlertCircle, CheckCircle, MessageSquare } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * AI Chat Agent Component
 * Handles natural language intent understanding and JSON generation
 * Supports Global, Mission, and Camera scopes
 */
const AIChatAgent = ({ userId, chatType, deviceId, missionId, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [conversationState, setConversationState] = useState(null);
  const [generatedJSON, setGeneratedJSON] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initial greeting message
  useEffect(() => {
    const greetingMessage = {
      role: 'assistant',
      content: `👋 Hi! I'm your AI assistant for ${chatType === 'global' ? 'all cameras' : chatType === 'mission' ? 'this mission' : 'this camera'}.\n\nI can help you:\n• Set up detection queries for people, cars, and objects\n• Configure alert levels\n• Generate AI query JSON for your external system\n\nWhat would you like to detect?`,
      timestamp: new Date().toISOString()
    };
    setMessages([greetingMessage]);
  }, [chatType]);

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage = {
      role: 'user',
      content: inputText,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        `${API}/ai-agent/chat`,
        {
          chat_type: chatType,
          message: inputText,
          conversation_id: conversationId,
          device_id: deviceId || null,
          mission_id: missionId || null,
          context: {}
        },
        {
          params: { user_id: userId }
        }
      );

      if (response.data.success) {
        const aiMessage = {
          role: 'assistant',
          content: response.data.message,
          timestamp: new Date().toISOString(),
          state: response.data.state
        };

        setMessages(prev => [...prev, aiMessage]);
        setConversationId(response.data.conversation_id);
        setConversationState(response.data.state);

        // If JSON data is available, store it
        if (response.data.data) {
          setGeneratedJSON(response.data.data);
        }

        // If action is ready_to_send, show the JSON
        if (response.data.action === 'ready_to_send' && response.data.data) {
          const jsonMessage = {
            role: 'system',
            content: '📋 Generated AI Query JSON:',
            json: response.data.data,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, jsonMessage]);
        }
      } else {
        throw new Error(response.data.error || 'Failed to process message');
      }
    } catch (err) {
      setError(err.message || 'Failed to send message');
      const errorMessage = {
        role: 'system',
        content: `❌ Error: ${err.message || 'Failed to send message'}`,
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const sendQueryToExternalAPI = async () => {
    if (!generatedJSON) return;

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/ai-agent/send-query`,
        generatedJSON,
        {
          params: { user_id: userId }
        }
      );

      if (response.data.success) {
        const successMessage = {
          role: 'system',
          content: `✅ ${response.data.message}\n\n${response.data.note || ''}`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, successMessage]);
      }
    } catch (err) {
      setError('Failed to send query');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatJSON = (json) => {
    return JSON.stringify(json, null, 2);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-t-lg">
          <div className="flex items-center space-x-2">
            <Bot className="w-6 h-6" />
            <div>
              <h2 className="text-lg font-bold">AI Chat Agent</h2>
              <p className="text-sm opacity-90">
                {chatType === 'global' ? 'Global Scope' : chatType === 'mission' ? `Mission: ${missionId}` : `Camera: ${deviceId}`}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Conversation State Indicator */}
        {conversationState && (
          <div className="px-4 py-2 bg-blue-50 border-b border-blue-100 text-sm">
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1">
                <div className={`w-2 h-2 rounded-full ${
                  conversationState === 'intent_understanding' ? 'bg-yellow-500' :
                  conversationState === 'alert_level_selection' ? 'bg-orange-500' :
                  conversationState === 'confirmation' ? 'bg-green-500' :
                  'bg-gray-400'
                }`} />
                <span className="text-gray-700">
                  State: <strong>{conversationState.replace(/_/g, ' ').toUpperCase()}</strong>
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : msg.role === 'system'
                    ? msg.isError
                      ? 'bg-red-50 text-red-800 border border-red-200'
                      : 'bg-purple-50 text-purple-900 border border-purple-200'
                    : 'bg-white text-gray-800 border border-gray-200 shadow-sm'
                }`}
              >
                {/* Message content */}
                <div className="whitespace-pre-wrap break-words">{msg.content}</div>

                {/* JSON display */}
                {msg.json && (
                  <div className="mt-3 bg-gray-900 text-green-400 p-3 rounded text-xs font-mono overflow-x-auto">
                    <pre>{formatJSON(msg.json)}</pre>
                  </div>
                )}

                {/* Timestamp */}
                <div className={`text-xs mt-1 ${
                  msg.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                }`}>
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-lg p-3 border border-gray-200 shadow-sm">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                  <span className="text-gray-600 text-sm">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* JSON Action Buttons */}
        {generatedJSON && (
          <div className="px-4 py-3 bg-green-50 border-t border-green-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-green-800">
                <CheckCircle className="w-5 h-5" />
                <span className="text-sm font-medium">Query JSON Generated</span>
              </div>
              <button
                onClick={sendQueryToExternalAPI}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
              >
                Send to External API (Mocked)
              </button>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="px-4 py-2 bg-red-50 border-t border-red-200 text-red-800 text-sm flex items-center space-x-2">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-gray-200 bg-white rounded-b-lg">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              disabled={loading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !inputText.trim()}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
};

export default AIChatAgent;
