import json
import base64
from openai import OpenAI
from config import config
from utils.helpers import clean_json_response

class AIService:
    def __init__(self):
        print("🔧 Initializing AIService...")
        if not config.OPENAI_API_KEY:
            print("❌ OPENAI_API_KEY not found in environment variables!")
            print("Please check your .env file")
            self.client = None
        else:
            print("✅ OpenAI API key found")
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
    
    def chat_completion(self, messages, temperature=0.7, max_tokens=500):
        """Send chat completion request to OpenAI"""
        if not self.client:
            return "Error: OpenAI API key not configured. Please check your .env file."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return f"Error: {str(e)}"
    
    def generate_json(self, prompt, temperature=0.7, max_tokens=1000):
        """Generate and parse JSON from AI"""
        try:
            response = self.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            raw = clean_json_response(response)
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Raw response: {response[:200] if 'response' in locals() else 'No response'}")
            return {}
        except Exception as e:
            print(f"Generation error: {e}")
            return {}
    
    def generate_speech(self, text, voice="alloy"):
        """Generate TTS audio"""
        if not self.client:
            return None
        
        try:
            audio = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=text
            )
            return audio.content
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio to text"""
        if not self.client:
            return ""
        
        try:
            transcript = self.client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file
            )
            return transcript.text
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

# Create instance
print("🚀 Creating ai_service instance...")
ai_service = AIService()
print("✅ ai_service initialized")