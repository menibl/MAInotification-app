"""
AI Chat Agent for Intent Understanding and AI Query Management
"""
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# System prompts for different stages
INTENT_ANALYSIS_PROMPT = """You are an AI-powered video and image analysis system for understanding events.

Your role:
1. Analyze the user's question to understand their intent
2. Identify which cameras or missions they're asking about
3. Identify what objects/events they want to detect (people, cars, etc.)
4. Ask clarifying questions if needed
5. Confirm your understanding before proceeding

Be conversational and helpful. Ask questions to clarify ambiguous requests.

When the user confirms, respond with a JSON structure like:
{
  "confirmed": true,
  "target_type": "cameras" | "mission" | "all",
  "target_ids": ["camera1", "camera3"],
  "objects_to_detect": ["people", "cars"],
  "query_text": "original user query"
}
"""

ALERT_LEVEL_PROMPT = """Ask the user about alert urgency levels for their detection query.

Explain the three levels:
1. HIGH (דחוף) - Immediate notification, requires urgent attention
2. MEDIUM (בינוני) - Important but not urgent
3. LOW (נמוך) - Informational only

Ask which level they want for their query and confirm their choice.
"""

FEEDBACK_LEARNING_PROMPT = """You are analyzing user feedback on AI detections.

The user is providing corrections:
- "I got an alert about a person but there's no person" - False positive
- "There was a car but no alert" - False negative
- "This is correct" - True positive

Analyze the feedback and generate an updated AI query JSON that will improve detection accuracy.
"""

class ChatState:
    """Track conversation state"""
    INTENT_UNDERSTANDING = "intent_understanding"
    ALERT_LEVEL_SELECTION = "alert_level_selection"
    CONFIRMATION = "confirmation"
    FEEDBACK_LEARNING = "feedback_learning"
    COMPLETED = "completed"

class AIChatAgent:
    def __init__(self):
        self.conversations = {}  # Store conversation states
        
    async def process_message(
        self,
        user_id: str,
        chat_type: str,  # "global", "mission", "camera"
        message: str,
        context: Optional[Dict] = None,
        image_url: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user message through the AI agent
        
        Args:
            user_id: User identifier
            chat_type: Type of chat (global/mission/camera)
            message: User message
            context: Additional context (cameras, missions, etc.)
            image_url: Optional image for feedback learning
            conversation_id: Track multi-turn conversations
            
        Returns:
            Response dict with agent's reply and actions
        """
        if not conversation_id:
            conversation_id = f"{user_id}_{chat_type}_{datetime.utcnow().timestamp()}"
            
        # Get or create conversation state
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "state": ChatState.INTENT_UNDERSTANDING,
                "history": [],
                "data": {}
            }
        
        conv = self.conversations[conversation_id]
        conv["history"].append({"role": "user", "content": message})
        
        # Route to appropriate handler based on state
        if image_url and "feedback" in message.lower():
            # Feedback learning mode
            result = await self._handle_feedback_learning(
                conv, message, image_url, context
            )
        elif conv["state"] == ChatState.INTENT_UNDERSTANDING:
            result = await self._handle_intent_understanding(
                conv, message, context
            )
        elif conv["state"] == ChatState.ALERT_LEVEL_SELECTION:
            result = await self._handle_alert_level(
                conv, message
            )
        else:
            result = await self._handle_general_chat(
                conv, message
            )
        
        conv["history"].append({"role": "assistant", "content": result["message"]})
        
        return {
            "conversation_id": conversation_id,
            "state": conv["state"],
            "message": result["message"],
            "action": result.get("action"),
            "data": result.get("data"),
            "requires_confirmation": result.get("requires_confirmation", False)
        }
    
    async def _handle_intent_understanding(
        self,
        conv: Dict,
        message: str,
        context: Optional[Dict]
    ) -> Dict:
        """Handle intent understanding phase"""
        
        # Build context string
        context_str = ""
        if context:
            if context.get("cameras"):
                cameras = context["cameras"]
                context_str += f"\nAvailable cameras: {', '.join([c['name'] + ' (ID: ' + c['id'] + ')' for c in cameras])}"
            if context.get("missions"):
                missions = context["missions"]
                context_str += f"\nAvailable missions: {', '.join([m['name'] + ' (ID: ' + m['id'] + ')' for m in missions])}"
        
        messages = [
            {"role": "system", "content": INTENT_ANALYSIS_PROMPT + context_str},
            *conv["history"]
        ]
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )
        
        reply = response.choices[0].message.content
        
        # Check if user confirmed
        if any(word in message.lower() for word in ["כן", "yes", "נכון", "correct", "אישור", "confirm"]):
            # Try to extract JSON from previous context
            if "confirmed" in reply.lower() or "{" in reply:
                # Move to alert level selection
                conv["state"] = ChatState.ALERT_LEVEL_SELECTION
                return {
                    "message": reply + "\n\n" + "עכשיו, באיזו רמת דחיפות תרצה לקבל התראות?\n1. דחוף (HIGH) - התראה מיידית\n2. בינוני (MEDIUM) - חשוב אך לא דחוף\n3. נמוך (LOW) - מידע בלבד",
                    "requires_confirmation": True
                }
        
        return {
            "message": reply,
            "requires_confirmation": True
        }
    
    async def _handle_alert_level(
        self,
        conv: Dict,
        message: str
    ) -> Dict:
        """Handle alert level selection"""
        
        # Extract alert level
        alert_level = "MEDIUM"  # default
        if any(word in message.lower() for word in ["דחוף", "high", "גבוה", "1"]):
            alert_level = "HIGH"
        elif any(word in message.lower() for word in ["נמוך", "low", "3"]):
            alert_level = "LOW"
        
        conv["data"]["alert_level"] = alert_level
        conv["state"] = ChatState.CONFIRMATION
        
        # Generate final JSON
        ai_query_json = self._generate_ai_query_json(conv)
        conv["data"]["ai_query_json"] = ai_query_json
        
        return {
            "message": f"מעולה! רמת ההתראה שנבחרה: {alert_level}\n\nהשאילתה שתישלח למערכת:\n```json\n{json.dumps(ai_query_json, indent=2, ensure_ascii=False)}\n```\n\nהאם לשלוח את השאילתה למערכת? (כן/לא)",
            "data": ai_query_json,
            "action": "ready_to_send",
            "requires_confirmation": True
        }
    
    async def _handle_feedback_learning(
        self,
        conv: Dict,
        message: str,
        image_url: str,
        context: Optional[Dict]
    ) -> Dict:
        """Handle feedback learning from images"""
        
        messages = [
            {"role": "system", "content": FEEDBACK_LEARNING_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )
        
        reply = response.choices[0].message.content
        
        # Extract updated JSON from reply
        # This should contain the corrected AI query
        
        return {
            "message": reply,
            "action": "update_ai_query",
            "data": {
                "feedback_type": "correction",
                "image_url": image_url,
                "user_feedback": message
            }
        }
    
    async def _handle_general_chat(
        self,
        conv: Dict,
        message: str
    ) -> Dict:
        """Handle general conversation"""
        
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant for a video surveillance system."},
            *conv["history"]
        ]
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )
        
        return {
            "message": response.choices[0].message.content
        }
    
    def _generate_ai_query_json(self, conv: Dict) -> Dict:
        """Generate AI query JSON from conversation data"""
        
        # Extract info from conversation history
        # This is a simplified version - you'd parse from actual AI responses
        
        return {
            "query_id": f"query_{datetime.utcnow().timestamp()}",
            "user_id": conv.get("user_id", "unknown"),
            "created_at": datetime.utcnow().isoformat(),
            "target_type": conv["data"].get("target_type", "cameras"),
            "target_ids": conv["data"].get("target_ids", []),
            "detection_objects": conv["data"].get("objects_to_detect", []),
            "alert_level": conv["data"].get("alert_level", "MEDIUM"),
            "query_text": conv["data"].get("query_text", ""),
            "confidence_threshold": 0.7 if conv["data"].get("alert_level") == "HIGH" else 0.5,
            "notification_settings": {
                "enabled": True,
                "alert_level": conv["data"].get("alert_level", "MEDIUM"),
                "notify_immediately": conv["data"].get("alert_level") == "HIGH"
            }
        }
    
    def get_conversation_state(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation state"""
        return self.conversations.get(conversation_id)
    
    def reset_conversation(self, conversation_id: str):
        """Reset conversation state"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

# Global agent instance
ai_chat_agent = AIChatAgent()
