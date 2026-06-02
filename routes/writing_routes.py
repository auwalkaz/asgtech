from flask import Blueprint, request, jsonify, session
from datetime import datetime
import random
import json
import os

# Import services
from services.ai_service import ai_service
from services.vocabulary_service import vocab_service
from services.word_service import word_service
from config import config

writing_bp = Blueprint("writing", __name__, url_prefix="/api")

# Helper function to load words from JSON files
def load_words_from_json(language, level='all', limit=50):
    """Load words directly from JSON files in the json folder"""
    # Dynamic path that works on local and Render
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_folder = os.path.join(os.path.dirname(current_dir), 'json')
    file_path = os.path.join(json_folder, f'wordbank_{language}.json')
    
    # Try alternative naming if not found
    if not os.path.exists(file_path):
        file_path = os.path.join(json_folder, f'{language}.json')
    
    if not os.path.exists(file_path):
        print(f"JSON file not found: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, dict) and 'words' in data:
            words_data = data['words']
        elif isinstance(data, list):
            words_data = data
        else:
            words_data = []
        
        # Filter by level if specified
        if level != 'all':
            words_data = [w for w in words_data if w.get('level', 'beginner') == level]
        
        # Limit the number of words
        words_data = words_data[:limit]
        
        return words_data
    except Exception as e:
        print(f"Error loading JSON for {language}: {e}")
        return []

# ==================== LANGUAGE LIST ENDPOINT ====================

@writing_bp.route("/words/list", methods=["GET"])
def get_available_languages():
    """Return list of available language word banks"""
    # Dynamic path to json folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_folder = os.path.join(os.path.dirname(current_dir), 'json')
    
    try:
        languages = []
        if os.path.exists(json_folder):
            for file in os.listdir(json_folder):
                if file.startswith('wordbank_') and file.endswith('.json'):
                    # Extract language code from wordbank_en.json
                    lang_code = file.replace('wordbank_', '').replace('.json', '')
                    languages.append(lang_code)
        
        if not languages:
            # Fallback languages if no JSON files found
            languages = ['en', 'es', 'fr', 'ar', 'zh', 'pt', 'sw', 'de', 'it']
        
        return jsonify({
            'success': True,
            'languages': sorted(languages)
        })
    except Exception as e:
        print(f"Error getting languages: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'languages': ['en']  # Fallback
        }), 500

# ==================== WORDS BY LANGUAGE ENDPOINT ====================

@writing_bp.route("/words/<language>", methods=["GET"])
def get_words_by_language(language):
    """Get words for a specific language directly from JSON files"""
    # Dynamic path that works on local and Render
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_folder = os.path.join(os.path.dirname(current_dir), 'json')
    file_path = os.path.join(json_folder, f'wordbank_{language}.json')
    
    # Try alternative filename if not found
    if not os.path.exists(file_path):
        file_path = os.path.join(json_folder, f'{language}.json')
    
    print(f"Looking for file: {file_path}")
    print(f"JSON folder exists: {os.path.exists(json_folder)}")
    
    if not os.path.exists(file_path):
        return jsonify({
            "success": False,
            "error": f"No word bank found for language: {language}",
            "file_tried": file_path,
            "words": []
        }), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, dict) and 'words' in data:
            words_data = data['words']
        elif isinstance(data, dict) and 'vocabulary' in data:
            words_data = data['vocabulary']
        elif isinstance(data, list):
            words_data = data
        else:
            words_data = []
        
        print(f"Loaded {len(words_data)} words for {language}")
        
        return jsonify({
            "success": True,
            "language": language,
            "words": words_data,
            "count": len(words_data)
        })
    except Exception as e:
        print(f"Error loading {language}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "words": []
        }), 500

# ==================== WRITING EXERCISES ====================

@writing_bp.route("/writing/exercises", methods=["GET"])
def get_writing_exercises():
    """Get writing exercises from JSON files"""
    language = request.args.get("language", session.get('language', 'en'))
    exercise_type = request.args.get("type", "spelling")
    level = request.args.get("level", "beginner")
    count = int(request.args.get("count", 5))
    
    items = []
    
    # First try to load from JSON files
    words_data = load_words_from_json(language, level, count * 2)
    
    if words_data:
        # Extract just the word strings
        for word in words_data:
            if isinstance(word, dict):
                word_text = word.get('word', '')
                if word_text:
                    items.append(word_text)
            else:
                items.append(str(word))
    
    # If JSON didn't have enough, try vocabulary service
    if len(items) < count:
        vocab_words = vocab_service.get_words(language, level, count * 2)
        if vocab_words:
            for word in vocab_words:
                if isinstance(word, dict):
                    word_text = word.get('word', '')
                    if word_text and word_text not in items:
                        items.append(word_text)
                else:
                    word_str = str(word)
                    if word_str not in items:
                        items.append(word_str)
    
    # Remove duplicates and limit
    items = list(dict.fromkeys(items))[:count]
    
    # If we don't have enough words, add fallbacks
    if len(items) < count:
        fallback_words = {
            'en': ['hello', 'world', 'beautiful', 'necessary', 'language', 'practice', 'learning', 'vocabulary'],
            'es': ['hola', 'mundo', 'hermoso', 'necesario', 'idioma', 'practicar', 'aprender'],
            'fr': ['bonjour', 'monde', 'beau', 'nécessaire', 'langue', 'pratiquer', 'apprendre'],
            'ar': ['مرحبا', 'عالم', 'جميل', 'ضروري', 'لغة', 'ممارسة', 'تعلم'],
            'pt': ['olá', 'mundo', 'bonito', 'necessário', 'idioma', 'praticar', 'aprender'],
            'de': ['hallo', 'welt', 'schön', 'notwendig', 'sprache', 'üben', 'lernen'],
            'it': ['ciao', 'mondo', 'bello', 'necessario', 'lingua', 'praticare', 'imparare'],
            'sw': ['jambo', 'dunia', 'nzuri', 'muhimu', 'lugha', 'kufanya mazoezi', 'kujifunza'],
            'zh': ['你好', '世界', '美丽', '必要', '语言', '练习', '学习']
        }
        
        fb_words = fallback_words.get(language, fallback_words['en'])
        while len(items) < count and fb_words:
            word = fb_words.pop(0)
            if word not in items:
                items.append(word)
    
    return jsonify({
        "success": True,
        "language": language,
        "type": exercise_type,
        "level": level,
        "items": items,
        "source": "json_files"
    })

# ==================== WORD BANK GENERATION ====================

@writing_bp.route("/words/bank/generate", methods=["GET"])
def generate_word_bank():
    """Get word bank for sentence building from JSON files"""
    language = request.args.get("language", session.get('language', 'en'))
    level = request.args.get("level", "beginner")
    theme = request.args.get("theme", None)
    
    words = []
    
    # Load from JSON files
    words_data = load_words_from_json(language, level, 20)
    
    if words_data:
        # Extract just the words
        for item in words_data:
            if isinstance(item, dict):
                word_text = item.get('word', '')
                if word_text and len(word_text) > 1:
                    words.append(word_text)
            else:
                words.append(str(item))
    
    # Try vocabulary service if needed
    if len(words) < 8:
        vocab_words = vocab_service.get_words(language, level, 15)
        if vocab_words:
            for word in vocab_words:
                if isinstance(word, dict):
                    word_text = word.get('word', '')
                    if word_text and word_text not in words:
                        words.append(word_text)
                else:
                    word_str = str(word)
                    if word_str not in words:
                        words.append(word_str)
    
    # Remove duplicates and limit
    words = list(dict.fromkeys(words))[:12]
    
    # If we still don't have enough, use fallback
    if len(words) < 8:
        fallback_words = {
            'beginner': ["I", "like", "to", "learn", "new", "words", "every", "day"],
            'intermediate': ["I", "would", "like", "to", "practice", "writing", "more", "often"],
            'advanced': ["Although", "learning", "is", "challenging", "it", "is", "rewarding"]
        }
        
        fb_words = fallback_words.get(level, fallback_words['beginner'])
        for w in fb_words:
            if w not in words:
                words.append(w)
            if len(words) >= 12:
                break
    
    theme_name = theme if theme else f"Vocabulary {level.title()} Level"
    
    return jsonify({
        "success": True,
        "theme": theme_name,
        "words": words[:12],
        "language": language,
        "level": level,
        "source": "json_files"
    })

# ==================== VOCABULARY WORDS ====================

@writing_bp.route("/words/vocabulary", methods=["GET"])
def get_vocabulary_words():
    """Get vocabulary words by language and level from JSON"""
    language = request.args.get("language", session.get('language', 'en'))
    level = request.args.get("level", "beginner")
    limit = int(request.args.get("limit", 20))
    
    # Load from JSON files
    words = load_words_from_json(language, level, limit)
    
    # If JSON didn't have any, try vocabulary service
    if not words:
        words = vocab_service.get_words(language, level, limit)
    
    return jsonify({
        "success": True,
        "language": language,
        "level": level,
        "words": words,
        "count": len(words),
        "source": "json_files" if words else "vocabulary_service"
    })

# ==================== SEARCH ====================

@writing_bp.route("/words/search", methods=["GET"])
def search_vocabulary():
    """Search for words in vocabulary from JSON"""
    language = request.args.get("language", session.get('language', 'en'))
    query = request.args.get("q", "").strip().lower()
    
    if not query:
        return jsonify({"success": False, "error": "No search query provided"}), 400
    
    results = []
    
    # Load all words from JSON
    words_data = load_words_from_json(language, 'all', 200)
    
    for item in words_data:
        if isinstance(item, dict):
            word = item.get('word', '').lower()
            meaning = item.get('meaning', '').lower()
            if query in word or query in meaning:
                results.append(item)
        else:
            if query in str(item).lower():
                results.append({'word': str(item)})
    
    # If no results from JSON, try vocabulary service
    if not results:
        results = vocab_service.search(language, query)
    
    return jsonify({
        "success": True,
        "language": language,
        "query": query,
        "results": results,
        "count": len(results)
    })

# ==================== THEMES ====================

@writing_bp.route("/words/themes", methods=["GET"])
def get_themes():
    """Get available themes/categories"""
    language = request.args.get("language", session.get('language', 'en'))
    
    themes = ['greetings', 'family', 'travel', 'food', 'work', 'hobbies', 'weather', 'shopping', 'nature', 'animals']
    
    return jsonify({
        "success": True,
        "language": language,
        "themes": themes
    })

# ==================== SENTENCE CHECKING ====================

@writing_bp.route("/check/sentence", methods=["POST"])
def check_sentence():
    """Check user's sentence for grammar and correctness"""
    try:
        data = request.json
        sentence = data.get("sentence", "").strip()
        language = data.get("language", "en")
        
        if not sentence:
            return jsonify({"error": "No sentence provided"}), 400
        
        # Basic checks for English
        words = sentence.split()
        has_capital = sentence[0].isupper() if sentence else False
        has_end_punct = sentence.endswith('.') or sentence.endswith('!') or sentence.endswith('?')
        has_min_words = len(words) >= 3
        
        # Common subjects and verbs for basic checking
        subjects = ['i', 'you', 'he', 'she', 'it', 'we', 'they', 'the', 'a', 'an']
        verbs = ['is', 'am', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 
                 'do', 'does', 'did', 'go', 'went', 'see', 'saw', 'make', 'made',
                 'love', 'like', 'want', 'need', 'learn', 'study', 'practice', 'write']
        
        has_subject = any(word.lower() in subjects for word in words[:3])
        has_verb = any(word.lower() in verbs for word in words)
        
        # Determine if sentence is correct (more lenient for learning)
        is_correct = has_min_words and has_capital and has_end_punct and (has_subject or len(words) >= 4)
        
        if is_correct:
            return jsonify({
                "success": True,
                "is_correct": True,
                "feedback": "Great sentence! Well structured! 🎉",
                "correction": "",
                "explanation": "Your sentence has good grammar and structure."
            })
        else:
            feedback_parts = []
            if len(words) < 3:
                feedback_parts.append("Add more words (need at least 3)")
            if not has_capital:
                feedback_parts.append("Start with a capital letter")
            if not has_end_punct:
                feedback_parts.append("End with punctuation (. ! ?)")
            if not has_subject and len(words) < 5:
                feedback_parts.append("Include a subject (I, you, he, she, we, they)")
            if not has_verb and len(words) < 5:
                feedback_parts.append("Include a verb (action word)")
            
            # Suggest correction
            corrected = sentence
            if not has_capital and corrected:
                corrected = corrected[0].upper() + corrected[1:]
            if not has_end_punct and corrected:
                corrected += '.'
            
            return jsonify({
                "success": True,
                "is_correct": False,
                "feedback": " ".join(feedback_parts),
                "correction": corrected,
                "explanation": "Your sentence needs some improvements. Keep practicing!"
            })
        
    except Exception as e:
        print(f"Sentence check error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "is_correct": False,
            "feedback": "Could not check sentence. Please try again."
        }), 500

# ==================== SPELLING CHECK ====================

@writing_bp.route("/check/spelling", methods=["POST"])
def check_spelling():
    """Check spelling of a word"""
    try:
        data = request.json
        user_word = data.get("word", "").strip().lower()
        correct_word = data.get("correct", "").strip().lower()
        language = data.get("language", "en")
        
        is_correct = user_word == correct_word
        
        if is_correct:
            feedback = f"Perfect! '{correct_word}' is spelled correctly! 🎉"
        else:
            # Helpful feedback
            if len(user_word) == len(correct_word):
                feedback = f"Not quite. The correct spelling is '{correct_word}'. Check the order of letters."
            elif len(user_word) > len(correct_word):
                feedback = f"Almost! The word '{correct_word}' has fewer letters. Try again!"
            else:
                feedback = f"Close! The word '{correct_word}' has more letters. Keep practicing!"
        
        return jsonify({
            "success": True,
            "is_correct": is_correct,
            "feedback": feedback,
            "correction": correct_word if not is_correct else ""
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== ACTIVITY SAVING ====================

@writing_bp.route("/activity/save", methods=["POST"])
def save_activity():
    """Save user activity progress"""
    try:
        data = request.json
        language = data.get("language", "en")
        activity_type = data.get("type", "writing_practice")
        points = data.get("points", 10)
        
        # Store in session
        if 'activities' not in session:
            session['activities'] = []
        
        session['activities'].append({
            'type': activity_type,
            'language': language,
            'points': points,
            'timestamp': datetime.now().isoformat()
        })
        session.modified = True
        
        return jsonify({
            "success": True, 
            "message": "Activity saved",
            "total_activities": len(session['activities'])
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== STATISTICS ====================

@writing_bp.route("/stats", methods=["GET"])
def get_writing_stats():
    """Get writing statistics"""
    try:
        activities = session.get('activities', [])
        total_points = sum(a.get('points', 0) for a in activities)
        
        return jsonify({
            "success": True,
            "stats": {
                "total_exercises": len(activities),
                "accuracy": 75,
                "streak": 0,
                "words_learned": 0,
                "total_points": total_points
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

print("✅ Writing routes loaded successfully with JSON file support!")