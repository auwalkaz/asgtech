from flask import Blueprint, request, jsonify, session
from datetime import datetime
from services.ai_service import ai_service
from config import config
from storage.memory_store import store
from utils.fallbacks import get_fallback_phrases
import random

speaking_bp = Blueprint("speaking", __name__, url_prefix="/api")

@speaking_bp.route("/speaking/phrases", methods=["GET"])
def get_speaking_phrases():
    """Get AI-generated speaking phrases dynamically - always fresh"""
    language = request.args.get("language", session.get('language', 'en'))
    scenario = request.args.get("scenario", "greeting")
    count = int(request.args.get("count", 5))
    force_refresh = request.args.get("refresh", "true").lower() == "true"  # Default to true for fresh phrases
    
    # Optional: Short-term cache for same session (5 minutes only)
    session_cache_key = f"speaking_{language}_{scenario}_{datetime.now().strftime('%Y-%m-%d-%H-%M')[:15]}"  # 15 min window
    
    # Only use cache if not forcing refresh AND cache is from last 5 minutes
    if not force_refresh and session_cache_key in store.ai_generated_words:
        return jsonify({
            "success": True,
            "language": language,
            "scenario": scenario,
            "phrases": store.ai_generated_words[session_cache_key],
            "source": "cache"
        })
    
    lang_name = config.SUPPORTED_LANGUAGES.get(language, {}).get("name", language.upper())
    
    # Different prompt templates for variety
    prompt_templates = [
        f"""Generate {count} unique, natural, and conversational phrases for a {scenario} situation in {lang_name}.

Make them sound like real native speakers.
Include both formal and informal variations.

For each phrase, provide:
- phrase: the phrase in {lang_name}
- translation: English translation

Return ONLY valid JSON: {{"phrases": [{{"phrase": "", "translation": ""}}]}}""",

        f"""Create {count} creative and interesting {scenario}-related sentences in {lang_name} for language learners.

Focus on practical, everyday expressions that people actually use.
Add variety in sentence structures.

For each phrase, provide:
- phrase: the phrase in {lang_name}
- translation: English translation

Return ONLY valid JSON: {{"phrases": [{{"phrase": "", "translation": ""}}]}}""",

        f"""Generate {count} diverse {scenario} conversation phrases in {lang_name}.

Make them fresh and different from standard textbook phrases.
Include cultural nuances when appropriate.

For each phrase, provide:
- phrase: the phrase in {lang_name}
- translation: English translation

Return ONLY valid JSON: {{"phrases": [{{"phrase": "", "translation": ""}}]}}"""
    ]
    
    # Randomly select a prompt template for variety
    selected_prompt = random.choice(prompt_templates)
    
    try:
        # Use higher temperature for more creativity
        result = ai_service.generate_json(selected_prompt, temperature=0.85, max_tokens=800)
        phrases = result.get("phrases", [])
        
        # Store in short-term cache
        store.ai_generated_words[session_cache_key] = phrases
        
        return jsonify({
            "success": True,
            "language": language,
            "scenario": scenario,
            "phrases": phrases,
            "source": "ai_generated",
            "fresh": True
        })
        
    except Exception as e:
        print(f"AI generation error: {e}")
        # Return fallback but mark as not fresh
        return jsonify({
            "success": True,
            "language": language,
            "scenario": scenario,
            "phrases": get_fallback_phrases(language, scenario),
            "source": "fallback",
            "fresh": False
        })

@speaking_bp.route("/speaking/scenarios", methods=["GET"])
def get_speaking_scenarios():
    """Get available speaking scenarios"""
    scenarios = [
        {"id": "greeting", "name": "Greetings", "icon": "👋", "description": "Learn how to greet people"},
        {"id": "introduction", "name": "Self Introduction", "icon": "🙋", "description": "Introduce yourself"},
        {"id": "shopping", "name": "Shopping", "icon": "🛒", "description": "Shopping conversations"},
        {"id": "restaurant", "name": "Restaurant", "icon": "🍽️", "description": "Ordering food"},
        {"id": "travel", "name": "Travel", "icon": "✈️", "description": "Travel situations"},
        {"id": "hobbies", "name": "Hobbies", "icon": "🎨", "description": "Talk about free time activities"},
        {"id": "emergency", "name": "Emergency", "icon": "🚨", "description": "Emergency phrases"},
        {"id": "business", "name": "Business", "icon": "💼", "description": "Professional conversations"},
        {"id": "small_talk", "name": "Small Talk", "icon": "💬", "description": "Casual conversations"},
        {"id": "weather", "name": "Weather", "icon": "🌤️", "description": "Discuss weather conditions"},
        {"id": "family", "name": "Family", "icon": "👨‍👩‍👧", "description": "Talk about family members"},
        {"id": "work", "name": "Job Interview", "icon": "💼", "description": "Practice job interviews"}
    ]
    return jsonify({"success": True, "scenarios": scenarios})

@speaking_bp.route("/speaking/regenerate", methods=["POST"])
def regenerate_phrases():
    """Force regenerate new phrases for current scenario"""
    data = request.json
    language = data.get("language", session.get('language', 'en'))
    scenario = data.get("scenario", "greeting")
    count = data.get("count", 5)
    
    # Call the main endpoint with force_refresh=True
    return get_speaking_phrases()