from flask import Blueprint, request, jsonify
from datetime import datetime
import random

tips_bp = Blueprint("tips", __name__, url_prefix="/api")

@tips_bp.route("/tips/generate", methods=["GET"])
def generate_tips():
    """Generate smart tips - always works, no AI required yet"""
    try:
        category = request.args.get("category", "all")
        language = request.args.get("language", "en")
        count = min(int(request.args.get("count", 6)), 10)
        
        # Get comprehensive tips database
        tips_database = get_comprehensive_tips_database()
        
        # Get tips for the language
        lang_tips = tips_database.get(language, tips_database["en"])
        
        # Filter by category if needed
        if category != "all":
            filtered = [t for t in lang_tips if t.get("category", "").lower() == category.lower()]
            if filtered:
                lang_tips = filtered
        
        # If still no tips, get from English
        if not lang_tips:
            lang_tips = tips_database["en"]
            if category != "all":
                filtered = [t for t in lang_tips if t.get("category", "").lower() == category.lower()]
                if filtered:
                    lang_tips = filtered
        
        # Shuffle for variety
        random.shuffle(lang_tips)
        
        # Use time-based seed for variety
        hour_seed = datetime.now().strftime("%Y-%m-%d-%H")
        random.seed(hour_seed + language + category)
        random.shuffle(lang_tips)
        
        return jsonify({
            "success": True,
            "category": category,
            "language": language,
            "tips": lang_tips[:count],
            "source": "smart_tips",
            "generated_at": datetime.now().isoformat(),
            "message": "💡 Smart tips - refresh for more!"
        })
        
    except Exception as e:
        print(f"Tips generation error: {e}")
        return jsonify({
            "success": True,
            "tips": get_emergency_tips(language)[:count],
            "source": "emergency"
        })

def get_comprehensive_tips_database():
    """Return a comprehensive database of tips in multiple languages"""
    
    return {
        "en": [
            # Language Learning Tips
            {"icon": "💡", "title": "The 15-Minute Rule", "content": "Study for 15 minutes daily - consistency beats intensity for language learning!", "category": "learning"},
            {"icon": "🧠", "title": "Spaced Repetition Magic", "content": "Review words just before you forget them - it's the most efficient way to memorize!", "category": "memory"},
            {"icon": "🎯", "title": "Set SMART Goals", "content": "Specific, Measurable, Achievable, Relevant, Time-bound goals keep you motivated!", "category": "motivation"},
            {"icon": "🗣️", "title": "Shadowing Technique", "content": "Repeat after native speakers immediately - it improves pronunciation and fluency!", "category": "speaking"},
            {"icon": "📱", "title": "Immerse Yourself", "content": "Change your phone's language to your target language - it's free daily practice!", "category": "learning"},
            {"icon": "🎧", "title": "Listen While Commuting", "content": "Use podcasts or audiobooks during your commute - turn wasted time into learning time!", "category": "listening"},
            {"icon": "📖", "title": "Read What You Love", "content": "Read books, articles, or social media posts about topics you actually enjoy!", "category": "reading"},
            {"icon": "✍️", "title": "Keep a Journal", "content": "Write 3 sentences daily about your day - small habit, big results!", "category": "writing"},
            
            # Nigerian/African Culture
            {"icon": "🇳🇬", "title": "Nigeria's Giant Status", "content": "Nigeria is Africa's most populous country with over 200 million people!", "category": "culture"},
            {"icon": "🎬", "title": "Nollywood's Global Reach", "content": "Nigeria's film industry produces more movies annually than Hollywood!", "category": "culture"},
            {"icon": "🦁", "title": "African Elephant Fact", "content": "The African elephant is the largest land animal, weighing up to 6,000 kg!", "category": "nature"},
            {"icon": "🌍", "title": "Linguistic Diversity", "content": "Africa is home to over 2,000 languages - about 30% of the world's languages!", "category": "culture"},
            {"icon": "🦒", "title": "Giraffe Necks", "content": "Giraffes have the same number of neck vertebrae as humans - just 7, but much longer!", "category": "nature"},
            {"icon": "🌿", "title": "Baobab Trees", "content": "Baobab trees can live for over 1,000 years and store up to 30,000 gallons of water!", "category": "nature"},
            
            # Science & Technology
            {"icon": "🔬", "title": "Brain Plasticity", "content": "Your brain can learn new languages at ANY age - neuroplasticity never stops!", "category": "science"},
            {"icon": "🧬", "title": "Human DNA Fact", "content": "Humans share 99.9% of their DNA with each other - we're almost identical!", "category": "science"},
            {"icon": "🤖", "title": "AI Language Learning", "content": "AI tutors can personalize your learning and give instant feedback 24/7!", "category": "technology"},
            {"icon": "🚀", "title": "Space Fact", "content": "One day on Venus is longer than one year on Venus - it rotates very slowly!", "category": "science"},
            {"icon": "💻", "title": "Free Learning Apps", "content": "Use Duolingo, Memrise, Anki, or HelloTalk - all have free versions!", "category": "technology"},
            
            # Environment
            {"icon": "🌎", "title": "Amazon Oxygen", "content": "The Amazon rainforest produces 20% of the world's oxygen!", "category": "environment"},
            {"icon": "🌱", "title": "Tree Communication", "content": "Trees in a forest communicate through underground fungal networks!", "category": "environment"},
            {"icon": "🐝", "title": "Bee Importance", "content": "Bees pollinate 70% of the world's crops - they're essential for food!", "category": "environment"},
            
            # Engineering
            {"icon": "🏗️", "title": "Great Wall Fact", "content": "The Great Wall of China is over 13,000 miles long - visible from space!", "category": "engineering"},
            {"icon": "🌉", "title": "Burj Khalifa", "content": "The Burj Khalifa is the world's tallest building at 828 meters!", "category": "engineering"},
            
            # Motivation
            {"icon": "💪", "title": "Mistakes Are Learning", "content": "Every mistake is a learning opportunity - embrace them, don't fear them!", "category": "motivation"},
            {"icon": "🎉", "title": "Celebrate Small Wins", "content": "Celebrate every new word and correct sentence - progress is progress!", "category": "motivation"},
            {"icon": "🌟", "title": "Consistency Over Perfection", "content": "Showing up every day matters more than being perfect. Just keep going!", "category": "motivation"}
        ],
        
        "ar": [
            {"icon": "💡", "title": "قاعدة الـ 15 دقيقة", "content": "ادرس 15 دقيقة يومياً - الاستمرارية أهم من الشدة في تعلم اللغة!", "category": "learning"},
            {"icon": "🇸🇦", "title": "ثراء اللغة العربية", "content": "اللغة العربية تحتوي على أكثر من 12 مليون كلمة - من أغنى لغات العالم!", "category": "culture"},
            {"icon": "🧠", "title": "التكرار المتباعد", "content": "راجع الكلمات قبل أن تنساها - هذه الطريقة الأكثر فعالية للحفظ!", "category": "memory"},
            {"icon": "📖", "title": "اقرأ ما تحب", "content": "اقرأ كتباً أو مقالات عن مواضيع تستمتع بها - ستتعلم بشكل أسرع!", "category": "reading"},
            {"icon": "🎤", "title": "سجل صوتك", "content": "سجل نفسك وأنت تتحدث واستمع - ستلاحظ تحسناً كبيراً!", "category": "speaking"},
            {"icon": "🇳🇬", "title": "تنوع نيجيريا اللغوي", "content": "نيجيريا تضم أكثر من 500 لغة أصلية - من أكثر الدول تنوعاً لغوياً!", "category": "culture"},
            {"icon": "🔬", "title": "مرونة الدماغ", "content": "يمكن لدماغك تعلم لغة جديدة في أي عمر - المرونة العصبية لا تتوقف!", "category": "science"}
        ],
        
        "fr": [
            {"icon": "💡", "title": "La Règle des 15 Minutes", "content": "Étudiez 15 minutes par jour - la constance bat l'intensité!", "category": "learning"},
            {"icon": "🇫🇷", "title": "Richesse du Français", "content": "Le français compte plus de 100 000 mots dans son dictionnaire officiel!", "category": "culture"},
            {"icon": "🥖", "title": "Gastronomie Française", "content": "La France produit plus de 1000 variétés de fromage différentes!", "category": "culture"},
            {"icon": "📖", "title": "Lisez des BD", "content": "Les bandes dessinées françaises sont excellentes pour apprendre la langue!", "category": "reading"}
        ],
        
        "es": [
            {"icon": "💡", "title": "La Regla de 15 Minutos", "content": "Estudia 15 minutos diarios - la consistencia es clave!", "category": "learning"},
            {"icon": "🇪🇸", "title": "Segundo Idioma Mundial", "content": "El español es el segundo idioma más hablado del mundo!", "category": "culture"},
            {"icon": "💃", "title": "Cultura Latina", "content": "Hay 20 países donde el español es idioma oficial!", "category": "culture"},
            {"icon": "📖", "title": "Lectura Diaria", "content": "Lee noticias en español todos los días - mejora tu vocabulario rápidamente!", "category": "reading"}
        ],
        
        "pt": [
            {"icon": "💡", "title": "Regra dos 15 Minutos", "content": "Estude 15 minutos por dia - consistência é mais importante que intensidade!", "category": "learning"},
            {"icon": "🇧🇷", "title": "Países Lusófonos", "content": "O português é língua oficial em 9 países em 4 continentes diferentes!", "category": "culture"},
            {"icon": "🌍", "title": "Comunidade Global", "content": "Mais de 260 milhões de pessoas falam português no mundo!", "category": "culture"},
            {"icon": "📖", "title": "Leitura Prazerosa", "content": "Leia livros que você ama em português - aprenda naturalmente!", "category": "reading"}
        ],
        
        "sw": [
            {"icon": "💡", "title": "Kanuni ya Dakika 15", "content": "Jifunze dakika 15 kila siku - uthabiti ni muhimu zaidi!", "category": "learning"},
            {"icon": "🇹🇿", "title": "Lugha ya Kiswahili", "content": "Kiswahili kinazungumzwa na zaidi ya watu milioni 200 duniani!", "category": "culture"},
            {"icon": "🦁", "title": "Safari ya Afrika", "content": "Kusema 'Hakuna Matata' ni Kikabila maarufu kutoka Afrika Mashariki!", "category": "culture"},
            {"icon": "📖", "title": "Soma Hadithi", "content": "Soma hadithi fupi za Kiswahili - zitakusaidia kujifunza maneno mapya!", "category": "reading"}
        ]
    }

def get_emergency_tips(language):
    """Ultimate fallback tips - always works"""
    emergency_tips = {
        "en": [
            {"icon": "💡", "title": "Keep Practicing", "content": "Every day of practice brings you closer to fluency!", "category": "motivation"},
            {"icon": "📚", "title": "Learn 5 Words Daily", "content": "Learning just 5 new words a day means 1,825 words per year!", "category": "learning"},
            {"icon": "🎯", "title": "Stay Consistent", "content": "Consistency is more important than the amount of time you study!", "category": "motivation"}
        ],
        "ar": [
            {"icon": "💡", "title": "استمر في الممارسة", "content": "كل يوم من الممارسة يقرّبك من الطلاقة!", "category": "motivation"},
            {"icon": "📚", "title": "تعلم 5 كلمات يومياً", "content": "تعلم 5 كلمات جديدة يومياً يعني 1825 كلمة سنوياً!", "category": "learning"}
        ]
    }
    return emergency_tips.get(language, emergency_tips["en"])