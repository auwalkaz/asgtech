import base64
from services.ai_service import ai_service
from config import config

class AudioService:
    def __init__(self):
        self.client = ai_service.client
    
    def text_to_speech(self, text, language='en'):
        """Convert text to speech using OpenAI TTS"""
        voice_config = config.SUPPORTED_LANGUAGES.get(language, config.SUPPORTED_LANGUAGES["en"])
        tts_voice = voice_config["model_voice"]
        
        audio_content = ai_service.generate_speech(text, tts_voice)
        audio_base64 = base64.b64encode(audio_content).decode("utf-8")
        
        return {
            "audio": audio_base64,
            "voice_used": tts_voice,
            "text_length": len(text)
        }
    
    def text_to_speech_with_chunks(self, text, language='en'):
        """Convert text to speech with sentence-level chunks"""
        sentences = text.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        voice_config = config.SUPPORTED_LANGUAGES.get(language, config.SUPPORTED_LANGUAGES["en"])
        tts_voice = voice_config["model_voice"]
        
        # Full audio
        full_audio = ai_service.generate_speech(text, tts_voice)
        full_audio_base64 = base64.b64encode(full_audio).decode("utf-8")
        
        # Sentence audios
        sentence_audios = []
        for sentence in sentences[:5]:
            if len(sentence) > 5:
                audio_content = ai_service.generate_speech(sentence, tts_voice)
                sentence_audios.append({
                    "sentence": sentence,
                    "audio": base64.b64encode(audio_content).decode("utf-8")
                })
        
        return {
            "full_audio": full_audio_base64,
            "sentence_audios": sentence_audios,
            "total_sentences": len(sentences),
            "voice_used": tts_voice
        }

audio_service = AudioService()