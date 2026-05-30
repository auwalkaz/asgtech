import os
from dotenv import load_dotenv

# Load .env file from the correct location
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-this-in-production")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    
    # Supported Languages
    SUPPORTED_LANGUAGES = {
        "en": {"name": "English", "voice": "alloy", "model_voice": "alloy", "flag": "🇬🇧", "code": "en-US"},
        "fr": {"name": "French", "voice": "nova", "model_voice": "nova", "flag": "🇫🇷", "code": "fr-FR"},
        "es": {"name": "Spanish", "voice": "nova", "model_voice": "nova", "flag": "🇪🇸", "code": "es-ES"},
        "pt": {"name": "Portuguese", "voice": "shimmer", "model_voice": "shimmer", "flag": "🇵🇹", "code": "pt-PT"},
        "sw": {"name": "Swahili", "voice": "echo", "model_voice": "echo", "flag": "🇹🇿", "code": "sw-KE"},
        "ar": {"name": "Arabic", "voice": "onyx", "model_voice": "onyx", "flag": "🇸🇦", "code": "ar-SA"},
        "zh": {"name": "Chinese", "voice": "shimmer", "model_voice": "shimmer", "flag": "🇨🇳", "code": "zh-CN"},
        "hi": {"name": "Hindi", "voice": "nova", "model_voice": "nova", "flag": "🇮🇳", "code": "hi-IN"},
        "it": {"name": "Italian", "voice": "nova", "model_voice": "nova", "flag": "🇮🇹", "code": "it-IT"},
        "de": {"name": "German", "voice": "onyx", "model_voice": "onyx", "flag": "🇩🇪", "code": "de-DE"},
        "ja": {"name": "Japanese", "voice": "shimmer", "model_voice": "shimmer", "flag": "🇯🇵", "code": "ja-JP"},
        "ko": {"name": "Korean", "voice": "nova", "model_voice": "nova", "flag": "🇰🇷", "code": "ko-KR"},
        "ru": {"name": "Russian", "voice": "onyx", "model_voice": "onyx", "flag": "🇷🇺", "code": "ru-RU"},
        "tr": {"name": "Turkish", "voice": "nova", "model_voice": "nova", "flag": "🇹🇷", "code": "tr-TR"},
        "nl": {"name": "Dutch", "voice": "shimmer", "model_voice": "shimmer", "flag": "🇳🇱", "code": "nl-NL"}
    }

config = Config()

# Debug print
print(f"✅ Config loaded - OpenAI Key present: {bool(config.OPENAI_API_KEY)}")
print(f"📁 Data folder: {config.DATA_FOLDER}")