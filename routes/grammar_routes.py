from flask import Blueprint, request, jsonify, session
from services.ai_service import ai_service
from config import config

grammar_bp = Blueprint("grammar", __name__, url_prefix="/api")

@grammar_bp.route("/grammar/correct", methods=["POST"])
def grammar_correction():
    """AI-powered grammar correction for sentences"""
    try:
        data = request.json
        sentence = data.get("sentence", "").strip()
        language = data.get("language", "en")
        
        if not sentence:
            return jsonify({"error": "No sentence provided"}), 400
        
        lang_name = config.SUPPORTED_LANGUAGES.get(language, {}).get("name", "English")
        
        prompt = f"""You are an expert {lang_name} grammar teacher. Correct the following sentence:

Sentence: "{sentence}"

Return ONLY valid JSON in this exact format:
{{
  "is_correct": true/false,
  "correction": "corrected sentence here",
  "explanation": "brief explanation of the error",
  "grammar_rule": "simple rule to remember",
  "examples": [
    {{"wrong": "example mistake", "correct": "example correction"}}
  ]
}}"""

        result = ai_service.generate_json(prompt, temperature=0.3, max_tokens=500)
        
        return jsonify({
            "success": True,
            "original": sentence,
            "is_correct": result.get("is_correct", False),
            "correction": result.get("correction", sentence),
            "explanation": result.get("explanation", ""),
            "grammar_rule": result.get("grammar_rule", ""),
            "examples": result.get("examples", [])
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@grammar_bp.route("/grammar/check", methods=["POST"])
def grammar_check():
    """Check grammar of a sentence"""
    try:
        data = request.json
        sentence = data.get("sentence", "").strip()
        language = data.get("language", "en")
        
        if not sentence:
            return jsonify({"error": "No sentence provided"}), 400
        
        lang_name = config.SUPPORTED_LANGUAGES.get(language, {}).get("name", "English")
        
        prompt = f"""Check this {lang_name} sentence for grammar errors:
        
Sentence: "{sentence}"

If correct, praise the user.
If incorrect, explain what's wrong and show the corrected version.
Keep response short and encouraging (max 2 sentences)."""

        result = ai_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200
        )
        
        return jsonify({
            "success": True,
            "feedback": result
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@grammar_bp.route("/grammar/ask-ai", methods=["POST"])
def ask_grammar_ai():
    """AI endpoint for parts of speech questions"""
    try:
        data = request.json
        part_of_speech = data.get("part", "noun")
        question = data.get("question", f"Teach me about {part_of_speech}s")
        
        prompt = f"""You are an expert English teacher. ONLY teach about {part_of_speech}s.

Student's question: {question}

Please provide:
1. A clear definition of {part_of_speech}s
2. 5 examples with full sentences
3. A simple memory tip
4. A practice exercise for the student

Keep it friendly, encouraging, and under 300 words. Use emojis."""

        response = ai_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600
        )
        
        return jsonify({
            "success": True,
            "response": response,
            "part": part_of_speech
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500