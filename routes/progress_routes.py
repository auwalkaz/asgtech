from flask import Blueprint, request, jsonify, session
from storage.memory_store import store

progress_bp = Blueprint("progress", __name__, url_prefix="/api")

@progress_bp.route("/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """Get all user stats for dashboard"""
    try:
        session_id = session.get('user_id', 'default')
        language = request.args.get('language', session.get('language', 'en'))
        
        progress = store.get_progress(session_id, language)
        streak = store.update_streak(session_id, language)
        
        overall = (progress.get("speaking_score", 0) + 
                  progress.get("writing_score", 0) + 
                  progress.get("reading_score", 0)) / 3
        
        current_level = progress.get("level", "beginner")
        next_level = "intermediate" if current_level == "beginner" else "advanced" if current_level == "intermediate" else "master"
        
        return jsonify({
            "success": True,
            "stats": {
                "words_learned": progress.get("words_learned", 0),
                "speaking_score": progress.get("speaking_score", 0),
                "writing_score": progress.get("writing_score", 0),
                "reading_score": progress.get("reading_score", 0),
                "sentences_built": progress.get("sentences_built", 0),
                "daily_streak": streak,
                "overall_progress": round(overall, 1),
                "current_level": current_level,
                "next_level": next_level,
                "total_practice_time": progress.get("total_practice_time", 0),
                "achievements": progress.get("achievements", [])
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@progress_bp.route("/dashboard/achievements", methods=["GET"])
def get_achievements():
    """Get user achievements/badges"""
    try:
        session_id = session.get('user_id', 'default')
        language = request.args.get('language', session.get('language', 'en'))
        
        progress = store.get_progress(session_id, language)
        streak = store.update_streak(session_id, language)
        
        achievements = []
        
        if progress.get("words_learned", 0) >= 10:
            achievements.append({"id": "word_starter", "name": "Word Starter", "description": "Learned 10 words", "icon": "📖", "earned": True})
        if progress.get("words_learned", 0) >= 50:
            achievements.append({"id": "vocabulary_builder", "name": "Vocabulary Builder", "description": "Learned 50 words", "icon": "📚", "earned": True})
        if progress.get("speaking_score", 0) >= 50:
            achievements.append({"id": "confident_speaker", "name": "Confident Speaker", "description": "50% speaking score", "icon": "🎤", "earned": True})
        if streak >= 7:
            achievements.append({"id": "weekly_warrior", "name": "Weekly Warrior", "description": "7 day streak", "icon": "🔥", "earned": True})
        if streak >= 30:
            achievements.append({"id": "dedicated_learner", "name": "Dedicated Learner", "description": "30 day streak", "icon": "🏆", "earned": True})
        
        return jsonify({"success": True, "achievements": achievements})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@progress_bp.route("/activity/save", methods=["POST"])
def save_activity():
    """Save a learning activity"""
    try:
        data = request.json
        session_id = session.get('user_id', data.get('session_id', 'default'))
        language = data.get('language', session.get('language', 'en'))
        activity_type = data.get('type')
        points = data.get('points', 10)
        
        progress = store.update_progress(session_id, language, activity_type, points)
        streak = store.update_streak(session_id, language)
        
        return jsonify({"success": True, "progress": progress, "streak": streak})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@progress_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    """Get personalized learning recommendations"""
    try:
        session_id = session.get('user_id', 'default')
        language = request.args.get('language', session.get('language', 'en'))
        
        progress = store.get_progress(session_id, language)
        
        speaking_score = progress.get("speaking_score", 0)
        writing_score = progress.get("writing_score", 0)
        reading_score = progress.get("reading_score", 0)
        
        recommendations = []
        
        if speaking_score < 50:
            recommendations.append({
                "path": "speaking-only.html",
                "name": "Speaking Practice",
                "reason": "Your speaking needs improvement. Practice pronunciation!",
                "priority": "high",
                "icon": "🎤"
            })
        
        if writing_score < 50:
            recommendations.append({
                "path": "writing-focus.html",
                "name": "Writing Practice",
                "reason": "Writing skills need attention. Start with spelling!",
                "priority": "high",
                "icon": "✍️"
            })
        
        if reading_score < 50:
            recommendations.append({
                "path": "reading-focus.html",
                "name": "Reading Practice",
                "reason": "Reading comprehension can improve. Try short stories!",
                "priority": "medium",
                "icon": "📖"
            })
        
        recommendations.append({
            "path": "daily-words.html",
            "name": "Daily Words Challenge",
            "reason": "Learn 10 new words every day to build vocabulary!",
            "priority": "daily",
            "icon": "📅"
        })
        
        return jsonify({"success": True, "recommendations": recommendations[:5]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500