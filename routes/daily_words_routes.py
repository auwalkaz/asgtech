from flask import Blueprint, request, jsonify, session
from datetime import datetime
import random
from storage.memory_store import store
from services.ai_service import ai_service
from services.vocabulary_service import vocab_service
from utils.fallbacks import get_fallback_words_with_phrases
from config import config  # Add this import

daily_words_bp = Blueprint("daily_words", __name__, url_prefix="/api")

@daily_words_bp.route("/daily-words", methods=["GET"])
def daily_words():
    """Get AI-generated daily vocabulary words (10 new words every day)"""
    language = request.args.get("language", session.get('language', 'en'))
    use_static = request.args.get("static", "false").lower() == "true"
    level = request.args.get("level", "beginner")
    today = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"daily_{today}_{language}"
    lang_name = config.SUPPORTED_LANGUAGES.get(language, {}).get("name", "English")
    
    # Option 1: Use static vocabulary from JSON files
    if use_static:
        static_words = vocab_service.get_random_words(language, level, 10)
        if static_words:
            formatted = []
            for w in static_words:
                formatted.append({
                    "word": w.get("word"),
                    "meaning": w.get("meaning"),
                    "example": w.get("example"),
                    "pronunciation": w.get("pronunciation", w.get("word")),
                    "common_phrases": [w.get("tip", "Learn this word!")],
                    "source": "static_vocab",
                    "id": w.get("id")
                })
            return jsonify({
                "success": True,
                "date": today,
                "language": language,
                "language_name": lang_name,
                "level": level,
                "words": formatted,
                "source": "static"
            })
    
    # Option 2: Use cached AI-generated words
    if cache_key in store.daily_words:
        return jsonify({
            "success": True,
            "date": today,
            "language": language,
            "language_name": lang_name,
            "words": store.daily_words[cache_key],
            "source": "cache"
        })
    
    # Option 3: Generate new AI words
    prompt = f"""Generate 10 useful vocabulary words for someone learning {lang_name}.
Each word should be common and useful for daily conversation.

For each word, provide:
- word: the word in {lang_name}
- meaning: English meaning
- example: example sentence in {lang_name}
- pronunciation: simple phonetic guide
- common_phrases: 2-3 common phrases using this word

Return ONLY valid JSON:
{{"words": [
  {{"word": "", "meaning": "", "example": "", "pronunciation": "", "common_phrases": []}}
]}}"""

    try:
        result = ai_service.generate_json(prompt, temperature=0.8, max_tokens=2000)
        words = result.get("words", [])
        store.daily_words[cache_key] = words
        
        return jsonify({
            "success": True,
            "date": today,
            "language": language,
            "language_name": lang_name,
            "words": words,
            "source": "ai_generated"
        })
        
    except Exception as e:
        print(f"Error generating words: {e}")
        default_words = get_fallback_words_with_phrases(language)
        store.daily_words[cache_key] = default_words[:10]
        return jsonify({
            "success": True,
            "date": today,
            "language": language,
            "language_name": lang_name,
            "words": default_words[:10],
            "source": "fallback",
            "warning": "Using default words"
        })