from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
import time
import os
import json
import random

# Math quiz data
from questions_data import QUESTIONS_BANK

# Language learning imports
from config import config
from routes import (
    session_bp, vocab_bp, chat_bp, grammar_bp,
    speaking_bp, reading_bp, writing_bp, progress_bp,
    daily_words_bp, tips_bp, lingua_bp, translation_bp,
    json_bp
)

app = Flask(__name__)
app.secret_key = 'math_quiz_secret_key_2026'
CORS(app, supports_credentials=True)

# ================= MATH QUIZ CONFIG =================
LEVELS = ['beginner', 'medium', 'advanced']
LEVEL_NAMES = {'beginner': 'Beginner', 'medium': 'Medium', 'advanced': 'Advanced'}
POINTS = {'beginner': 2, 'medium': 3, 'advanced': 5}
PASSING_SCORES = {'beginner': 50, 'medium': 75, 'advanced': 125}
MAX_QUESTIONS = 50

# ================= LANGUAGE LEARNING BLUEPRINTS =================
app.register_blueprint(session_bp)
app.register_blueprint(vocab_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(grammar_bp)
app.register_blueprint(speaking_bp)
app.register_blueprint(reading_bp)
app.register_blueprint(writing_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(daily_words_bp)
app.register_blueprint(tips_bp)
app.register_blueprint(lingua_bp)
app.register_blueprint(translation_bp)
app.register_blueprint(json_bp)

# ================= MATH QUIZ ROUTES =================

@app.route('/')
def index():
    """Math quiz home page"""
    if 'user_data' not in session:
        session['user_data'] = {
            'name': 'Player',
            'current_level': 'beginner',
            'scores': {'beginner': 0, 'medium': 0, 'advanced': 0},
            'unlocked_levels': {'beginner': True, 'medium': False, 'advanced': False},
            'level_completed': {'beginner': False, 'medium': False, 'advanced': False},
            'level_started': {'beginner': False, 'medium': False, 'advanced': False},
            'answered_questions': {'beginner': [], 'medium': [], 'advanced': []},
            'total_questions_answered': {'beginner': 0, 'medium': 0, 'advanced': 0},
            'current_session_questions': []
        }
    return render_template('index.html')

@app.route('/get_user_info')
def get_user_info():
    """Get user info - unified endpoint for both math quiz and language learning"""
    user_data = session.get('user_data', {})
    
    # Combine math quiz data with language learning data
    return jsonify({
        # Math quiz data
        'name': user_data.get('name', 'Player'),
        'scores': user_data.get('scores', {'beginner': 0, 'medium': 0, 'advanced': 0}),
        'unlocked_levels': user_data.get('unlocked_levels', {'beginner': True, 'medium': False, 'advanced': False}),
        'level_completed': user_data.get('level_completed', {'beginner': False, 'medium': False, 'advanced': False}),
        'level_started': user_data.get('level_started', {'beginner': False, 'medium': False, 'advanced': False}),
        'total_answered': user_data.get('total_questions_answered', {'beginner': 0, 'medium': 0, 'advanced': 0}),
        # Language learning data
        'language': session.get('language', 'en'),
        'level': session.get('level', 'beginner'),
        'points': session.get('total_points', 0),
        'streak': session.get('streak_days', 0),
        'premium': session.get('premium', False),
        'avatar': session.get('avatar', '🐧'),
        'user_id': session.get('user_id', 'guest_' + str(int(time.time())))
    })

@app.route('/set_user_name', methods=['POST'])
def set_user_name():
    data = request.json
    if 'user_data' not in session:
        session['user_data'] = {}
    session['user_data']['name'] = data.get('name', 'Player')
    session.modified = True
    return jsonify({'status': 'success'})

@app.route('/start_level', methods=['POST'])
def start_level():
    data = request.json
    level = data['level']
    user_data = session.get('user_data', {})
    
    if not user_data.get('unlocked_levels', {}).get(level, False):
        return jsonify({'error': 'Level locked'}), 403
    
    if user_data.get('level_completed', {}).get(level, False):
        return jsonify({'error': 'Level already completed'}), 400
    
    user_data['level_started'][level] = True
    
    answered_ids = user_data.get('answered_questions', {}).get(level, [])
    available = [q for q in QUESTIONS_BANK[level] if q['id'] not in answered_ids]
    next_questions = available[:10]
    
    user_data['current_session_questions'] = [q['id'] for q in next_questions]
    session['user_data'] = user_data
    session.modified = True
    
    return jsonify({
        'success': True,
        'questions': next_questions,
        'total_answered': len(answered_ids),
        'remaining': len(available),
        'current_score': user_data.get('scores', {}).get(level, 0),
        'passing_score': PASSING_SCORES[level]
    })

@app.route('/get_questions/<level>')
def get_questions(level):
    if level not in LEVELS:
        return jsonify({'error': 'Invalid level'}), 400
    
    user_data = session.get('user_data', {})
    
    if not user_data.get('level_started', {}).get(level, False):
        return jsonify({'error': 'Level not started', 'not_started': True}), 400
    
    if user_data.get('level_completed', {}).get(level, False):
        return jsonify({'error': 'Level already completed', 'completed': True}), 400
    
    answered_ids = user_data.get('answered_questions', {}).get(level, [])
    available = [q for q in QUESTIONS_BANK[level] if q['id'] not in answered_ids]
    next_questions = available[:10]
    
    return jsonify({
        'questions': next_questions,
        'total_answered': len(answered_ids),
        'remaining': len(available),
        'total_questions': MAX_QUESTIONS,
        'current_score': user_data.get('scores', {}).get(level, 0),
        'passing_score': PASSING_SCORES[level]
    })

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    level = data['level']
    question_id = data['question_id']
    user_answer = data['answer']
    
    user_data = session.get('user_data', {})
    
    if not user_data.get('level_started', {}).get(level, False):
        return jsonify({'error': 'Level not started'}), 400
    
    question = next((q for q in QUESTIONS_BANK[level] if q['id'] == question_id), None)
    if not question:
        return jsonify({'error': 'Question not found'}), 404
    
    if question_id in user_data.get('answered_questions', {}).get(level, []):
        return jsonify({'error': 'Already answered'}), 400
    
    is_correct = False
    try:
        if isinstance(question['answer'], float):
            is_correct = abs(float(user_answer) - question['answer']) < 0.01
        else:
            if isinstance(question['answer'], str):
                is_correct = str(user_answer).strip().lower() == question['answer'].lower()
            else:
                is_correct = float(user_answer) == float(question['answer'])
    except:
        is_correct = False
    
    points_earned = POINTS[level] if is_correct else 0
    if is_correct:
        if 'scores' not in user_data:
            user_data['scores'] = {'beginner': 0, 'medium': 0, 'advanced': 0}
        user_data['scores'][level] = user_data['scores'].get(level, 0) + points_earned
    
    if 'answered_questions' not in user_data:
        user_data['answered_questions'] = {'beginner': [], 'medium': [], 'advanced': []}
    if 'total_questions_answered' not in user_data:
        user_data['total_questions_answered'] = {'beginner': 0, 'medium': 0, 'advanced': 0}
    
    user_data['answered_questions'][level].append(question_id)
    user_data['total_questions_answered'][level] += 1
    
    current_score = user_data['scores'][level]
    level_passed = current_score >= PASSING_SCORES[level]
    questions_answered = len(user_data['answered_questions'][level])
    questions_remaining = MAX_QUESTIONS - questions_answered
    
    level_completed = questions_answered >= MAX_QUESTIONS or level_passed
    
    next_unlocked = False
    next_level_name = None
    
    if level_completed and not user_data.get('level_completed', {}).get(level, False):
        user_data['level_completed'][level] = True
        
        if level == 'beginner' and not user_data.get('unlocked_levels', {}).get('medium', False):
            user_data['unlocked_levels']['medium'] = True
            next_unlocked = True
            next_level_name = 'medium'
        elif level == 'medium' and not user_data.get('unlocked_levels', {}).get('advanced', False):
            user_data['unlocked_levels']['advanced'] = True
            next_unlocked = True
            next_level_name = 'advanced'
    
    session['user_data'] = user_data
    session.modified = True
    
    return jsonify({
        'correct': is_correct,
        'points_earned': points_earned,
        'current_score': user_data['scores'][level],
        'passing_score': PASSING_SCORES[level],
        'level_passed': level_passed,
        'level_completed': level_completed,
        'next_unlocked': next_unlocked,
        'next_level': next_level_name,
        'questions_answered': questions_answered,
        'questions_remaining': questions_remaining,
        'total_questions': MAX_QUESTIONS,
        'all_scores': user_data['scores'],
        'all_completed': user_data.get('level_completed', {})
    })

@app.route('/reset')
def reset():
    session.clear()
    return jsonify({'status': 'reset'})

# ================= LANGUAGE LEARNING PAGE ROUTES =================

@app.route('/writing-focus.html')
def writing_focus():
    return render_template('writing-focus.html')

@app.route('/speaking-only.html')
def speaking_only():
    return render_template('speaking-only.html')

@app.route('/vocabulary-builder.html')
def vocabulary_builder():
    return render_template('vocabulary-builder.html')

@app.route('/reading-focus.html')
def reading_focus():
    return render_template('reading-focus.html')

@app.route('/beginner-full.html')
def beginner_full():
    return render_template('beginner-full.html')

@app.route('/advanced-conversation.html')
def advanced_conversation():
    return render_template('advanced-conversation.html')

@app.route('/daily-words.html')
def daily_words_page():
    return render_template('daily-words.html')

@app.route('/language-translator.html')
def language_translator():
    return render_template('language-translator.html')

@app.route('/grammar-practice.html')
def grammar_practice():
    return render_template('grammar-practice.html')

# ================= API HEALTH CHECK =================

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "success": True,
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "supported_languages": list(config.SUPPORTED_LANGUAGES.keys())
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
