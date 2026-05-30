from flask import Blueprint, request, jsonify, session
from datetime import datetime
import uuid
from storage.memory_store import store
from config import config

session_bp = Blueprint("session", __name__, url_prefix="/api")

@session_bp.route("/session/start", methods=["POST"])
def start_session():
    try:
        data = request.json or {}
        language = data.get('language', 'en')
        level = data.get('level', 'beginner')
        user_name = data.get('name', 'Learner')
        
        session_id = str(uuid.uuid4())
        
        session['user_id'] = session_id
        session['language'] = language
        session['level'] = level
        session['name'] = user_name
        session['created_at'] = datetime.now().isoformat()
        
        # Initialize user progress
        user_key = store.get_user_key(session_id, language)
        if user_key not in store.user_progress:
            store.user_progress[user_key] = {
                "words_learned": 0,
                "speaking_score": 0,
                "writing_score": 0,
                "reading_score": 0,
                "sentences_built": 0,
                "total_practice_time": 0,
                "level": level,
                "achievements": [],
                "last_active": datetime.now().isoformat()
            }
        
        # Initialize user settings
        if session_id not in store.user_settings:
            store.user_settings[session_id] = {
                "auto_play": True,
                "save_history": True,
                "daily_reminder": False,
                "preferred_voice": config.SUPPORTED_LANGUAGES.get(language, {}).get("voice", "alloy"),
                "difficulty": level
            }
        
        welcome_messages = {
            "en": f"Welcome {user_name}! Ready to learn {config.SUPPORTED_LANGUAGES.get(language, {}).get('name', 'English')}? 🎉",
            "ar": f"مرحبًا {user_name}! هل أنت مستعد لتعلم {config.SUPPORTED_LANGUAGES.get(language, {}).get('name', 'English')}؟ 🎉"
        }
        welcome = welcome_messages.get(language, welcome_messages["en"])
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "language": language,
            "level": level,
            "user_name": user_name,
            "welcome_message": welcome,
            "settings": store.user_settings[session_id]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@session_bp.route("/session/status", methods=["GET"])
def session_status():
    try:
        session_id = session.get('user_id')
        if not session_id:
            return jsonify({"success": False, "error": "No active session"}), 401
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "language": session.get('language', 'en'),
            "level": session.get('level', 'beginner'),
            "name": session.get('name', 'Learner'),
            "created_at": session.get('created_at')
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@session_bp.route("/session/update", methods=["POST"])
def update_session():
    try:
        session_id = session.get('user_id')
        if not session_id:
            return jsonify({"success": False, "error": "No active session"}), 401
        
        data = request.json
        if 'language' in data:
            session['language'] = data['language']
        if 'level' in data:
            session['level'] = data['level']
            user_key = store.get_user_key(session_id, session.get('language', 'en'))
            if user_key in store.user_progress:
                store.user_progress[user_key]['level'] = data['level']
        
        return jsonify({
            "success": True,
            "session": {
                "language": session.get('language'),
                "level": session.get('level'),
                "name": session.get('name')
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@session_bp.route("/session/end", methods=["POST"])
def end_session():
    try:
        session.clear()
        return jsonify({"success": True, "message": "Session ended"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500