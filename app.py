from flask import Flask, jsonify, render_template, send_from_directory, request, session, redirect
from flask_cors import CORS
from config import config
from datetime import datetime
import os
import secrets
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

# ================= PREMIUM CHECK DECORATOR =================

def premium_required(f):
    """Decorator to check if user has premium access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'user_id' not in session:
            return redirect('/auth')
        
        user_email = session.get('user_email')
        users = session.get('users', {})
        user_data = users.get(user_email, {})
        subscription_tier = user_data.get('subscription_tier', 'free')
        
        # Check if user has premium (not free)
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

# Premium-only routes (require premium subscription)
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

# Writing practice route
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
    """Serve the authentication page"""
    # If already logged in, redirect to home
    if 'user_id' in session:
        return redirect('/')
    return render_template('auth.html')

# ================= UPGRADE PAGES =================

@app.route('/upgrade-required')
def upgrade_required():
    """Page shown when free user tries to access premium content"""
    return render_template('upgrade-required.html')

@app.route('/upgrade')
def upgrade_page():
    """Premium upgrade page"""
    return render_template('upgrade.html')

@app.route('/api/check-premium')
def check_premium():
    """API endpoint to check if user has premium access"""
    subscription_tier = get_user_subscription()
    return jsonify({
        'is_premium': subscription_tier != 'free',
        'subscription_tier': subscription_tier,
        'is_logged_in': 'user_id' in session
    })

# ================= DEVELOPMENT QUICK LOGIN =================

@app.route('/dev-login')
def dev_login():
    """Quick development login - bypasses password"""
    test_email = 'dev@localhost'
    test_name = 'Developer'
    
    if 'users' not in session:
        session['users'] = {}
    
    if test_email not in session['users']:
        user_id = 'dev_' + secrets.token_hex(8)
        session['users'][test_email] = {
            'id': user_id,
            'email': test_email,
            'name': test_name,
            'subscription_tier': 'premium_yearly',
            'subscription_expires': (datetime.now() + timedelta(days=365)).isoformat(),
            'created_at': datetime.now().isoformat(),
            'total_points': 9999,
            'streak_days': 30,
            'last_active': datetime.now().isoformat(),
            'usage': {}
        }
    
    session.permanent = True
    session['user_id'] = session['users'][test_email]['id']
    session['user_email'] = test_email
    session['user_name'] = test_name
    session.modified = True
    
    return '''
    <html>
    <head><title>Dev Login - Astech</title>
    <style>
        body { background: linear-gradient(135deg, #0f172a, #1e1b4b); font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; color: white; }
        .container { text-align: center; background: #1e293b; padding: 40px; border-radius: 20px; }
        button { background: #3b82f6; border: none; padding: 10px 20px; border-radius: 10px; color: white; cursor: pointer; margin-top: 20px; }
        .premium-badge { background: #f59e0b; display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 12px; margin-top: 10px; }
    </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Login Successful!</h1>
            <p>Welcome back, <strong>Developer</strong>!</p>
            <div class="premium-badge">⭐ PREMIUM ACCESS</div>
            <p style="margin-top: 20px;">You have full access to all features.</p>
            <button onclick="window.location.href='/'">Go to Dashboard</button>
        </div>
        <script>setTimeout(() => { window.location.href = '/'; }, 1500);</script>
    </body>
    </html>
    '''

@app.route('/dev-switch-user/<user_type>')
def dev_switch_user(user_type):
    """Switch between different test user types"""
    users_config = {
        'premium': {'name': 'Premium User', 'tier': 'premium_yearly', 'points': 5000},
        'free': {'name': 'Free User', 'tier': 'free', 'points': 150}
    }
    
    config = users_config.get(user_type, users_config['premium'])
    test_email = f'{user_type}@dev.local'
    
    if 'users' not in session:
        session['users'] = {}
    
    session['users'][test_email] = {
        'id': f'dev_{user_type}',
        'email': test_email,
        'name': config['name'],
        'subscription_tier': config['tier'],
        'subscription_expires': (datetime.now() + timedelta(days=365)).isoformat() if config['tier'] != 'free' else None,
        'created_at': datetime.now().isoformat(),
        'total_points': config['points'],
        'streak_days': 15,
        'last_active': datetime.now().isoformat(),
        'usage': {}
    }
    
    session['user_id'] = f'dev_{user_type}'
    session['user_email'] = test_email
    session['user_name'] = config['name']
    session.modified = True
    
    return f'''
    <html>
    <head><title>Dev Login - Astech</title>
    <style>
        body {{ background: linear-gradient(135deg, #0f172a, #1e1b4b); font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; color: white; }}
        .container {{ text-align: center; background: #1e293b; padding: 40px; border-radius: 20px; }}
        .premium-badge {{ background: {'#f59e0b' if config['tier'] != 'free' else '#475569'}; display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 12px; margin-top: 10px; }}
        button {{ background: #3b82f6; border: none; padding: 10px 20px; border-radius: 10px; color: white; cursor: pointer; margin-top: 20px; }}
    </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Switched to {config['name']}</h1>
            <div class="premium-badge">{'⭐ PREMIUM' if config['tier'] != 'free' else '📖 FREE'}</div>
            <button onclick="window.location.href='/'">Go to Dashboard</button>
        </div>
        <script>setTimeout(() => {{ window.location.href = '/'; }}, 1000);</script>
    </body>
    </html>
    '''

@app.route('/dev-panel')
def dev_panel():
    """Development panel"""
    return '''
    <html>
    <head><title>Dev Panel - Astech</title>
    <style>
        body { background: #0f172a; font-family: sans-serif; color: white; padding: 20px; }
        .card { background: #1e293b; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        button { background: #3b82f6; border: none; padding: 10px 15px; border-radius: 8px; color: white; cursor: pointer; margin: 5px; }
        .btn-success { background: #10b981; }
        .btn-warning { background: #f59e0b; }
        .btn-danger { background: #ef4444; }
    </style>
    </head>
    <body>
        <h1>🔧 Astech Developer Panel</h1>
        <div class="card">
            <h2>Quick Login</h2>
            <button onclick="location.href='/dev-login'">🚀 Dev Login (Premium)</button>
            <button class="btn-success" onclick="location.href='/dev-switch-user/premium'">⭐ Premium User</button>
            <button class="btn-warning" onclick="location.href='/dev-switch-user/free'">📖 Free User</button>
            <button class="btn-danger" onclick="location.href='/reset'">🗑️ Reset Session</button>
        </div>
        <div class="card">
            <h2>Navigation</h2>
            <button onclick="location.href='/'">🏠 Home</button>
            <button onclick="location.href='/auth'">🔐 Auth Page</button>
            <button onclick="location.href='/upgrade'">⭐ Upgrade Page</button>
            <button onclick="location.href='/writing'">✍️ Writing</button>
        </div>
        <div class="card">
            <h2>Session Info</h2>
            <button onclick="checkSession()">Check Session</button>
            <pre id="sessionInfo"></pre>
        </div>
        <script>
            async function checkSession() {
                const res = await fetch('/api/auth/status');
                const data = await res.json();
                document.getElementById('sessionInfo').innerHTML = JSON.stringify(data, null, 2);
            }
        </script>
    </body>
    </html>
    '''

@app.route('/reset')
def reset_session():
    """Reset session"""
    session.clear()
    return '<html><body style="background:#0f172a;color:white;text-align:center;padding:50px;"><h1>✅ Session Reset</h1><p>Redirecting...</p><script>setTimeout(()=>{window.location.href="/auth";},1500);</script></body></html>'

# ================= SUBSCRIPTION PLANS API =================

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
    return jsonify({
        'success': True,
        'plans': SUBSCRIPTION_PLANS
    })

@app.route('/api/subscription/upgrade', methods=['POST'])
def upgrade_subscription():
    """Upgrade user subscription"""
    try:
        data = request.json
        plan_id = data.get('plan_id')
        
        if plan_id not in SUBSCRIPTION_PLANS:
            return jsonify({'success': False, 'error': 'Invalid plan'}), 400
        
        user_email = session.get('user_email')
        users = session.get('users', {})
        
        if user_email in users:
            users[user_email]['subscription_tier'] = plan_id
            session.modified = True
            
            return jsonify({
                'success': True,
                'message': f'Successfully upgraded to {SUBSCRIPTION_PLANS[plan_id]["name"]}!'
            })
        
        return jsonify({'success': False, 'error': 'User not found'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ================= JSON ROUTES FOR WORDBANK FILES =================

@app.route('/debug/json/<language>')
def debug_json(language):
    import json
    
    json_folder = '/home/auwalkz/app/json'
    file_path = os.path.join(json_folder, f'wordbank_{language}.json')
    
    if not os.path.exists(file_path):
        file_path = os.path.join(json_folder, f'{language}.json')
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {
            'status': 'success',
            'language': language,
            'file': file_path,
            'keys': list(data.keys()) if isinstance(data, dict) else f'Array with {len(data)} items',
            'size': os.path.getsize(file_path),
            'preview': str(data)[:500] + '...' if len(str(data)) > 500 else str(data)
        }
    else:
        return {
            'status': 'error',
            'language': language,
            'file': file_path,
            'message': 'File not found'
        }

@app.route('/api/json/<language>')
def get_json_data(language):
    """API endpoint to get JSON data for a language"""
    import json
    
    json_folder = '/home/auwalkz/app/json'
    file_path = os.path.join(json_folder, f'wordbank_{language}.json')
    
    if not os.path.exists(file_path):
        file_path = os.path.join(json_folder, f'{language}.json')
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            return jsonify(data)
        elif isinstance(data, list):
            return jsonify({'words': data})
        else:
            return jsonify({'data': data})
    else:
        return jsonify({'error': f'No data for {language}', 'words': []}), 404

@app.route('/api/vocabulary/words')
def get_vocabulary_words():
    """Get vocabulary words for a language"""
    import json
    
    language = request.args.get('language', 'en')
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '')
    
    json_folder = '/home/auwalkz/app/json'
    file_path = os.path.join(json_folder, f'wordbank_{language}.json')
    
    if not os.path.exists(file_path):
        file_path = os.path.join(json_folder, f'{language}.json')
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'No vocabulary found', 'words': [], 'page': 1, 'total_pages': 0})
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'words' in data:
        words = data['words']
    elif isinstance(data, list):
        words = data
    else:
        words = []
    
    if search:
        words = [w for w in words if search.lower() in w.get('word', '').lower() or search.lower() in w.get('meaning', '').lower()]
    
    for idx, word in enumerate(words):
        if 'id' not in word:
            word['id'] = str(idx + 1)
        if 'mastery_level' not in word:
            word['mastery_level'] = 0
    
    per_page = 12
    total = len(words)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_words = words[start:end]
    
    return jsonify({
        'success': True,
        'words': paginated_words,
        'page': page,
        'total_pages': total_pages,
        'total': total
    })

@app.route('/api/vocabulary/stats')
def get_vocabulary_stats():
    """Get vocabulary statistics"""
    import json
    
    language = request.args.get('language', 'en')
    
    json_folder = '/home/auwalkz/app/json'
    file_path = os.path.join(json_folder, f'wordbank_{language}.json')
    
    if not os.path.exists(file_path):
        file_path = os.path.join(json_folder, f'{language}.json')
    
    words = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and 'words' in data:
            words = data['words']
        elif isinstance(data, list):
            words = data
    
    total_words = len(words)
    mastered = len([w for w in words if w.get('mastery_level', 0) >= 3])
    learning = len([w for w in words if 0 < w.get('mastery_level', 0) < 3])
    
    return jsonify({
        'success': True,
        'stats': {
            'total_words': total_words,
            'mastered_words': mastered,
            'learning_words': learning,
            'total_practices': 0,
            'streak_days': 0,
            'weekly_progress': 0,
            'average_accuracy': 0
        }
    })

@app.route('/debug-files')
def debug_files():
    files = os.listdir('templates/')
    return {'templates_folder': '/app/templates', 'files': files}

# ================= COMPATIBILITY ENDPOINTS =================

@app.route("/get_user_info", methods=["GET"])
def get_user_info_compat():
    """Compatibility endpoint for frontend - returns user info"""
    subscription_tier = get_user_subscription()
    return jsonify({
        "success": True,
        "user_id": session.get('user_id', 'guest'),
        "name": session.get('user_name', 'Language Learner'),
        "email": session.get('user_email', 'guest@example.com'),
        "language": session.get('language', 'en'),
        "level": session.get('level', 'beginner'),
        "points": session.get('total_points', 0),
        "streak": session.get('streak_days', 0),
        "premium": subscription_tier != 'free',
        "subscription_tier": subscription_tier
    })

@app.route("/api/user/info", methods=["GET"])
def get_user_info_api():
    """API endpoint for user info"""
    subscription_tier = get_user_subscription()
    return jsonify({
        "success": True,
        "user": {
            "id": session.get('user_id', 'guest'),
            "name": session.get('user_name', 'Language Learner'),
            "email": session.get('user_email', ''),
            "language": session.get('language', 'en'),
            "level": session.get('level', 'beginner'),
            "points": session.get('total_points', 0),
            "streak": session.get('streak_days', 0),
            "subscription_tier": subscription_tier,
            "is_premium": subscription_tier != 'free'
        }
    })

# ================= AUTHENTICATION API (for frontend) =================

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Register new user via API"""
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
            'subscription_expires': None,
            'total_points': 0,
            'streak_days': 0,
            'last_active': datetime.now().isoformat(),
            'usage': {}
        }
        session.modified = True
        
        session.permanent = True
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = name if name else email.split('@')[0]
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'email': email,
                'name': name if name else email.split('@')[0],
                'subscription_tier': 'free'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login user via API"""
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
        
        user_data['last_active'] = datetime.now().isoformat()
        session.modified = True
        
        session.permanent = True
        session['user_id'] = user_data['id']
        session['user_email'] = email
        session['user_name'] = user_data['name']
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_data['id'],
                'email': email,
                'name': user_data['name'],
                'subscription_tier': user_data.get('subscription_tier', 'free')
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Logout user"""
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_name', None)
    session.modified = True
    return jsonify({'success': True, 'message': 'Logged out'})

@app.route('/api/auth/status')
def api_auth_status():
    """Get current auth status"""
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    user_name = session.get('user_name')
    subscription_tier = get_user_subscription()
    
    return jsonify({
        'success': True,
        'logged_in': 'user_id' in session,
        'user': {
            'id': user_id,
            'email': user_email,
            'name': user_name,
            'subscription_tier': subscription_tier,
            'is_premium': subscription_tier != 'free'
        } if 'user_id' in session else None
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)