from flask import Blueprint, request, jsonify
from datetime import datetime
import random
import json
import os

# Import AI service
from services.ai_service import ai_service

tips_bp = Blueprint("tips", __name__, url_prefix="/api")

# Cache for AI-generated tips (short-lived for variety)
tips_cache = {}
last_cache_clear = datetime.now()

# Comprehensive topic list for unlimited variety
ALL_TOPICS = [
    "nature", "wildlife", "ocean", "forests", "mountains", "deserts", "rivers", "volcanoes", "earthquakes",
    "history", "ancient civilizations", "egypt", "rome", "greece", "china", "maya", "inca", "aztec",
    "cities", "landmarks", "paris", "tokyo", "new york", "london", "dubai", "singapore", "sydney",
    "science", "physics", "chemistry", "biology", "astronomy", "geology", "medicine", "genetics",
    "space", "planets", "stars", "galaxies", "black holes", "nasa", "astronauts", "telescopes",
    "animals", "mammals", "birds", "reptiles", "insects", "sea creatures", "dinosaurs", "endangered species",
    "technology", "ai", "robotics", "computers", "internet", "smartphones", "gaming", "virtual reality",
    "art", "painting", "sculpture", "famous artists", "museums", "renaissance", "modern art",
    "music", "instruments", "composers", "bands", "concerts", "music history", "genres",
    "sports", "olympics", "world cup", "basketball", "soccer", "tennis", "swimming", "athletics",
    "food", "cuisine", "cooking", "ingredients", "restaurants", "street food", "baking",
    "engineering", "bridges", "buildings", "dams", "tunnels", "skyscrapers", "roads",
    "architecture", "cathedrals", "temples", "mosques", "pyramids", "castles", "palaces",
    "culture", "traditions", "festivals", "holidays", "clothing", "dance", "theatre",
    "literature", "books", "authors", "poetry", "novels", "libraries", "writing",
    "mythology", "greek myths", "norse legends", "egyptian gods", "folk tales",
    "psychology", "brain", "memory", "learning", "emotions", "dreams", "intelligence",
    "business", "entrepreneurship", "companies", "marketing", "leadership", "innovation",
    "environment", "climate change", "renewable energy", "recycling", "conservation", "pollution"
]

# Topic emoji mapping
TOPIC_EMOJIS = {
    "nature": "🌍", "wildlife": "🦁", "ocean": "🌊", "forests": "🌲", "mountains": "🏔️", "deserts": "🏜️", "volcanoes": "🌋",
    "history": "🏛️", "ancient civilizations": "🗿", "egypt": "🐫", "rome": "🏟️", "greece": "🏺",
    "cities": "🏙️", "landmarks": "🗽", "paris": "🗼", "tokyo": "🗻", "new york": "🗽",
    "science": "🔬", "physics": "⚛️", "chemistry": "🧪", "biology": "🧬", "astronomy": "🔭",
    "space": "🚀", "planets": "🪐", "stars": "⭐", "galaxies": "🌌", "black holes": "⚫",
    "animals": "🐘", "dinosaurs": "🦕", "birds": "🦅", "sea creatures": "🐋",
    "technology": "🤖", "ai": "🧠", "robotics": "🦾", "computers": "💻", "internet": "🌐",
    "art": "🎨", "music": "🎵", "sports": "⚽", "food": "🍕", "engineering": "🏗️",
    "architecture": "🏛️", "culture": "🎭", "literature": "📚", "mythology": "🔱",
    "psychology": "🧠", "business": "💼", "environment": "🌱"
}

@tips_bp.route("/tips/generate", methods=["GET"])
def generate_tips():
    """Generate UNLIMITED AI-generated tips - always fresh, always unique"""
    try:
        category = request.args.get("category", "all")
        language = request.args.get("language", "en")
        count = min(int(request.args.get("count", 6)), 10)
        force_fresh = request.args.get("refresh", "false").lower() == "true"
        
        # Clear old cache every 30 minutes for maximum freshness
        global last_cache_clear
        if (datetime.now() - last_cache_clear).seconds > 1800:  # 30 minutes
            tips_cache.clear()
            last_cache_clear = datetime.now()
            print("🔄 Tips cache cleared for maximum freshness")
        
        # ALWAYS try AI first - this is the primary source
        ai_tips = get_ai_generated_tips(language, category, count, force_fresh)
        
        if ai_tips and len(ai_tips) > 0:
            return jsonify({
                "success": True,
                "category": category,
                "language": language,
                "tips": ai_tips,
                "source": "ai_generated",
                "generated_at": datetime.now().isoformat(),
                "message": "🤖 AI-generated fresh tips! Refresh for UNLIMITED new tips!",
                "unlimited": True,
                "topics_count": len(ALL_TOPICS)
            })
        
        # Only use static as emergency fallback (should rarely happen)
        print("⚠️ AI failed, using emergency fallback tips")
        return jsonify({
            "success": True,
            "category": category,
            "language": language,
            "tips": get_emergency_tips(language)[:count],
            "source": "emergency_fallback",
            "message": "⚠️ AI temporarily unavailable. Please try again for fresh tips!"
        })
        
    except Exception as e:
        print(f"Tips generation error: {e}")
        return jsonify({
            "success": True,
            "tips": get_emergency_tips("en")[:count],
            "source": "emergency"
        })

def get_ai_generated_tips(language, category, count, force_fresh=False):
    """Generate UNLIMITED fresh AI tips - completely random and unique each time"""
    global tips_cache
    
    # Use timestamp for maximum freshness (cache only for 30 minutes)
    current_hour = datetime.now().strftime("%Y-%m-%d-%H")
    minute_seed = datetime.now().strftime("%M")
    cache_key = f"{language}_{category}_{current_hour}_{minute_seed}"
    
    # Only use cache if not forcing fresh and cache is very recent (within same 5 minutes)
    if not force_fresh and cache_key in tips_cache and len(tips_cache[cache_key]) >= count:
        cached_tips = tips_cache[cache_key][:count]
        random.shuffle(cached_tips)
        print(f"📦 Using cached tips (still fresh from this session)")
        return cached_tips
    
    if not ai_service or not ai_service.client:
        print("⚠️ AI service not available")
        return None
    
    try:
        # Language names
        language_names = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'sw': 'Swahili', 'ar': 'Arabic',
            'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'hi': 'Hindi',
            'ru': 'Russian', 'tr': 'Turkish', 'nl': 'Dutch'
        }
        
        lang_name = language_names.get(language, 'English')
        
        # Select 3 random topics for variety in each batch
        random_topics = random.sample(ALL_TOPICS, min(3, len(ALL_TOPICS)))
        random_seed = random.randint(1, 999999)
        time_seed = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        
        # Build topic prompt
        topics_text = ", ".join(random_topics)
        
        prompt = f"""You are a fascinating fact generator. Generate {count} completely UNIQUE, surprising, and educational facts about RANDOM topics from this list: {topics_text}

IMPORTANT RULES:
1. Each fact must be from a DIFFERENT topic
2. Facts should be surprising, interesting, and memorable
3. Include a mix of: amazing discoveries, little-known facts, world records, historical events, scientific breakthroughs
4. Make each fact something people would want to share with friends
5. Keep facts factual and educational

Random seed for uniqueness: {random_seed}{time_seed}

Return ONLY valid JSON array, NO markdown, NO extra text.

Each fact must be a JSON object with:
- "icon": a relevant emoji (choose from: 🌍 🏛️ 🏙️ 🔬 🚀 🦁 🤖 🎨 🎵 ⚽ 🍕 🏗️ 🌊 🏔️ 🗿 🦕 🧬 🌌)
- "title": short catchy title (max 50 characters)
- "content": the fascinating fact (max 150 characters)
- "category": the topic category

Example:
{{"icon": "🦕", "title": "T-Rex Bite Force", "content": "T-Rex had the strongest bite force of any land animal ever - 12,800 pounds!", "category": "animals"}}

Generate {count} UNIQUE, DIVERSE facts. Make each one different from the others. Return as JSON array."""

        print(f"🤖 AI generating {count} fresh tips (topics: {topics_text})")
        
        # Use AI service to generate JSON
        result = ai_service.generate_json(prompt, temperature=0.95, max_tokens=1500)
        
        if result and isinstance(result, list) and len(result) > 0:
            valid_tips = []
            for tip in result[:count]:
                if isinstance(tip, dict) and 'content' in tip and len(tip.get('content', '')) > 10:
                    # Ensure icon is appropriate
                    icon = tip.get("icon", "💡")
                    if len(icon) > 2:  # Not an emoji
                        icon = "💡"
                    
                    valid_tips.append({
                        "icon": icon,
                        "title": tip.get("title", "Amazing Fact")[:50],
                        "content": tip.get("content", "")[:200],
                        "category": tip.get("category", "general")
                    })
            
            if len(valid_tips) >= count // 2:  # At least half the requested count
                # Cache the tips
                tips_cache[cache_key] = valid_tips
                print(f"✅ AI generated {len(valid_tips)} UNIQUE fresh tips!")
                return valid_tips
        
        print(f"⚠️ AI returned invalid response, retrying...")
        return None
        
    except Exception as e:
        print(f"❌ AI tips generation error: {e}")
        return None

def get_emergency_tips(language):
    """Emergency fallback - only used if AI completely fails"""
    return [
        {"icon": "🤖", "title": "AI Tips Loading", "content": "Please click 'Get New Tips' again for AI-generated content!", "category": "info"},
        {"icon": "💡", "title": "Unlimited Facts", "content": "Our AI generates fresh facts every time - try again!", "category": "info"},
        {"icon": "🚀", "title": "Coming Soon", "content": "More amazing facts being generated. Click refresh!", "category": "info"}
    ]

print("✅ UNLIMITED AI TIPS loaded - every click generates fresh, unique content!")