from flask import Blueprint, request, jsonify, session
import random
from storage.memory_store import store
from services.vocabulary_service import vocab_service
from services.ai_service import ai_service
from utils.helpers import calculate_mastery, needs_review, needs_vocab_review
from datetime import datetime, timedelta
from config import config

vocab_bp = Blueprint("vocab", __name__, url_prefix="/api/vocabulary")

# Storage for user vocabulary (separate from store for user-added words)
VOCABULARY_STORAGE = {}
PRACTICE_HISTORY = {}
USER_STREAKS = {}

# ================= STATIC VOCABULARY FROM JSON =================

@vocab_bp.route("/static", methods=["GET"])
def get_static_vocab():
    """Get static vocabulary from JSON files"""
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

@vocab_bp.route("/static/random", methods=["GET"])
def get_random_static_words():
    """Get random static vocabulary words"""
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

@vocab_bp.route("/static/search", methods=["GET"])
def search_static_vocab():
    """Search static vocabulary"""
    language = request.args.get("language", "en")
    query = request.args.get("q", "").strip().lower()
    
    if not query:
        return jsonify({"success": False, "error": "Search query required"}), 400
    
    results = vocab_service.search(language, query)
    
    return jsonify({
        "success": True,
        "query": query,
        "count": len(results),
        "results": results
    })

@vocab_bp.route("/static/word/<word_id>", methods=["GET"])
def get_static_word_by_id(word_id):
    """Get a specific static word by ID"""
    language = request.args.get("language", "en")
    
    word = vocab_service.get_word_by_id(language, word_id)
    
    if word:
        return jsonify({"success": True, "word": word})
    return jsonify({"success": False, "error": "Word not found"}), 404

@vocab_bp.route("/static/stats", methods=["GET"])
def get_static_stats():
    """Get static vocabulary statistics"""
    stats = vocab_service.get_stats()
    return jsonify({"success": True, "stats": stats})

# ================= USER VOCABULARY ROUTES =================

@vocab_bp.route("/user/words", methods=["GET"])
def get_user_words():
    """Get user's saved vocabulary words"""
    session_id = session.get('user_id', 'default')
    language = request.args.get("language", "en")
    
    user_vocab = VOCABULARY_STORAGE.get(session_id, {})
    
    words = []
    for word_id, word_data in user_vocab.items():
        if word_data.get('language') == language:
            words.append(word_data)
    
    return jsonify({
        "success": True,
        "words": words,
        "total": len(words)
    })

@vocab_bp.route("/user/words", methods=["POST"])
def add_user_word():
    """Add a word to user's vocabulary"""
    session_id = session.get('user_id', 'default')
    data = request.json
    
    if not data.get('word') or not data.get('meaning'):
        return jsonify({"success": False, "error": "Word and meaning required"}), 400
    
    word_id = f"vocab_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
    
    if session_id not in VOCABULARY_STORAGE:
        VOCABULARY_STORAGE[session_id] = {}
    
    VOCABULARY_STORAGE[session_id][word_id] = {
        "id": word_id,
        "word": data['word'],
        "meaning": data['meaning'],
        "example": data.get('example', ''),
        "pronunciation": data.get('pronunciation', ''),
        "part_of_speech": data.get('part_of_speech', 'noun'),
        "language": data.get('language', 'en'),
        "difficulty": data.get('difficulty', 1),
        "mastery_level": 0,
        "review_count": 0,
        "correct_count": 0,
        "incorrect_count": 0,
        "last_reviewed": None,
        "created_at": datetime.now().isoformat()
    }
    
    # Update progress in store
    store.update_progress(session_id, data.get('language', 'en'), "word_learned")
    
    return jsonify({
        "success": True,
        "message": f"Added '{data['word']}' to your vocabulary",
        "word_id": word_id
    })

@vocab_bp.route("/user/words/<word_id>", methods=["DELETE"])
def delete_user_word(word_id):
    """Delete a word from user's vocabulary"""
    session_id = session.get('user_id', 'default')
    
    if session_id in VOCABULARY_STORAGE and word_id in VOCABULARY_STORAGE[session_id]:
        word_name = VOCABULARY_STORAGE[session_id][word_id].get('word', 'Unknown')
        del VOCABULARY_STORAGE[session_id][word_id]
        return jsonify({"success": True, "message": f"Deleted '{word_name}'"})
    
    return jsonify({"success": False, "error": "Word not found"}), 404

@vocab_bp.route("/user/practice/record", methods=["POST"])
def record_practice():
    """Record practice result for a word"""
    session_id = session.get('user_id', 'default')
    data = request.json
    word_id = data.get('word_id')
    correct = data.get('correct', False)
    
    if not word_id:
        return jsonify({"success": False, "error": "word_id required"}), 400
    
    if session_id not in VOCABULARY_STORAGE or word_id not in VOCABULARY_STORAGE[session_id]:
        return jsonify({"success": False, "error": "Word not found"}), 404
    
    word = VOCABULARY_STORAGE[session_id][word_id]
    
    word['review_count'] = word.get('review_count', 0) + 1
    if correct:
        word['correct_count'] = word.get('correct_count', 0) + 1
    else:
        word['incorrect_count'] = word.get('incorrect_count', 0) + 1
    
    word['last_reviewed'] = datetime.now().isoformat()
    
    # Calculate new mastery level
    word['mastery_level'] = calculate_mastery(
        word['correct_count'],
        word['incorrect_count'],
        word['review_count']
    )
    
    # Save practice history
    if session_id not in PRACTICE_HISTORY:
        PRACTICE_HISTORY[session_id] = []
    
    PRACTICE_HISTORY[session_id].append({
        "word_id": word_id,
        "word": word['word'],
        "correct": correct,
        "practice_type": data.get('practice_type', 'quiz'),
        "language": word['language'],
        "timestamp": datetime.now().isoformat()
    })
    
    # Update streak
    streak_key = f"{session_id}_{word['language']}"
    today = datetime.now().date().isoformat()
    if streak_key not in USER_STREAKS:
        USER_STREAKS[streak_key] = {"streak": 0, "last_date": None}
    
    if USER_STREAKS[streak_key].get("last_date") != today:
        if USER_STREAKS[streak_key].get("last_date") == (datetime.now().date() - timedelta(days=1)).isoformat():
            USER_STREAKS[streak_key]["streak"] += 1
        else:
            USER_STREAKS[streak_key]["streak"] = 1
        USER_STREAKS[streak_key]["last_date"] = today
    
    return jsonify({
        "success": True,
        "mastery_level": word['mastery_level'],
        "review_count": word['review_count'],
        "message": "Great job! 🎉" if correct else "Keep practicing! 💪"
    })

# ================= COMPATIBILITY ENDPOINTS (for frontend) =================

@vocab_bp.route("/words", methods=["GET"])
def get_words_compatibility():
    """Compatibility GET endpoint for frontend - gets words with static vocabulary included"""
    try:
        session_id = session.get('user_id', 'default')
        language = request.args.get("language", "en")
        status = request.args.get("status", "all")
        search = request.args.get("search", "")
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        
        user_vocab = VOCABULARY_STORAGE.get(session_id, {})
        
        words_list = []
        
        # Add user's custom words
        for word_id, word_data in user_vocab.items():
            if word_data.get('language') != language:
                continue
            
            mastery = word_data.get('mastery_level', 0)
            
            if status == 'learning' and mastery >= 3:
                continue
            if status == 'mastered' and mastery < 3:
                continue
            if status == 'review' and not needs_review(word_data.get('last_reviewed'), mastery):
                continue
            
            if search:
                search_lower = search.lower()
                if search_lower not in word_data.get('word', '').lower() and search_lower not in word_data.get('meaning', '').lower():
                    continue
            
            words_list.append({
                "id": word_id,
                "word": word_data.get('word'),
                "meaning": word_data.get('meaning'),
                "example": word_data.get('example', ''),
                "pronunciation": word_data.get('pronunciation', ''),
                "part_of_speech": word_data.get('part_of_speech', ''),
                "difficulty": word_data.get('difficulty', 1),
                "mastery_level": mastery,
                "review_count": word_data.get('review_count', 0),
                "last_reviewed": word_data.get('last_reviewed'),
                "created_at": word_data.get('created_at')
            })
        
        # Add static vocabulary from JSON files (as suggested words)
        static_words = vocab_service.get_words(language, "beginner", 50)
        for static_word in static_words:
            # Check if word already exists in user's vocabulary
            if not any(w.get('word', '').lower() == static_word.get('word', '').lower() for w in words_list):
                if search and search.lower() not in static_word.get('word', '').lower():
                    continue
                words_list.append({
                    "id": f"static_{static_word.get('id')}",
                    "word": static_word.get('word'),
                    "meaning": static_word.get('meaning'),
                    "example": static_word.get('example', ''),
                    "pronunciation": static_word.get('pronunciation', ''),
                    "part_of_speech": static_word.get('part_of_speech', ''),
                    "difficulty": 1,
                    "mastery_level": 0,
                    "review_count": 0,
                    "correct_count": 0,
                    "incorrect_count": 0,
                    "last_reviewed": None,
                    "created_at": datetime.now().isoformat(),
                    "is_static": True
                })
        
        # Sort by mastery level
        words_list.sort(key=lambda x: (x.get('mastery_level', 0), x.get('last_reviewed', '')))
        
        total = len(words_list)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = words_list[start:end]
        
        return jsonify({
            "success": True,
            "words": paginated,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1
        })
        
    except Exception as e:
        print(f"Error getting words: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@vocab_bp.route("/words", methods=["POST"])
def add_word_compatibility():
    """Compatibility POST endpoint for frontend - adds a word"""
    try:
        session_id = session.get('user_id', 'default')
        data = request.json
        
        if not data.get('word') or not data.get('meaning'):
            return jsonify({"success": False, "error": "Word and meaning required"}), 400
        
        # Check if word already exists
        user_vocab = VOCABULARY_STORAGE.get(session_id, {})
        for existing_word in user_vocab.values():
            if existing_word.get('word', '').lower() == data['word'].lower():
                return jsonify({"success": False, "error": f"Word '{data['word']}' already exists in your vocabulary"}), 400
        
        word_id = f"vocab_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
        
        if session_id not in VOCABULARY_STORAGE:
            VOCABULARY_STORAGE[session_id] = {}
        
        VOCABULARY_STORAGE[session_id][word_id] = {
            "id": word_id,
            "word": data['word'],
            "meaning": data['meaning'],
            "example": data.get('example', ''),
            "pronunciation": data.get('pronunciation', ''),
            "part_of_speech": data.get('part_of_speech', 'noun'),
            "language": data.get('language', 'en'),
            "difficulty": data.get('difficulty', 1),
            "mastery_level": 0,
            "review_count": 0,
            "correct_count": 0,
            "incorrect_count": 0,
            "last_reviewed": None,
            "created_at": datetime.now().isoformat(),
            "source": data.get('source', 'user_added')
        }
        
        # Update progress in store
        store.update_progress(session_id, data.get('language', 'en'), "word_learned")
        
        return jsonify({
            "success": True,
            "message": f"Added '{data['word']}' to your vocabulary",
            "word_id": word_id
        })
        
    except Exception as e:
        print(f"Error adding word: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ================= QUIZ ENDPOINTS =================

@vocab_bp.route("/quiz/generate", methods=["POST"])
def generate_quiz():
    """Generate a quiz from user's vocabulary"""
    try:
        session_id = session.get('user_id', 'default_user')
        data = request.json
        language = data.get('language', session.get('language', 'en'))
        word_count = min(data.get('word_count', 10), 20)
        
        if session_id not in VOCABULARY_STORAGE or not VOCABULARY_STORAGE[session_id]:
            return jsonify({"success": False, "error": "No words in vocabulary. Add some words first!"}), 404
        
        user_words = VOCABULARY_STORAGE[session_id]
        eligible_words = []
        
        for word_id, word_data in user_words.items():
            if word_data.get('language') != language:
                continue
            
            # Priority for words that need review
            priority = (5 - word_data.get('mastery_level', 0)) * 10
            if word_data.get('last_reviewed'):
                try:
                    days_since = (datetime.now() - datetime.fromisoformat(word_data['last_reviewed'])).days
                    priority += days_since * 5
                except:
                    priority += 50
            else:
                priority += 50
            
            eligible_words.append({
                "id": word_id,
                "word": word_data['word'],
                "meaning": word_data['meaning'],
                "example": word_data.get('example', ''),
                "priority": priority
            })
        
        if len(eligible_words) < 3:
            return jsonify({"success": False, "error": f"Add at least 3 words to create a quiz. You have {len(eligible_words)} words."}), 404
        
        eligible_words.sort(key=lambda x: x['priority'], reverse=True)
        selected = eligible_words[:word_count]
        
        questions = []
        for word in selected:
            other_meanings = [w['meaning'] for w in eligible_words if w['id'] != word['id']]
            random.shuffle(other_meanings)
            distractors = other_meanings[:3]
            
            while len(distractors) < 3:
                distractors.append("Different meaning")
            
            options = [word['meaning']] + distractors
            random.shuffle(options)
            
            questions.append({
                "id": word['id'],
                "word": word['word'],
                "question": f"What is the meaning of '{word['word']}'?",
                "options": options,
                "correct_answer": word['meaning'],
                "example": word['example']
            })
        
        return jsonify({
            "success": True,
            "questions": questions,
            "total": len(questions)
        })
        
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ================= AI POWERED ENDPOINTS =================

@vocab_bp.route("/lookup", methods=["POST"])
def lookup_word():
    """AI-powered word lookup to get correct meaning"""
    try:
        data = request.json
        word = data.get("word", "").strip()
        language = data.get("language", "en")
        
        if not word:
            return jsonify({"success": False, "error": "No word provided"}), 400
        
        lang_name = config.SUPPORTED_LANGUAGES.get(language, {}).get("name", "English")
        
        prompt = f"""You are a {lang_name} dictionary. Provide the definition for the word "{word}".

Return ONLY valid JSON in this format:
{{
  "word": "{word}",
  "meaning": "clear definition in English",
  "example": "example sentence using the word",
  "part_of_speech": "noun/verb/adjective/adverb"
}}"""

        if ai_service.client:
            try:
                result = ai_service.generate_json(prompt, temperature=0.3, max_tokens=300)
                
                return jsonify({
                    "success": True,
                    "word": result.get("word", word),
                    "meaning": result.get("meaning", f"Definition of {word}"),
                    "example": result.get("example", f"This is an example using the word '{word}'."),
                    "part_of_speech": result.get("part_of_speech", "noun")
                })
            except Exception as e:
                print(f"AI lookup error: {e}")
        
        # Fallback
        return jsonify({
            "success": True,
            "word": word,
            "meaning": f"The meaning of '{word}' in {lang_name}",
            "example": f"Example sentence using '{word}'.",
            "part_of_speech": "noun",
            "source": "fallback"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@vocab_bp.route("/verify-meaning", methods=["POST"])
def verify_meaning():
    """Check if user's meaning is correct, close, or wrong"""
    try:
        data = request.json
        word = data.get("word", "").strip()
        user_meaning = data.get("meaning", "").strip()
        language = data.get("language", "en")
        
        if not word or not user_meaning:
            return jsonify({"success": False, "error": "Missing word or meaning"}), 400
        
        lang_name = config.SUPPORTED_LANGUAGES.get(language, {}).get("name", "English")
        
        prompt = f"""You are a {lang_name} language teacher. Compare the user's definition with the correct definition.

Word: "{word}"
User's definition: "{user_meaning}"

Evaluate:
1. Is the user's meaning completely correct? (exact match)
2. Is it partially correct? (close, has some key elements)
3. Is it wrong? (completely different meaning)

Return ONLY valid JSON:
{{
  "status": "exact" or "partial" or "wrong",
  "correct_meaning": "the complete correct definition",
  "score": 0-100,
  "feedback": "helpful feedback for the user",
  "whats_missing": "what the user missed (for partial)",
  "suggestion": "how to improve the definition"
}}"""

        if ai_service.client:
            try:
                result = ai_service.generate_json(prompt, temperature=0.3, max_tokens=400)
                
                return jsonify({
                    "success": True,
                    "status": result.get("status", "wrong"),
                    "correct_meaning": result.get("correct_meaning", ""),
                    "score": result.get("score", 0),
                    "feedback": result.get("feedback", ""),
                    "whats_missing": result.get("whats_missing", ""),
                    "suggestion": result.get("suggestion", "")
                })
            except Exception as e:
                print(f"Verification error: {e}")
        
        # Simple fallback
        return jsonify({
            "success": True,
            "status": "partial",
            "correct_meaning": f"The definition of '{word}'",
            "score": 50,
            "feedback": "Keep practicing!",
            "whats_missing": "Review the definition",
            "suggestion": "Use a dictionary for accurate definitions"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ================= STATISTICS ENDPOINTS =================

@vocab_bp.route("/stats", methods=["GET"])
def get_vocabulary_stats():
    """Get vocabulary statistics for dashboard"""
    try:
        session_id = session.get('user_id', 'default_user')
        language = request.args.get("language", "en")
        
        if session_id not in VOCABULARY_STORAGE or not VOCABULARY_STORAGE[session_id]:
            return jsonify({
                "success": True,
                "stats": {
                    "total_words": 0,
                    "mastered_words": 0,
                    "learning_words": 0,
                    "total_practices": 0,
                    "average_accuracy": 0,
                    "streak_days": 0,
                    "weekly_progress": 0
                }
            })
        
        total_words = 0
        mastered_words = 0
        learning_words = 0
        total_practices = 0
        total_correct = 0
        weekly_progress = 0
        week_ago = datetime.now() - timedelta(days=7)
        
        for word_data in VOCABULARY_STORAGE[session_id].values():
            if word_data.get('language') != language:
                continue
            
            total_words += 1
            mastery = word_data.get('mastery_level', 0)
            if mastery >= 3:
                mastered_words += 1
            elif mastery > 0:
                learning_words += 1
            
            total_practices += word_data.get('review_count', 0)
            total_correct += word_data.get('correct_count', 0)
            
            last_reviewed = word_data.get('last_reviewed')
            if last_reviewed:
                try:
                    last_date = datetime.fromisoformat(last_reviewed)
                    if last_date >= week_ago:
                        weekly_progress += 1
                except:
                    pass
        
        avg_accuracy = round((total_correct / total_practices) * 100, 1) if total_practices > 0 else 0
        
        streak_key = f"{session_id}_{language}"
        streak_data = USER_STREAKS.get(streak_key, {"streak": 0})
        
        return jsonify({
            "success": True,
            "stats": {
                "total_words": total_words,
                "mastered_words": mastered_words,
                "learning_words": learning_words,
                "total_practices": total_practices,
                "average_accuracy": avg_accuracy,
                "streak_days": streak_data.get("streak", 0),
                "weekly_progress": weekly_progress
            }
        })
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@vocab_bp.route("/stats/progress", methods=["GET"])
def get_vocabulary_progress():
    """Get progress over time for charts"""
    try:
        session_id = session.get('user_id', 'default_user')
        days = int(request.args.get('days', 30))
        language = request.args.get('language', session.get('language', 'en'))
        
        from collections import defaultdict
        daily_data = defaultdict(lambda: {"date": "", "words_practiced": 0, "correct": 0, "new_words": 0, "accuracy": 0})
        
        if session_id in PRACTICE_HISTORY:
            for record in PRACTICE_HISTORY[session_id]:
                if record.get('language') == language:
                    date = record.get('timestamp', '')[:10]
                    if date:
                        daily_data[date]["date"] = date
                        daily_data[date]["words_practiced"] += 1
                        if record.get('correct'):
                            daily_data[date]["correct"] += 1
        
        if session_id in VOCABULARY_STORAGE:
            for word_data in VOCABULARY_STORAGE[session_id].values():
                if word_data.get('language') == language:
                    created = word_data.get('created_at')
                    if created:
                        date = created[:10]
                        daily_data[date]["date"] = date
                        daily_data[date]["new_words"] += 1
        
        for date, data in daily_data.items():
            if data["words_practiced"] > 0:
                data["accuracy"] = round((data["correct"] / data["words_practiced"]) * 100, 1)
        
        progress_data = list(daily_data.values())
        progress_data.sort(key=lambda x: x['date'])
        
        # Fill in missing dates
        result = []
        today = datetime.now()
        for i in range(days - 1, -1, -1):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            existing = next((d for d in progress_data if d['date'] == date), None)
            if existing:
                result.append(existing)
            else:
                result.append({"date": date, "words_practiced": 0, "correct": 0, "new_words": 0, "accuracy": 0})
        
        return jsonify({"success": True, "progress_data": result})
        
    except Exception as e:
        print(f"Error getting progress: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@vocab_bp.route("/review/due", methods=["GET"])
def get_due_for_review():
    """Get words due for review based on spaced repetition"""
    try:
        session_id = session.get('user_id', 'default_user')
        language = request.args.get('language', session.get('language', 'en'))
        limit = int(request.args.get('limit', 15))
        
        if session_id not in VOCABULARY_STORAGE:
            return jsonify({"success": True, "due_words": [], "total_due": 0})
        
        due_words = []
        for word_id, word_data in VOCABULARY_STORAGE[session_id].items():
            if word_data.get('language') != language:
                continue
            
            if needs_review(word_data.get('last_reviewed'), word_data.get('mastery_level', 0)):
                due_words.append({
                    "id": word_id,
                    "word": word_data['word'],
                    "meaning": word_data['meaning'],
                    "example": word_data.get('example', ''),
                    "mastery_level": word_data.get('mastery_level', 0)
                })
        
        due_words.sort(key=lambda x: x['mastery_level'])
        
        return jsonify({
            "success": True,
            "due_words": due_words[:limit],
            "total_due": len(due_words)
        })
        
    except Exception as e:
        print(f"Error getting due words: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

print("✅ Vocabulary routes loaded successfully!")