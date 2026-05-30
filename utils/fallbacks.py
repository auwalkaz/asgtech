def get_fallback_words_with_phrases(language):
    """Fallback vocabulary words with common phrases"""
    fallbacks = {
        "en": [
            {"word": "Excellent", "meaning": "Extremely good", "example": "The food was excellent.", 
             "pronunciation": "/ˈek.səl.ənt/", "common_phrases": ["Excellent idea!", "That's excellent news"]},
            {"word": "Appreciate", "meaning": "To value or be grateful", "example": "I appreciate your help.", 
             "pronunciation": "/əˈpriː.ʃi.eɪt/", "common_phrases": ["I appreciate that", "Much appreciated"]},
            {"word": "Challenge", "meaning": "A difficult task", "example": "Learning a new language is a challenge.", 
             "pronunciation": "/ˈtʃæl.ɪndʒ/", "common_phrases": ["Face the challenge", "Accept the challenge"]}
        ],
        "ar": [
            {"word": "ممتاز (mumtaz)", "meaning": "Excellent", "example": "كان الطعام ممتازاً", 
             "pronunciation": "/mum.taːz/", "common_phrases": ["فكرة ممتازة", "أخبار ممتازة"]},
            {"word": "يقدر (yuqaddir)", "meaning": "To appreciate", "example": "أقدر مساعدتك", 
             "pronunciation": "/ju.qad.dir/", "common_phrases": ["أقدر ذلك", "شكراً جزيلاً"]}
        ]
    }
    return fallbacks.get(language, fallbacks["en"])

def get_fallback_phrases(language, scenario):
    return [
        {"phrase": "Hello", "translation": "Greeting"},
        {"phrase": "How are you?", "translation": "Asking about well-being"},
        {"phrase": "Thank you", "translation": "Express gratitude"}
    ]

def get_fallback_exercises(language, exercise_type):
    if exercise_type == "spelling":
        return ["Hello", "Good", "Morning", "Friend", "Thank"]
    return ["Hello, how are you?", "Good morning everyone!"]

def get_fallback_story(language, level, variant=0):
    stories = {
        "en": {
            "title": "A Simple Day",
            "content": "This is a simple story for language learning. Practice reading every day to improve.",
            "questions": [
                {"question": "What is this?", "answer": "A story"},
                {"question": "How can you improve?", "answer": "Practice reading"}
            ]
        },
        "ar": {
            "title": "يوم بسيط",
            "content": "هذه قصة بسيطة لتعلم اللغة. تدرب على القراءة كل يوم لتحسين مستواك.",
            "questions": [
                {"question": "ما هذا؟", "answer": "قصة"},
                {"question": "كيف يمكنك التحسن؟", "answer": "ممارسة القراءة"}
            ]
        }
    }
    return stories.get(language, stories["en"])

def get_fallback_word_bank(language, level):
    fallbacks = {
        "en": {
            "beginner": {"theme": "Basic Actions", "words": ["I", "like", "to", "learn", "English", "every", "day"]},
            "intermediate": {"theme": "Daily Conversations", "words": ["I", "would", "like", "to", "practice", "speaking"]}
        },
        "ar": {
            "beginner": {"theme": "الكلمات الأساسية", "words": ["أنا", "أحب", "أن", "أتعلم", "العربية", "كل", "يوم"]}
        }
    }
    return fallbacks.get(language, fallbacks["en"]).get(level, fallbacks["en"]["beginner"])