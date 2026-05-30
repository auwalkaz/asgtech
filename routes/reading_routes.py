from flask import Blueprint, request, jsonify, session
from services.ai_service import ai_service
from services.audio_service import audio_service
from config import config
from storage.memory_store import store
from utils.fallbacks import get_fallback_story

reading_bp = Blueprint("reading", __name__, url_prefix="/api")

@reading_bp.route("/reading/stories", methods=["GET"])
def get_reading_stories():
    """Get AI-generated short stories for reading comprehension"""
    language = request.args.get("language", "en")
    level = request.args.get("level", "beginner")
    count = int(request.args.get("count", 2))
    
    stories_list = []
    
    for i in range(count):
        cache_key = f"story_{language}_{level}_{i}"
        
        if cache_key in store.ai_generated_words:
            stories_list.append(store.ai_generated_words[cache_key])
            continue
        
        lang_name = config.SUPPORTED_LANGUAGES.get(language, {}).get("name", "English")
        
        prompt = f"""Write a short {level} level story in {lang_name} for language learners (#{i+1} of {count}).

Requirements:
- 50-80 words
- Simple vocabulary
- Present tense
- Include 2 comprehension questions

Return ONLY valid JSON:
{{
  "title": "Story Title",
  "content": "Story text here...",
  "questions": [
    {{"question": "Question 1?", "answer": "Answer 1"}},
    {{"question": "Question 2?", "answer": "Answer 2"}}
  ]
}}"""

        try:
            result = ai_service.generate_json(prompt, temperature=0.8, max_tokens=800)
            store.ai_generated_words[cache_key] = result
            stories_list.append(result)
        except Exception as e:
            print(f"Story generation error: {e}")
            stories_list.append(get_fallback_story(language, level, i))
    
    return jsonify({
        "success": True,
        "language": language,
        "level": level,
        "stories": stories_list,
        "source": "ai_generated"
    })

@reading_bp.route("/reading/pronounce", methods=["POST"])
def pronounce_text():
    """Generate audio for text"""
    try:
        data = request.json
        text = data.get("text", "")
        language = data.get("language", "en")
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        audio_result = audio_service.text_to_speech(text, language)
        
        return jsonify({
            "success": True,
            "audio": audio_result["audio"],
            "voice_used": audio_result["voice_used"],
            "text_length": audio_result["text_length"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@reading_bp.route("/reading/compare", methods=["POST"])
def compare_text():
    """Compare user's spoken text with expected text"""
    try:
        data = request.json
        user_text = data.get("user_text", "").strip()
        expected_text = data.get("expected_text", "").strip()
        language = data.get("language", "en")
        
        if not user_text or not expected_text:
            return jsonify({"error": "Missing text for comparison"}), 400
        
        prompt = f"""Compare these two texts:
EXPECTED: "{expected_text}"
USER SAID: "{user_text}"

Return JSON: {{"is_match": true/false, "accuracy": 0-100, "feedback": "feedback", "differences": [], "suggestion": ""}}"""

        result = ai_service.generate_json(prompt, temperature=0.3, max_tokens=300)
        
        return jsonify({
            "success": True,
            "is_match": result.get("is_match", False),
            "accuracy": result.get("accuracy", 0),
            "feedback": result.get("feedback", ""),
            "differences": result.get("differences", []),
            "suggestion": result.get("suggestion", "")
        })
        
    except Exception as e:
        # Simple fallback comparison
        is_match = user_text.lower() == expected_text.lower() or expected_text.lower() in user_text.lower()
        return jsonify({
            "success": True,
            "is_match": is_match,
            "accuracy": 80 if is_match else 40,
            "feedback": "Great job!" if is_match else "Keep practicing!",
            "differences": [],
            "suggestion": "Listen and try again."
        })