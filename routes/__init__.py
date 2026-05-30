from .session_routes import session_bp
from .vocabulary_routes import vocab_bp
from .chat_routes import chat_bp
from .grammar_routes import grammar_bp
from .speaking_routes import speaking_bp
from .reading_routes import reading_bp
from .writing_routes import writing_bp
from .progress_routes import progress_bp
from .daily_words_routes import daily_words_bp
from .tips_routes import tips_bp
from .lingua_routes import lingua_bp
from .translation_routes import translation_bp
from .json_routes import json_bp  # Add this

__all__ = [
    'session_bp',
    'vocab_bp', 
    'chat_bp',
    'grammar_bp',
    'speaking_bp',
    'reading_bp',
    'writing_bp',
    'progress_bp',
    'daily_words_bp',
    'tips_bp',
    'lingua_bp',
    'translation_bp',
    'json_bp'  # Add this
]