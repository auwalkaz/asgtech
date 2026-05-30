from flask import Blueprint, request, jsonify, session
import base64
from storage.memory_store import store
from services.ai_service import ai_service
from services.audio_service import audio_service
from config import config

chat_bp = Blueprint("chat", __name__, url_prefix="/api")

@chat_bp.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint for AI tutor conversations"""
    try:
        data = request.json
        user_text = data.get("text")
        language = data.get("language", session.get('language', 'en'))
        session_id = data.get("session_id", session.get('user_id', 'default'))
        
        if not user_text:
            return jsonify({"error": "No text provided"}), 400
        
        voice_config = config.SUPPORTED_LANGUAGES.get(language, config.SUPPORTED_LANGUAGES["en"])
        tts_voice = voice_config["model_voice"]
        
        history = store.session_history.get(session_id, [])
        messages = [
            {"role": "system", "content": f"You are a strict but encouraging language tutor. Reply in {language} and correct mistakes clearly. Keep responses helpful and concise (max 3 sentences)."}
        ]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": user_text})
        
        ai_text = ai_service.chat_completion(messages, temperature=0.7, max_tokens=500)
        
        store.session_history[session_id] = history + [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": ai_text}
        ]
        
        audio_result = audio_service.text_to_speech(ai_text, language)
        
        # Update practice time
        user_key = store.get_user_key(session_id, language)
        if user_key in store.user_progress:
            store.user_progress[user_key]["total_practice_time"] = store.user_progress[user_key].get("total_practice_time", 0) + 1
        
        return jsonify({
            "success": True,
            "reply": ai_text,
            "audio": audio_result["audio"],
            "voice_used": audio_result["voice_used"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@chat_bp.route("/voice-chat", methods=["POST"])
def voice_chat():
    """Voice chat endpoint for speech recognition"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No audio file"}), 400
        
        file = request.files["file"]
        language = request.form.get("language", session.get('language', 'en'))
        session_id = request.form.get("session_id", session.get('user_id', 'default'))
        
        voice_config = config.SUPPORTED_LANGUAGES.get(language, config.SUPPORTED_LANGUAGES["en"])
        tts_voice = voice_config["model_voice"]
        
        path = f"temp_{session_id}.webm"
        file.save(path)
        
        with open(path, "rb") as f:
            user_text = ai_service.transcribe_audio(f)
        
        import os
        os.remove(path)
        
        history = store.session_history.get(session_id, [])
        messages = [
            {"role": "system", "content": f"You are a strict language tutor. Reply in {language} and correct mistakes clearly."}
        ]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": user_text})
        
        ai_text = ai_service.chat_completion(messages, temperature=0.7, max_tokens=500)
        
        store.session_history[session_id] = history + [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": ai_text}
        ]
        
        audio_result = audio_service.text_to_speech(ai_text, language)
        
        return jsonify({
            "success": True,
            "user_text": user_text,
            "ai_text": ai_text,
            "audio": audio_result["audio"],
            "voice_used": audio_result["voice_used"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@chat_bp.route("/clear", methods=["POST"])
def clear_session():
    """Clear conversation session"""
    try:
        session_id = request.json.get("session_id", session.get('user_id', 'default'))
        if session_id in store.session_history:
            del store.session_history[session_id]
        return jsonify({"success": True, "message": "Session cleared"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500