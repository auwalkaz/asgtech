from flask import Flask, jsonify, render_template, send_from_directory, request, session, redirect
from flask_cors import CORS
from config import config
from datetime import datetime
import os
import secrets
import hashlib
from datetime import timedelta
from functools import wraps

# Import all blueprints
from routes import (
    session_bp, vocab_bp, chat_bp, grammar_bp,
    speaking_bp, reading_bp, writing_bp, progress_bp,
    daily_words_bp, tips_bp, lingua_bp, translation_bp,
    json_bp
)

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.permanent_session_lifetime = timedelta(days=30)
CORS(app, supports_credentials=True)

# Register all blueprints
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

# ================= HELPER FUNCTION FOR JSON PATH (FIXED FOR RENDER) =================
def get_json_folder():
    """Get the correct JSON folder path that works on both local and Render"""
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json'),
        '/opt/render/project/src/json',
        os.path.join(os.getcwd(), 'json'),
        '/home/auwalkz/app/json',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Found JSON folder at: {path}")
            return path
    
    os.makedirs(possible_paths[0], exist_ok=True)
    return possible_paths[0]

# ================= PREMIUM CHECK DECORATOR =================

def premium_required(f):
    """Decorator to check if user has premium access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/auth')
        
        user_email = session.get('user_email')
        users = session.get('users', {})
        user_data = users.get(user_email, {})
        subscription_tier = user_data.get('subscription_tier', 'free')
        
        if subscription_tier == 'free':
            return redirect('/upgrade-required')
        
        return f(*args, **kwargs)
    return decorated_function

def get_user_subscription():
    """Helper to get user subscription status"""
    user_email = session.get('user_email')
    users = session.get('users', {})
    user_data = users.get(user_email, {})
    return user_data.get('subscription_tier', 'free')

# ================= SERVE ALL HTML PAGES =================

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/beginner-full.html")
@premium_required
def beginner_full():
    return render_template('beginner-full.html')

@app.route("/vocabulary-builder.html")
@premium_required
def vocabulary_builder():
    return render_template('vocabulary-builder.html')

@app.route("/speaking-only.html")
@premium_required
def speaking_only():
    return render_template('speaking-only.html')

@app.route("/writing-focus.html")
@premium_required
def writing_focus():
    return render_template('writing-focus.html')

@app.route("/reading-focus.html")
@premium_required
def reading_focus():
    return render_template('reading-focus.html')

@app.route("/advanced-conversation.html")
@premium_required
def advanced_conversation():
    return render_template('advanced-conversation.html')

@app.route("/daily-words.html")
@premium_required
def daily_words_page():
    return render_template('daily-words.html')

@app.route("/language-translator.html")
@premium_required
def language_translator():
    return render_template('language-translator.html')

@app.route("/grammar-practice.html")
@premium_required
def grammar_practice():
    return render_template('grammar-practice.html')

@app.route("/writing")
@premium_required
def writing_practice():
    return send_from_directory('static', 'writing-practice.html')

# ================= API HEALTH CHECK =================

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "success": True,
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "supported_languages": list(config.SUPPORTED_LANGUAGES.keys())
    })

# ================= AUTH PAGES =================

@app.route('/auth')
@app.route('/auth.html')
@app.route('/login')
@app.route('/signup')
def auth_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template('auth.html')

@app.route('/upgrade-required')
def upgrade_required():
    return render_template('upgrade-required.html')

@app.route('/upgrade')
def upgrade_page():
    return render_template('upgrade.html')

@app.route('/api/check-premium')
def check_premium():
    subscription_tier = get_user_subscription()
    return jsonify({
        'is_premium': subscription_tier != 'free',
        'subscription_tier': subscription_tier,
        'is_logged_in': 'user_id' in session
    })

# ================= JSON ROUTES FOR WORDBANK FILES =================

@app.route('/api/words/<language>')
def get_words_api(language):
    """Get words for a specific language"""
    import json
    import random
    
    json_folder = get_json_folder()
    file_path = os.path.join(json_folder, f'wordbank_{language}.json')
    
    if not os.path.exists(file_path):
        file_path = os.path.join(json_folder, f'{language}.json')
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'words' in data:
            words = data['words']
        elif isinstance(data, list):
            words = data
        else:
            words = []
        
        return jsonify({
            "success": True,
            "language": language,
            "words": words,
            "count": len(words)
        })
    
    return jsonify({"success": False, "error": f"No word bank for {language}", "words": []}), 404

@app.route('/api/words/list')
def get_languages_list():
    """Get list of available languages"""
    import json
    
    json_folder = get_json_folder()
    languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'sw', 'zh', 'ar', 'hi']
    
    if os.path.exists(json_folder):
        found = []
        for file in os.listdir(json_folder):
            if file.startswith('wordbank_') and file.endswith('.json'):
                lang = file.replace('wordbank_', '').replace('.json', '')
                found.append(lang)
        if found:
            languages = found
    
    return jsonify({"success": True, "languages": sorted(languages)})

# ================= VOCABULARY API =================

@app.route('/api/vocabulary/words', methods=['GET'])
def get_vocabulary_words():
    """Get vocabulary words"""
    import json
    
    language = request.args.get('language', 'en')
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '')
    per_page = 12
    
    json_folder = get_json_folder()
    file_path = os.path.join(json_folder, f'wordbank_{language}.json')
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        words = data.get('words', []) if isinstance(data, dict) else data
        
        if search:
            words = [w for w in words if search.lower() in w.get('word', '').lower()]
        
        for idx, w in enumerate(words):
            if 'id' not in w:
                w['id'] = str(idx + 1)
            if 'mastery_level' not in w:
                w['mastery_level'] = 0
        
        total = len(words)
        total_pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        
        return jsonify({
            'success': True,
            'words': words[start:end],
            'page': page,
            'total_pages': total_pages,
            'total': total
        })
    
    return jsonify({'success': True, 'words': [], 'page': 1, 'total_pages': 0, 'total': 0})

@app.route('/api/vocabulary/words', methods=['POST'])
def add_vocabulary_word():
    """Add a word to vocabulary"""
    data = request.json
    # Store in session for now
    if 'user_vocabulary' not in session:
        session['user_vocabulary'] = []
    
    word_data = {
        'id': str(len(session['user_vocabulary']) + 1),
        'word': data.get('word'),
        'meaning': data.get('meaning'),
        'example': data.get('example', ''),
        'part_of_speech': data.get('part_of_speech', 'noun'),
        'mastery_level': 0,
        'created_at': datetime.now().isoformat()
    }
    
    session['user_vocabulary'].append(word_data)
    session.modified = True
    
    return jsonify({'success': True, 'word': word_data})

@app.route('/api/vocabulary/words/<word_id>', methods=['DELETE'])
def delete_vocabulary_word(word_id):
    """Delete a word from vocabulary"""
    if 'user_vocabulary' in session:
        session['user_vocabulary'] = [w for w in session['user_vocabulary'] if w.get('id') != word_id]
        session.modified = True
    
    return jsonify({'success': True})

@app.route('/api/vocabulary/practice/record', methods=['POST'])
def record_practice():
    """Record practice result"""
    data = request.json
    word_id = data.get('word_id')
    correct = data.get('correct', False)
    
    if 'user_vocabulary' in session:
        for word in session['user_vocabulary']:
            if word.get('id') == word_id:
                if correct and word.get('mastery_level', 0) < 5:
                    word['mastery_level'] = word.get('mastery_level', 0) + 1
                break
        session.modified = True
    
    return jsonify({'success': True, 'mastery_level': word.get('mastery_level', 0) if 'word' in locals() else 0})

@app.route('/api/vocabulary/quiz/generate', methods=['POST'])
def generate_quiz():
    """Generate a quiz"""
    import random
    
    data = request.json
    language = data.get('language', 'en')
    word_count = min(data.get('word_count', 5), 10)
    
    json_folder = get_json_folder()
    file_path = os.path.join(json_folder, f'wordbank_{language}.json')
    
    if os.path.exists(file_path):
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            words_data = json.load(f)
        
        words = words_data.get('words', []) if isinstance(words_data, dict) else words_data
        random.shuffle(words)
        selected = words[:word_count]
        
        questions = []
        for w in selected:
            options = [w.get('meaning', '')]
            other_meanings = [ow.get('meaning', '') for ow in words if ow.get('word') != w.get('word')]
            options.extend(random.sample(other_meanings, min(3, len(other_meanings))))
            random.shuffle(options)
            
            questions.append({
                'id': w.get('id', w.get('word')),
                'question': f"What is the meaning of '{w.get('word')}'?",
                'options': options,
                'correct_answer': w.get('meaning', ''),
                'example': w.get('example', '')
            })
        
        return jsonify({'success': True, 'questions': questions, 'total': len(questions)})
    
    return jsonify({'success': False, 'error': 'No words available'}), 404

@app.route('/api/vocabulary/stats')
def get_vocabulary_stats():
    """Get vocabulary statistics"""
    language = request.args.get('language', 'en')
    
    json_folder = get_json_folder()
    file_path = os.path.join(json_folder, f'wordbank_{language}.json')
    
    total_words = 0
    if os.path.exists(file_path):
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        words = data.get('words', []) if isinstance(data, dict) else data
        total_words = len(words)
    
    mastered = 0
    if 'user_vocabulary' in session:
        mastered = len([w for w in session['user_vocabulary'] if w.get('mastery_level', 0) >= 3])
    
    return jsonify({
        'success': True,
        'stats': {
            'total_words': total_words,
            'mastered_words': mastered,
            'learning_words': max(0, total_words - mastered),
            'total_practices': 0,
            'streak_days': 0,
            'weekly_progress': 0,
            'average_accuracy': 0
        }
    })

# ================= DAILY WORDS API =================

@app.route('/api/daily-words')
def get_daily_words():
    """Get daily words"""
    import json
    import random
    
    language = request.args.get('language', 'en')
    json_folder = get_json_folder()
    file_path = os.path.join(json_folder, f'wordbank_{language}.json')
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        words = data.get('words', []) if isinstance(data, dict) else data
        random.shuffle(words)
        
        return jsonify({
            'success': True,
            'words': words[:10],
            'date': datetime.now().strftime('%Y-%m-%d')
        })
    
    # Fallback
    return jsonify({
        'success': True,
        'words': [
            {'word': 'Hello', 'meaning': 'A greeting', 'example': 'Hello world!', 'pronunciation': '/həˈləʊ/'},
            {'word': 'World', 'meaning': 'The earth', 'example': 'Hello world!', 'pronunciation': '/wɜːld/'}
        ],
        'date': datetime.now().strftime('%Y-%m-%d')
    })

# ================= DASHBOARD STATS =================

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Get dashboard statistics"""
    return jsonify({
        'success': True,
        'stats': {
            'words_learned': len(session.get('user_vocabulary', [])),
            'speaking_score': 0,
            'writing_score': 0,
            'reading_score': 0,
            'daily_streak': 0,
            'overall_progress': 0
        }
    })

@app.route('/api/session/start', methods=['POST'])
def start_session():
    """Start a learning session"""
    return jsonify({'success': True, 'session_id': secrets.token_hex(16)})

@app.route('/api/activity/save', methods=['POST'])
def save_activity():
    """Save user activity"""
    data = request.json
    if 'activities' not in session:
        session['activities'] = []
    
    session['activities'].append({
        'type': data.get('type'),
        'points': data.get('points', 0),
        'timestamp': datetime.now().isoformat()
    })
    session.modified = True
    
    return jsonify({'success': True})

# ================= TIPS GENERATION =================

@app.route('/api/tips/generate')
def generate_tips():
    """Generate AI tips"""
    language = request.args.get('language', 'en')
    count = min(int(request.args.get('count', 6)), 10)
    
    tips = [
        {"icon": "💡", "title": "The 15-Minute Rule", "content": "Study for 15 minutes daily - consistency beats intensity!", "category": "Learning"},
        {"icon": "🧠", "title": "Spaced Repetition", "content": "Review words just before you forget them - it's the most efficient way to memorize!", "category": "Memory"},
        {"icon": "🎯", "title": "Set SMART Goals", "content": "Specific, Measurable, Achievable, Relevant, Time-bound goals keep you motivated!", "category": "Motivation"},
        {"icon": "🗣️", "title": "Shadowing Technique", "content": "Repeat after native speakers immediately - it improves pronunciation and fluency!", "category": "Speaking"},
        {"icon": "📱", "title": "Immerse Yourself", "content": "Change your phone's language to your target language - it's free daily practice!", "category": "Learning"},
        {"icon": "🎧", "title": "Listen While Commuting", "content": "Use podcasts or audiobooks during your commute - turn wasted time into learning time!", "category": "Listening"}
    ]
    
    return jsonify({
        'success': True,
        'tips': tips[:count],
        'source': 'ai_generated',
        'generated_at': datetime.now().isoformat()
    })

# ================= SUBSCRIPTION PLANS =================

SUBSCRIPTION_PLANS = {
    'premium_monthly': {
        'name': 'Premium Monthly',
        'price': 9.99,
        'price_display': '$9.99/month',
        'features': ['Unlimited vocabulary', 'Unlimited AI chat', 'No ads', 'Voice lessons', 'Priority support']
    },
    'premium_yearly': {
        'name': 'Premium Yearly',
        'price': 79.99,
        'price_display': '$79.99/year',
        'features': ['All monthly features', 'Save 33%', 'Certificate of completion', 'Advanced analytics']
    },
    'lifetime': {
        'name': 'Lifetime',
        'price': 199.99,
        'price_display': '$199.99 one-time',
        'features': ['All premium features forever', 'Lifetime updates', 'Personal mentor access', 'Custom learning path']
    }
}

@app.route('/api/subscription/plans')
def get_subscription_plans():
    """Get available subscription plans"""
    return jsonify({'success': True, 'plans': SUBSCRIPTION_PLANS})

@app.route('/api/subscription/upgrade', methods=['POST'])
def upgrade_subscription():
    """Upgrade user subscription"""
    data = request.json
    plan_id = data.get('plan_id')
    
    if plan_id not in SUBSCRIPTION_PLANS:
        return jsonify({'success': False, 'error': 'Invalid plan'}), 400
    
    user_email = session.get('user_email')
    users = session.get('users', {})
    
    if user_email in users:
        users[user_email]['subscription_tier'] = plan_id
        session.modified = True
        
        return jsonify({'success': True, 'message': f'Successfully upgraded to {SUBSCRIPTION_PLANS[plan_id]["name"]}!'})
    
    return jsonify({'success': False, 'error': 'User not found'}), 404

# ================= AUTHENTICATION API =================

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Register new user"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        if 'users' not in session:
            session['users'] = {}
        
        if email in session['users']:
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        
        user_id = secrets.token_hex(16)
        session['users'][email] = {
            'id': user_id,
            'email': email,
            'password_hash': password_hash,
            'salt': salt,
            'name': name if name else email.split('@')[0],
            'created_at': datetime.now().isoformat(),
            'subscription_tier': 'free',
            'total_points': 0,
            'streak_days': 0
        }
        session.modified = True
        
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = name if name else email.split('@')[0]
        
        return jsonify({'success': True, 'user': {'id': user_id, 'email': email, 'name': session['user_name'], 'subscription_tier': 'free'}})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login user"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        users = session.get('users', {})
        user_data = users.get(email)
        
        if not user_data:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), user_data['salt'].encode(), 100000).hex()
        
        if password_hash != user_data['password_hash']:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        session['user_id'] = user_data['id']
        session['user_email'] = email
        session['user_name'] = user_data['name']
        session.modified = True
        
        return jsonify({'success': True, 'user': {'id': user_data['id'], 'email': email, 'name': user_data['name'], 'subscription_tier': user_data.get('subscription_tier', 'free')}})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Logout user"""
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_name', None)
    return jsonify({'success': True})

@app.route('/api/auth/status')
def api_auth_status():
    """Get auth status"""
    return jsonify({
        'success': True,
        'logged_in': 'user_id' in session,
        'user': {
            'id': session.get('user_id'),
            'email': session.get('user_email'),
            'name': session.get('user_name'),
            'subscription_tier': get_user_subscription()
        } if 'user_id' in session else None
    })

# ================= DEVELOPMENT ENDPOINTS =================

@app.route('/dev-login')
def dev_login():
    """Quick development login"""
    if 'users' not in session:
        session['users'] = {}
    
    test_email = 'dev@localhost'
    if test_email not in session['users']:
        session['users'][test_email] = {
            'id': 'dev_' + secrets.token_hex(8),
            'email': test_email,
            'name': 'Developer',
            'subscription_tier': 'premium_yearly',
            'created_at': datetime.now().isoformat()
        }
    
    session['user_id'] = session['users'][test_email]['id']
    session['user_email'] = test_email
    session['user_name'] = 'Developer'
    session.modified = True
    
    return redirect('/')

@app.route('/dev-panel')
def dev_panel():
    """Developer panel"""
    return render_template('dev-panel.html') if os.path.exists('templates/dev-panel.html') else "Dev Panel - App is running"

@app.route('/reset')
def reset_session():
    """Reset session"""
    session.clear()
    return redirect('/auth')

@app.route('/debug-files')
def debug_files():
    """Debug endpoint to list files"""
    templates = os.listdir('templates/') if os.path.exists('templates/') else []
    return {'templates_folder': 'templates', 'files': templates}

# ================= ERROR HANDLERS =================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Page not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ================= RUN APP =================

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

print("=" * 50)
print("🚀 Astech Language Learning App is running!")
print("=" * 50)