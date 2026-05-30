from flask import Blueprint, request, jsonify, send_from_directory
import os
import json
from pathlib import Path

json_bp = Blueprint("json", __name__, url_prefix="/api/json")

# Path to JSON files
JSON_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'json')

# Language mapping
LANGUAGE_MAP = {
    'en': 'wordbank_en.json',
    'ar': 'wordbank_ar.json',
    'fr': 'wordbank_fr.json',
    'es': 'wordbank_es.json',
    'pt': 'wordbank_pt.json',
    'sw': 'wordbank_sw.json',
    'de': 'wordbank_de.json',
    'it': 'wordbank_it.json',
    'zh': 'wordbank_zh.json',
    'hi': 'wordbank_hi.json'
}

@json_bp.route("/languages", methods=["GET"])
def list_languages():
    """List all available languages"""
    try:
        available_languages = []
        for code, filename in LANGUAGE_MAP.items():
            filepath = os.path.join(JSON_FOLDER, filename)
            if os.path.exists(filepath):
                available_languages.append({
                    "code": code,
                    "file": filename,
                    "exists": True,
                    "size": os.path.getsize(filepath)
                })
            else:
                available_languages.append({
                    "code": code,
                    "file": filename,
                    "exists": False,
                    "size": 0
                })
        
        return jsonify({
            "success": True,
            "languages": available_languages,
            "folder": JSON_FOLDER
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@json_bp.route("/<language>", methods=["GET"])
def get_vocabulary(language):
    """Get vocabulary for a specific language"""
    try:
        if language not in LANGUAGE_MAP:
            return jsonify({
                "success": False,
                "error": f"Language '{language}' not supported. Available: {list(LANGUAGE_MAP.keys())}"
            }), 400
        
        filename = LANGUAGE_MAP[language]
        filepath = os.path.join(JSON_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                "success": False,
                "error": f"Vocabulary file for '{language}' not found at {filepath}"
            }), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Filter by level if requested
        level = request.args.get("level", "all")
        if level != "all":
            filtered_data = [item for item in data if item.get('level') == level]
        else:
            filtered_data = data
        
        return jsonify({
            "success": True,
            "language": language,
            "count": len(filtered_data),
            "words": filtered_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@json_bp.route("/<language>/level/<level>", methods=["GET"])
def get_vocabulary_by_level(language, level):
    """Get vocabulary for specific language and level"""
    try:
        if language not in LANGUAGE_MAP:
            return jsonify({"success": False, "error": f"Language '{language}' not supported"}), 400
        
        filename = LANGUAGE_MAP[language]
        filepath = os.path.join(JSON_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": f"Vocabulary file not found"}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        filtered_data = [item for item in data if item.get('level') == level]
        
        return jsonify({
            "success": True,
            "language": language,
            "level": level,
            "count": len(filtered_data),
            "words": filtered_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@json_bp.route("/search", methods=["GET"])
def search_vocabulary():
    """Search for a word across all languages"""
    try:
        query = request.args.get("q", "").strip().lower()
        language = request.args.get("language")
        
        if not query:
            return jsonify({"success": False, "error": "Search query required"}), 400
        
        results = []
        
        languages_to_search = [language] if language else list(LANGUAGE_MAP.keys())
        
        for lang in languages_to_search:
            if lang not in LANGUAGE_MAP:
                continue
            
            filename = LANGUAGE_MAP[lang]
            filepath = os.path.join(JSON_FOLDER, filename)
            
            if not os.path.exists(filepath):
                continue
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data:
                word = item.get('word', '').lower()
                meaning = item.get('meaning', '').lower()
                if query in word or query in meaning:
                    item_copy = item.copy()
                    item_copy['language'] = lang
                    results.append(item_copy)
        
        return jsonify({
            "success": True,
            "query": query,
            "count": len(results),
            "results": results[:50]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@json_bp.route("/stats", methods=["GET"])
def get_stats():
    """Get statistics about all vocabulary files"""
    try:
        stats = {}
        total_words = 0
        
        for code, filename in LANGUAGE_MAP.items():
            filepath = os.path.join(JSON_FOLDER, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stats[code] = {
                        "filename": filename,
                        "total_words": len(data),
                        "levels": {
                            "beginner": len([w for w in data if w.get('level') == 'beginner']),
                            "intermediate": len([w for w in data if w.get('level') == 'intermediate']),
                            "advanced": len([w for w in data if w.get('level') == 'advanced'])
                        }
                    }
                    total_words += len(data)
            else:
                stats[code] = {
                    "filename": filename,
                    "total_words": 0,
                    "exists": False
                }
        
        return jsonify({
            "success": True,
            "stats": stats,
            "total_words": total_words,
            "folder": JSON_FOLDER
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

print("✅ JSON Routes loaded successfully!")
print(f"📁 JSON folder: {JSON_FOLDER}")
print(f"📚 Supported languages: {list(LANGUAGE_MAP.keys())}")
