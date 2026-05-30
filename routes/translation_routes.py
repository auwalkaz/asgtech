from flask import Blueprint, request, jsonify, session
from datetime import datetime
from services.ai_service import ai_service
from config import config

translation_bp = Blueprint("translation", __name__, url_prefix="/api/translation")

@translation_bp.route("/languages", methods=["GET"])
def get_supported_languages():
    languages = [
        {"code": "en", "name": "English", "flag": "🇬🇧", "native": "English"},
        {"code": "es", "name": "Spanish", "flag": "🇪🇸", "native": "Español"},
        {"code": "fr", "name": "French", "flag": "🇫🇷", "native": "Français"},
        {"code": "de", "name": "German", "flag": "🇩🇪", "native": "Deutsch"},
        {"code": "it", "name": "Italian", "flag": "🇮🇹", "native": "Italiano"},
        {"code": "pt", "name": "Portuguese", "flag": "🇵🇹", "native": "Português"},
        {"code": "ar", "name": "Arabic", "flag": "🇸🇦", "native": "العربية"},
        {"code": "zh", "name": "Chinese", "flag": "🇨🇳", "native": "中文"},
        {"code": "ja", "name": "Japanese", "flag": "🇯🇵", "native": "日本語"},
        {"code": "ko", "name": "Korean", "flag": "🇰🇷", "native": "한국어"},
        {"code": "ru", "name": "Russian", "flag": "🇷🇺", "native": "Русский"},
        {"code": "hi", "name": "Hindi", "flag": "🇮🇳", "native": "हिन्दी"},
        {"code": "sw", "name": "Swahili", "flag": "🇹🇿", "native": "Kiswahili"},
        {"code": "tr", "name": "Turkish", "flag": "🇹🇷", "native": "Türkçe"},
        {"code": "nl", "name": "Dutch", "flag": "🇳🇱", "native": "Nederlands"}
    ]
    return jsonify({"success": True, "languages": languages})

@translation_bp.route("/suggestions", methods=["POST"])
def get_smart_suggestions():
    """Generate alternative ways to say a phrase in the target language"""
    try:
        data = request.json
        text = data.get("text", "").strip()
        target_lang = data.get("target_lang", "es")
        
        if not text:
            return jsonify({"success": False, "error": "No text provided"}), 400
        
        target_name = config.SUPPORTED_LANGUAGES.get(target_lang, {}).get("name", "Spanish")
        
        # Create prompt for AI to generate suggestions in target language
        prompt = f"""Generate 6 different ways to say "{text}" in {target_name}.

Return ONLY valid JSON in this exact format:
[
  {{"text": "casual way to say it in {target_name}", "context": "Casual Conversation", "type": "casual"}},
  {{"text": "formal way to say it in {target_name}", "context": "Formal/Business", "type": "formal"}},
  {{"text": "warm/friendly way to say it in {target_name}", "context": "Warm/Friendly", "type": "warm"}},
  {{"text": "professional way to say it in {target_name}", "context": "Professional Setting", "type": "business"}},
  {{"text": "regional variation in {target_name}", "context": "Regional Dialect", "type": "casual"}},
  {{"text": "learning tip about this phrase in {target_name}", "context": "Learning Tip", "type": "tip"}}
]

Make sure all texts are in {target_name} language. Be creative and provide natural, conversational alternatives."""

        if ai_service.client:
            try:
                result = ai_service.generate_json(prompt, temperature=0.8, max_tokens=800)
                
                # Handle both array and object responses
                if isinstance(result, list):
                    suggestions = result
                elif isinstance(result, dict) and "suggestions" in result:
                    suggestions = result["suggestions"]
                else:
                    suggestions = []
                
                # Ensure each suggestion has required fields
                for s in suggestions:
                    if "context" not in s:
                        s["context"] = get_context_for_type(s.get("type", "casual"))
                    if "type" not in s:
                        s["type"] = "casual"
                
                return jsonify({
                    "success": True,
                    "original": text,
                    "target_lang": target_lang,
                    "target_name": target_name,
                    "suggestions": suggestions[:6],
                    "source": "ai_generated"
                })
            except Exception as e:
                print(f"AI suggestion error: {e}")
                return generate_fallback_suggestions(text, target_lang, target_name)
        else:
            return generate_fallback_suggestions(text, target_lang, target_name)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def get_context_for_type(phrase_type):
    contexts = {
        'casual': 'Casual Conversation',
        'formal': 'Formal/Business',
        'warm': 'Warm/Friendly',
        'business': 'Professional Setting',
        'tip': 'Learning Tip'
    }
    return contexts.get(phrase_type, 'Alternative')


def generate_fallback_suggestions(text, target_lang, target_name):
    """Generate fallback suggestions if AI is unavailable"""
    timestamp = int(datetime.now().timestamp())
    
    suggestions = [
        {"text": f"✨ Casual way to say \"{text}\" in {target_name}", "context": "Casual Conversation", "type": "casual"},
        {"text": f"📝 Formal version of \"{text}\" in {target_name}", "context": "Formal/Business", "type": "formal"},
        {"text": f"💬 Warm and friendly: \"{text}\" in {target_name}", "context": "Warm/Friendly", "type": "warm"},
        {"text": f"💼 Professional: \"{text}\" in {target_name}", "context": "Professional Setting", "type": "business"},
        {"text": f"🌍 Regional variation of \"{text}\" in {target_name}", "context": "Regional Dialect", "type": "casual"},
        {"text": f"💡 Tip: Practice saying \"{text}\" in {target_name} with different tones!", "context": "Learning Tip", "type": "tip"}
    ]
    
    return jsonify({
        "success": True,
        "original": text,
        "target_lang": target_lang,
        "target_name": target_name,
        "suggestions": suggestions,
        "source": "fallback"
    })

@translation_bp.route("/convert", methods=["POST"])
def convert_language():
    try:
        data = request.json
        text = data.get("text", "").strip()
        source_lang = data.get("source_lang", "en")
        target_lang = data.get("target_lang", "es")
        
        if not text:
            return jsonify({"success": False, "error": "No text provided"}), 400
        
        source_name = config.SUPPORTED_LANGUAGES.get(source_lang, {}).get("name", "English")
        target_name = config.SUPPORTED_LANGUAGES.get(target_lang, {}).get("name", "Spanish")
        
        # Comprehensive translation database with cultural notes
        translations = {
            # English to Spanish
            ("en", "es"): {
                "hello": {"text": "hola", "pronunciation": "oh-lah", "culture": "In Spain, use '¡Hola!' casually. In formal situations, say 'Buenos días/tardes/noches'"},
                "good morning": {"text": "buenos días", "pronunciation": "bway-nos dee-as", "culture": "Used until lunch time (around 2 PM) in most Spanish-speaking countries"},
                "thank you": {"text": "gracias", "pronunciation": "grah-see-as", "culture": "Add 'muchas' for 'thank you very much' - 'muchas gracias'"},
                "how are you": {"text": "¿cómo estás?", "pronunciation": "koh-moh es-tas", "culture": "For formal situations, use '¿Cómo está usted?'"},
                "i love you": {"text": "te amo", "pronunciation": "teh ah-moh", "culture": "Use 'te quiero' for family/friends, 'te amo' for romantic love"},
                "i want to drink water": {"text": "quiero beber agua", "pronunciation": "kyeh-roh beh-ber ah-gwah", "culture": "In restaurants, say 'Me gustaría agua' (I would like water) to be more polite"},
                "what is your name": {"text": "¿cómo te llamas?", "pronunciation": "koh-moh teh yah-mas", "culture": "Literally means 'How do you call yourself?' - very common in Spain"},
                "nice to meet you": {"text": "mucho gusto", "pronunciation": "moo-choh goo-stoh", "culture": "Often followed by a handshake or kiss on the cheek in many countries"},
                "where is the bathroom": {"text": "¿dónde está el baño?", "pronunciation": "don-deh es-tah el bah-nyoh", "culture": "In some countries, use 'servicio' instead of 'baño'"}
            },
            # English to French
            ("en", "fr"): {
                "hello": {"text": "bonjour", "pronunciation": "bohn-zhoor", "culture": "Use 'bonjour' until evening, then switch to 'bonsoir'"},
                "good morning": {"text": "bonjour", "pronunciation": "bohn-zhoor", "culture": "French people always greet before asking anything - it's considered rude not to"},
                "thank you": {"text": "merci", "pronunciation": "mer-see", "culture": "Add 'beaucoup' for 'thank you very much' - 'merci beaucoup'"},
                "how are you": {"text": "comment allez-vous?", "pronunciation": "koh-mahn tah-lay-voo", "culture": "Use 'ça va?' for casual, 'comment allez-vous?' for formal"},
                "i love you": {"text": "je t'aime", "pronunciation": "zhuh tem", "culture": "French is the language of love - used for romantic partners only"},
                "i want to drink water": {"text": "je veux boire de l'eau", "pronunciation": "zhuh vuh bwar duh loh", "culture": "In restaurants, say 'Je voudrais de l'eau' (I would like water) to be more polite"},
                "what is your name": {"text": "comment vous appelez-vous?", "pronunciation": "koh-mahn vooz ah-play-voo", "culture": "Literally means 'How do you call yourself?'"},
                "nice to meet you": {"text": "enchanté", "pronunciation": "ahn-shahn-tay", "culture": "Men say 'enchanté', women say 'enchantée'"},
                "where is the bathroom": {"text": "où sont les toilettes?", "pronunciation": "oo sohn lay twah-let", "culture": "Never ask for 'la salle de bain' (bathroom with bath) in public"}
            },
            # English to Arabic
            ("en", "ar"): {
                "hello": {"text": "مرحبا", "pronunciation": "marhaban", "culture": "Common response is 'مرحبتين' (marhabtain) - two hellos!"},
                "good morning": {"text": "صباح الخير", "pronunciation": "sabah al-khayr", "culture": "Response is 'صباح النور' (sabah an-noor) - morning of light"},
                "thank you": {"text": "شكرا", "pronunciation": "shukran", "culture": "Response is 'عفوا' (afwan) - you're welcome"},
                "how are you": {"text": "كيف حالك؟", "pronunciation": "kayfa haluka (m) / haluki (f)", "culture": "Common response: 'الحمد لله' (alhamdulillah) - praise to God"},
                "i love you": {"text": "أحبك", "pronunciation": "uhibbuka (m) / uhibbuki (f)", "culture": "Arabic has separate words for male/female recipients"},
                "i want to drink water": {"text": "أريد أن أشرب الماء", "pronunciation": "uridu an ashraba al-ma'a", "culture": "In cafes, say 'ماء من فضلك' (ma'a min fadlik) - water please"},
                "what is your name": {"text": "ما اسمك؟", "pronunciation": "ma ismuka (m) / ismuki (f)", "culture": "After introducing, say 'تشرفنا' (tasharrafna) - honored to meet you"},
                "nice to meet you": {"text": "تشرفنا", "pronunciation": "tasharrafna", "culture": "Literally means 'we are honored' - very polite"},
                "where is the bathroom": {"text": "أين الحمام؟", "pronunciation": "ayna al-hammam", "culture": "In Arab homes, never ask for bathroom immediately - build conversation first"}
            },
            # English to Portuguese
            ("en", "pt"): {
                "hello": {"text": "olá", "pronunciation": "oh-lah", "culture": "In Brazil, 'Oi!' is more common; in Portugal, 'Olá' is preferred"},
                "good morning": {"text": "bom dia", "pronunciation": "bom dee-ah", "culture": "Used until noon. Brazilians are very warm with greetings!"},
                "thank you": {"text": "obrigado", "pronunciation": "oh-bree-gah-doh", "culture": "Men say 'obrigado', women say 'obrigada'"},
                "how are you": {"text": "como está?", "pronunciation": "koh-moh es-tah", "culture": "Casual: 'Tudo bem?' (too-doo beng) - very common in Brazil"},
                "i love you": {"text": "eu te amo", "pronunciation": "eh-oo chee ah-moo", "culture": "Used for romantic love. For family/friends, use 'eu te adoro'"},
                "i want to drink water": {"text": "quero beber água", "pronunciation": "keh-roo beh-behr ah-gwah", "culture": "Politely: 'Gostaria de água' (I would like water)"},
                "what is your name": {"text": "como se chama?", "pronunciation": "koh-moh see shah-mah", "culture": "Literally 'How do you call yourself?'"},
                "nice to meet you": {"text": "prazer em conhecê-lo", "pronunciation": "prah-zer eng koh-nyeh-seh-loo", "culture": "Casual: 'Prazer!' (Pleasure!)"},
                "where is the bathroom": {"text": "onde fica o banheiro?", "pronunciation": "on-jee fee-kah oo bahn-yeh-roo", "culture": "In Portugal, use 'casa de banho' instead of 'banheiro'"}
            },
            # English to Swahili
            ("en", "sw"): {
                "hello": {"text": "habari", "pronunciation": "hah-bah-ree", "culture": "Response: 'Nzuri' (good) or 'Safi' (clean/fine)"},
                "good morning": {"text": "habari za asubuhi", "pronunciation": "hah-bah-ree zah ah-soo-boo-hee", "culture": "Short response: 'Nzuri' (good)"},
                "thank you": {"text": "asante", "pronunciation": "ah-sahn-teh", "culture": "Add 'sana' for 'thank you very much' - 'asante sana'"},
                "how are you": {"text": "habari yako?", "pronunciation": "hah-bah-ree yah-koh", "culture": "Response: 'Nzuri, asante' (Good, thank you)"},
                "i love you": {"text": "nakupenda", "pronunciation": "nah-koo-pen-dah", "culture": "Used for both romantic and family love in Swahili culture"},
                "i want to drink water": {"text": "nataka kunywa maji", "pronunciation": "nah-tah-kah koon-ywah mah-jee", "culture": "Politely: 'Tafadhali, maji' (Please, water)"},
                "what is your name": {"text": "jina lako nani?", "pronunciation": "jee-nah lah-koh nah-nee", "culture": "Response: 'Jina langu ni...' (My name is...)"},
                "nice to meet you": {"text": "nafurahi kukujua", "pronunciation": "nah-foo-rah-hee koo-koo-joo-ah", "culture": "Warm handshake is important in Swahili culture"},
                "where is the bathroom": {"text": "cho kiko wapi?", "pronunciation": "choh kee-koh wah-pee", "culture": "In East Africa, 'cho' is common slang for toilet"}
            },
            # English to German
            ("en", "de"): {
                "hello": {"text": "hallo", "pronunciation": "hah-loh", "culture": "In Southern Germany/Austria, use 'Servus' or 'Grüß Gott'"},
                "good morning": {"text": "guten morgen", "pronunciation": "goo-ten mor-gen", "culture": "Germans value punctuality and direct greetings"},
                "thank you": {"text": "danke", "pronunciation": "dahn-keh", "culture": "Add 'schön' for 'thank you kindly' - 'danke schön'"},
                "how are you": {"text": "wie geht es dir?", "pronunciation": "vee gayt es deer", "culture": "Germans often answer honestly, not just 'fine'"},
                "i love you": {"text": "ich liebe dich", "pronunciation": "ish lee-beh dish", "culture": "Germans use this sparingly - reserved for deep relationships"},
                "i want to drink water": {"text": "ich möchte wasser trinken", "pronunciation": "ish mur-shtuh vah-ser trin-ken", "culture": "Always use 'möchte' (would like) instead of 'will' (want)"}
            },
            # English to Italian
            ("en", "it"): {
                "hello": {"text": "ciao", "pronunciation": "chow", "culture": "Only for casual/friends. Formal: 'Buongiorno'"},
                "good morning": {"text": "buongiorno", "pronunciation": "bwon-jor-noh", "culture": "Used until lunch. Italians love to greet with enthusiasm!"},
                "thank you": {"text": "grazie", "pronunciation": "grahts-yeh", "culture": "Add 'mille' for 'a thousand thanks' - 'grazie mille'"},
                "how are you": {"text": "come stai?", "pronunciation": "koh-meh sty", "culture": "Italians often answer with 'Bene, grazie' (Good, thanks)"},
                "i love you": {"text": "ti amo", "pronunciation": "tee ah-moh", "culture": "For romantic love. Use 'ti voglio bene' for family/friends"},
                "i want to drink water": {"text": "voglio bere acqua", "pronunciation": "voh-lyoh beh-reh ah-kwah", "culture": "Politely: 'Vorrei dell'acqua' (I would like some water)"}
            }
        }
        
        # Check if we have a direct translation
        text_lower = text.lower().strip()
        translation_key = translations.get((source_lang, target_lang))
        
        if translation_key and text_lower in translation_key:
            result = translation_key[text_lower]
            return jsonify({
                "success": True,
                "original": text,
                "original_lang": source_lang,
                "original_name": source_name,
                "translated": result["text"],
                "target_lang": target_lang,
                "target_name": target_name,
                "pronunciation": result.get("pronunciation", ""),
                "cultural_note": result.get("culture", f"In {target_name}, this phrase is commonly used in daily conversation."),
                "alternative_translations": [],
                "confidence": 95,
                "source": "translation_db"
            })
        
        # Try AI translation if available
        if ai_service.client:
            try:
                prompt = f"""Translate the following from {source_name} to {target_name}.
Text: "{text}"

Return JSON:
{{
  "translated": "translated text",
  "pronunciation": "simple pronunciation guide",
  "cultural_note": "brief cultural context (1 sentence)",
  "alternatives": ["alternative1", "alternative2"]
}}"""
                result = ai_service.generate_json(prompt, temperature=0.5, max_tokens=400)
                
                return jsonify({
                    "success": True,
                    "original": text,
                    "original_lang": source_lang,
                    "original_name": source_name,
                    "translated": result.get("translated", text),
                    "target_lang": target_lang,
                    "target_name": target_name,
                    "pronunciation": result.get("pronunciation", ""),
                    "cultural_note": result.get("cultural_note", f"In {target_name}, this phrase is used in everyday conversation."),
                    "alternative_translations": result.get("alternatives", []),
                    "confidence": 85,
                    "source": "ai_generated"
                })
            except Exception as e:
                print(f"AI translation error: {e}")
        
        # Fallback response
        return jsonify({
            "success": True,
            "original": text,
            "original_lang": source_lang,
            "original_name": source_name,
            "translated": f"[Translation to {target_name}] {text}",
            "target_lang": target_lang,
            "target_name": target_name,
            "pronunciation": "",
            "cultural_note": f"In {target_name}, this phrase would be understood. Practice with a native speaker for perfect pronunciation!",
            "alternative_translations": [],
            "confidence": 60,
            "source": "fallback"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

print("✅ Translation routes loaded with cultural notes!")
