# AI Service
from .ai_service import ai_service, AIService

# Vocabulary Service
from .vocabulary_service import vocab_service, VocabularyService

# Word Service (doesn't depend on WordNet)
from .word_service import word_service, WordService

# Audio Service
from .audio_service import audio_service, AudioService

# WordNet Service - try to import but don't fail if not available
try:
    from .wordnet_service import wordnet_service, WordNetService
    print("✅ WordNetService loaded")
except ImportError as e:
    print(f"⚠️ WordNetService not available: {e}")
    wordnet_service = None
    WordNetService = None

# Export all available services
__all__ = [
    'ai_service', 'AIService',
    'vocab_service', 'VocabularyService',
    'word_service', 'WordService',
    'audio_service', 'AudioService'
]

# Only add WordNet if available
if wordnet_service is not None:
    __all__.extend(['wordnet_service', 'WordNetService'])
