from datetime import datetime, timedelta
from collections import defaultdict

class MemoryStore:
    def __init__(self):
        print("🗄️ Initializing MemoryStore...")
        # Session data
        self.daily_words = {}
        self.user_progress = {}
        self.user_streaks = {}
        self.session_history = {}
        self.ai_generated_words = {}
        self.user_settings = {}
        
        # Vocabulary storage
        self.user_vocabulary = {}  # {user_id: {word_id: word_data}}
        self.practice_history = {}  # {user_id: [practice_records]}
        self.static_vocab = {}  # Loaded from JSON files
        print("✅ MemoryStore initialized")
    
    def get_user_key(self, session_id, language):
        return f"{session_id}_{language}"
    
    def update_streak(self, session_id, language):
        """Update and return user's daily streak"""
        streak_key = f"{session_id}_{language}"
        today = datetime.now().date().isoformat()
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        
        if streak_key not in self.user_streaks:
            self.user_streaks[streak_key] = {"streak": 0, "last_date": None}
        
        streak_data = self.user_streaks[streak_key]
        last_date = streak_data.get("last_date")
        
        if last_date == today:
            pass  # Already updated today
        elif last_date == yesterday:
            streak_data["streak"] += 1
        else:
            streak_data["streak"] = 1
        
        streak_data["last_date"] = today
        return streak_data["streak"]
    
    def get_progress(self, session_id, language):
        """Get user progress for a specific language"""
        user_key = self.get_user_key(session_id, language)
        
        # Return default progress if not exists
        if user_key not in self.user_progress:
            return {
                "words_learned": 0,
                "speaking_score": 0,
                "writing_score": 0,
                "reading_score": 0,
                "sentences_built": 0,
                "total_practice_time": 0,
                "level": "beginner",
                "achievements": [],
                "last_active": datetime.now().isoformat()
            }
        
        return self.user_progress[user_key]
    
    def update_progress(self, session_id, language, activity_type, points=10):
        """Update user progress based on activity"""
        user_key = self.get_user_key(session_id, language)
        
        # Initialize if not exists
        if user_key not in self.user_progress:
            self.user_progress[user_key] = {
                "words_learned": 0,
                "speaking_score": 0,
                "writing_score": 0,
                "reading_score": 0,
                "sentences_built": 0,
                "total_practice_time": 0,
                "level": "beginner",
                "achievements": [],
                "last_active": datetime.now().isoformat()
            }
        
        progress = self.user_progress[user_key]
        
        # Update based on activity type
        if activity_type == "word_learned":
            progress["words_learned"] += 1
            if progress["words_learned"] >= 10 and "word_starter" not in progress["achievements"]:
                progress["achievements"].append("word_starter")
            if progress["words_learned"] >= 50 and "vocabulary_builder" not in progress["achievements"]:
                progress["achievements"].append("vocabulary_builder")
                
        elif activity_type == "sentence_built":
            progress["sentences_built"] += 1
            
        elif activity_type == "speaking_practice":
            progress["speaking_score"] = min(100, progress["speaking_score"] + points)
            if progress["speaking_score"] >= 50 and "confident_speaker" not in progress["achievements"]:
                progress["achievements"].append("confident_speaker")
                
        elif activity_type == "writing_practice":
            progress["writing_score"] = min(100, progress["writing_score"] + points)
            
        elif activity_type == "reading_practice":
            progress["reading_score"] = min(100, progress["reading_score"] + points)
        
        # Update timestamp and practice time
        progress["total_practice_time"] += 1
        progress["last_active"] = datetime.now().isoformat()
        
        return progress

# Create global instance
store = MemoryStore()
