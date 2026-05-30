from flask import Blueprint, request, jsonify
from services.vocabulary_service import vocab_service

lingua_bp = Blueprint("lingua", __name__, url_prefix="/api/lingua")

@lingua_bp.route("/vocabulary", methods=["GET"])
def get_vocabulary():
    try:
        language = request.args.get("language", "en")
        level = request.args.get("level", "beginner")
        limit = int(request.args.get("limit", 50))
        
        words = vocab_service.get_words(language, level, limit)
        
        return jsonify({
            "success": True,
            "language": language,
            "level": level,
            "count": len(words),
            "words": words
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@lingua_bp.route("/vocabulary/random", methods=["GET"])
def get_random_vocabulary():
    try:
        language = request.args.get("language", "en")
        level = request.args.get("level", "beginner")
        count = min(int(request.args.get("count", 10)), 30)
        
        words = vocab_service.get_random_words(language, level, count)
        
        return jsonify({
            "success": True,
            "language": language,
            "level": level,
            "count": len(words),
            "words": words
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@lingua_bp.route("/grammar/parts-of-speech", methods=["GET"])
def get_parts_of_speech():
    try:
        language = request.args.get("language", "en")
        
        parts_of_speech = {
            "en": [
                {"id": "noun", "name": "Noun", "icon": "📖", "definition": "Names a person, place, thing, or idea", 
                 "examples": [{"word": "cat", "sentence": "The cat sleeps."}], "commonWords": ["dog", "house", "car"]},
                {"id": "verb", "name": "Verb", "icon": "⚡", "definition": "Shows action or state of being",
                 "examples": [{"word": "run", "sentence": "I run daily."}], "commonWords": ["run", "eat", "sleep"]},
                {"id": "adjective", "name": "Adjective", "icon": "🎨", "definition": "Describes a noun",
                 "examples": [{"word": "beautiful", "sentence": "Beautiful smile."}], "commonWords": ["good", "big", "small"]},
                {"id": "adverb", "name": "Adverb", "icon": "🏃", "definition": "Describes a verb",
                 "examples": [{"word": "quickly", "sentence": "He runs quickly."}], "commonWords": ["quickly", "slowly"]}
            ],
            "ar": [
                {"id": "noun", "name": "اسم", "icon": "📖", "definition": "يسمي شخصًا أو مكانًا أو شيئًا أو فكرة",
                 "examples": [{"word": "قطة", "sentence": "القطة تنام."}], "commonWords": ["كلب", "منزل", "سيارة"]},
                {"id": "verb", "name": "فعل", "icon": "⚡", "definition": "يظهر فعلًا أو حالة",
                 "examples": [{"word": "يركض", "sentence": "أركض يوميًا."}], "commonWords": ["يركض", "يأكل", "ينام"]}
            ]
        }
        
        result = parts_of_speech.get(language, parts_of_speech["en"])
        
        return jsonify({
            "success": True,
            "language": language,
            "parts": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@lingua_bp.route("/quiz/generate", methods=["GET"])
def generate_quiz():
    try:
        language = request.args.get("language", "en")
        count = min(int(request.args.get("count", 5)), 10)
        
        quizzes = {
            "en": [
                {"sentence": "I ___ to school every day.", "blankWord": "go", "correctPos": "verb", 
                 "options": ["noun", "verb", "adjective", "adverb"], "hint": "Action word"},
                {"sentence": "The ___ is sleeping on the bed.", "blankWord": "cat", "correctPos": "noun", 
                 "options": ["noun", "verb", "adjective", "adverb"], "hint": "A furry pet"}
            ],
            "ar": [
                {"sentence": "أنا ___ إلى المدرسة كل يوم.", "blankWord": "أذهب", "correctPos": "verb", 
                 "options": ["اسم", "فعل", "صفة", "ظرف"], "hint": "كلمة تدل على حركة"}
            ]
        }
        
        lang_quizzes = quizzes.get(language, quizzes["en"])
        
        return jsonify({
            "success": True,
            "language": language,
            "questions": lang_quizzes[:count],
            "total": len(lang_quizzes[:count])
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

print("✅ Lingua routes loaded successfully!")
