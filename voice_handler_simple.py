"""
Simplified Voice Debate Handler
Uses Deepgram REST API for simpler integration with Flask
"""

import requests
import base64
from debate_engine import DebateEngine
import time

class VoiceDebateHandler:
    def __init__(self, deepgram_api_key: str, anthropic_api_key: str, difficulty: str, topic: str, mode: str = "ranked"):
        """Initialize voice debate handler"""
        self.deepgram_api_key = deepgram_api_key
        self.anthropic_api_key = anthropic_api_key
        self.difficulty = difficulty
        self.topic = topic
        self.mode = mode
        
        # Initialize debate engine
        self.debate_engine = DebateEngine(anthropic_api_key, difficulty, topic, mode)
        
        # State
        self.is_speaking = False
        self.audio_buffer = b''
        
        # Callbacks
        self.on_transcript_update = None
        self.on_ai_response = None
        self.on_scores_update = None
        self.on_audio_ready = None
        
        print(f"🎤 Voice handler initialized for {difficulty} debate on: {topic}")
    
    def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio using Deepgram REST API"""
        try:
            print(f"🎤 Transcribing {len(audio_data)} bytes of audio...")
            
            # Deepgram REST API endpoint
            url = "https://api.deepgram.com/v1/listen"
            
            headers = {
                "Authorization": f"Token {self.deepgram_api_key}",
                "Content-Type": "audio/webm"
            }
            
            params = {
                "model": "nova-2",
                "smart_format": "true",
                "language": "en"
            }
            
            # Send audio to Deepgram
            response = requests.post(
                url,
                headers=headers,
                params=params,
                data=audio_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
                print(f"✅ Transcription: {transcript}")
                return transcript
            else:
                print(f"❌ Deepgram error: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def process_argument(self, user_text: str):
        """Process user's argument through debate engine"""
        try:
            print(f"🤖 Processing argument with Claude...")
            
            # Get AI response from debate engine
            result = self.debate_engine.process_user_argument(user_text)
            
            # Send scores update
            if result.get('scores') and self.on_scores_update:
                self.on_scores_update(result['scores'])
            
            # Get AI response text
            ai_response = result.get('ai_response', '')
            feedback = result.get('feedback', '')
            
            print(f"✅ AI Response: {ai_response[:100]}...")
            
            # Send AI response to frontend
            if self.on_ai_response:
                self.on_ai_response(ai_response, feedback)
            
            # Generate speech for AI response
            audio_data = self.speak_response(ai_response)
            
            return {
                'ai_response': ai_response,
                'scores': result.get('scores'),
                'feedback': feedback,
                'audio': audio_data
            }
            
        except Exception as e:
            print(f"❌ Error processing argument: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def speak_response(self, text: str) -> str:
        """Convert text to speech using Deepgram TTS REST API"""
        try:
            self.is_speaking = True
            print(f"🔊 Generating AI speech for: {text[:50]}...")
            
            # Deepgram TTS REST API endpoint - MALE VOICE
            url = "https://api.deepgram.com/v1/speak?model=aura-zeus-en&encoding=mp3"
            
            headers = {
                "Authorization": f"Token {self.deepgram_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text
            }
            
            # Generate speech
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                # Encode audio as base64 for transmission
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                print(f"✅ Generated {len(response.content)} bytes of audio")
                
                self.is_speaking = False
                return audio_base64
            else:
                print(f"❌ TTS error: {response.status_code} - {response.text}")
                self.is_speaking = False
                return None
                
        except Exception as e:
            self.is_speaking = False
            print(f"❌ Error generating speech: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_current_scores(self):
        """Get current debate scores"""
        return self.debate_engine.get_current_scores()
    
    def cleanup(self):
        """Clean up resources"""
        self.is_speaking = False
        print("🧹 Voice handler cleaned up")
