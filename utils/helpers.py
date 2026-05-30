import json
import re
import uuid
from datetime import datetime

def clean_json_response(raw):
    """Clean JSON from AI response"""
    if not raw:
        return "{}"
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()

def get_voice_description(voice):
    descriptions = {
        "alloy": "Neutral, clear, versatile - great for English",
        "echo": "Male, warm, authoritative - good for Swahili/Arabic",
        "fable": "British English, storytelling - warm tone",
        "onyx": "Deep, professional male voice - good for German/Russian",
        "nova": "Female, warm, expressive - excellent for Romance languages",
        "shimmer": "Female, clear, melodic - good for tonal languages"
    }
    return descriptions.get(voice, "Standard voice")

def calculate_mastery(correct_count, incorrect_count, review_count):
    """Calculate mastery level from 0-5"""
    total = correct_count + incorrect_count
    if total == 0:
        return 0
    accuracy = correct_count / total
    return round(min(5, (accuracy * min(1, review_count / 10) * 5)), 1)

def needs_review(last_reviewed, mastery_level):
    """Check if word needs review based on spaced repetition"""
    if not last_reviewed:
        return True
    try:
        last_date = datetime.fromisoformat(last_reviewed)
        days_since = (datetime.now() - last_date).days
        intervals = [1, 2, 3, 5, 7, 10, 14, 21, 30]
        idx = min(int(mastery_level), len(intervals) - 1)
        return days_since >= intervals[idx]
    except:
        return True

def needs_vocab_review(word_data):
    """Alias for needs_review - checks if a word needs review based on spaced repetition intervals"""
    if not word_data:
        return True
    last_reviewed = word_data.get('last_reviewed') if isinstance(word_data, dict) else None
    mastery_level = word_data.get('mastery_level', 0) if isinstance(word_data, dict) else 0
    return needs_review(last_reviewed, mastery_level)

def get_phonetic_guide(word):
    """Simple phonetic guide for common words"""
    phonetics = {
        "the": "th-uh", "and": "uh-nd", "to": "too", "of": "uh-v",
        "a": "uh", "in": "ih-n", "that": "th-at", "is": "ih-z",
        "was": "wuh-z", "for": "f-or", "on": "on", "are": "ar",
        "with": "w-ith", "be": "bee", "at": "at", "have": "hav",
        "hello": "heh-loh", "good": "good", "morning": "mor-ning",
        "friend": "frend", "thank": "thangk", "please": "pleez",
        "sorry": "sor-ee", "yes": "yess", "no": "noh", "maybe": "may-bee",
        "cat": "kat", "dog": "dog", "house": "hows", "car": "kar",
        "teacher": "tee-cher", "student": "stoo-dent", "book": "book",
        "pen": "pen", "paper": "pay-per", "table": "tay-bul"
    }
    word_lower = word.lower()
    if word_lower in phonetics:
        return phonetics[word_lower]
    elif len(word) <= 3:
        return word
    else:
        # Simple syllable breakdown
        mid = len(word) // 2
        return f"{word[:mid]}-{word[mid:]}"

def generate_session_id():
    """Generate a unique session ID"""
    return str(uuid.uuid4())