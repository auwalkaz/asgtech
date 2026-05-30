import json
import random
from pathlib import Path

# Direct imports to avoid circular references
from services.wordnet_service import wordnet_service
from services.ai_service import ai_service

class WordService:
    def __init__(self):
        self.json_folder = Path(__file__).parent.parent / "json"
        self.cache = {}
        print(f"📁 WordService initialized. JSON folder: {self.json_folder}")
    
    def _load_json(self, filename):
        """Load JSON file with caching"""
        if filename in self.cache:
            return self.cache[filename]
        
        filepath = self.json_folder / filename
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache[filename] = data
                    print(f"✅ Loaded {filename}")
                    return data
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
                return {}
        else:
            print(f"⚠️ File not found: {filepath}")
            return {}
    
    def get_language_file(self, language='en'):
        """Get the appropriate wordbank file for a language"""
        lang_files = {
            'en': 'wordbank_en.json',
            'es': 'wordbank_es.json',
            'fr': 'wordbank_fr.json',
            'ar': 'wordbank_ar.json',
            'pt': 'wordbank_pt.json',
            'de': 'wordbank_de.json',
            'it': 'wordbank_it.json',
            'sw': 'wordbank_sw.json',
            'zh': 'wordbank_zh.json'
        }
        
        filename = lang_files.get(language, f'wordbank_{language}.json')
        data = self._load_json(filename)
        
        if data:
            return data
        
        # Fallback to main words.json
        print(f"⚠️ No wordbank for {language}, trying words.json")
        return self._load_json('words.json')
    
    def get_words_from_json(self, language='en', category='general', count=5):
        """Get words from JSON files"""
        data = self.get_language_file(language)
        words = []
        
        if isinstance(data, list):
            words = data
        elif isinstance(data, dict):
            # Try different structures
            if category in data and isinstance(data[category], list):
                words = data[category]
            elif 'words' in data and isinstance(data['words'], list):
                words = data['words']
            elif 'vocabulary' in data and isinstance(data['vocabulary'], list):
                words = data['vocabulary']
            elif 'common_words' in data and isinstance(data['common_words'], list):
                words = data['common_words']
            else:
                # Get first list found
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        words = value
                        break
        
        if words and len(words) >= count:
            return random.sample(words, count)
        return words[:count] if words else []
    
    def get_words_from_wordnet(self, language='en', count=5):
        """Get words from WordNet with definitions"""
        if language != 'en':
            json_words = self.get_words_from_json(language, 'general', count)
            if json_words:
                return [{'word': w, 'meaning': '', 'example': '', 'source': 'json'} for w in json_words]
        
        # Use WordNet for English
        return wordnet_service.get_words('en', count)
    
    def get_words_from_ai(self, language='en', category='general', count=5):
        """Generate words using AI"""
        try:
            from config import config
            lang_name = config.SUPPORTED_LANGUAGES.get(language, {}).get("name", language.upper())
            
            prompt = f"""Generate {count} common {lang_name} words for {category} category.
            Each word should have its meaning and an example sentence.
            
            Return ONLY valid JSON in this format:
            {{"words": [
                {{"word": "word1", "meaning": "meaning in English", "example": "example sentence"}},
                {{"word": "word2", "meaning": "meaning in English", "example": "example sentence"}}
            ]}}"""
            
            result = ai_service.generate_json(prompt, temperature=0.7, max_tokens=800)
            ai_words = result.get('words', [])
            if ai_words:
                print(f"✅ AI generated {len(ai_words)} words for {language}")
                return ai_words[:count]
        except Exception as e:
            print(f"❌ AI generation error: {e}")
        
        return []
    
    def get_words(self, language='en', category='general', count=5, use_wordnet=True, use_ai=True):
        """Get words from multiple sources: JSON -> WordNet -> AI -> Fallback"""
        
        # 1. Try JSON first (fastest)
        json_words = self.get_words_from_json(language, category, count)
        if json_words and len(json_words) >= count:
            print(f"📖 Got {len(json_words)} words from JSON for {language}")
            
            # Enhance with definitions if available and language is English
            enhanced_words = []
            for word in json_words:
                if isinstance(word, str):
                    # Try to get definition from WordNet for English
                    if use_wordnet and language == 'en':
                        wordnet_data = wordnet_service.get_words('en', 10)
                        found = False
                        for wn_word in wordnet_data:
                            if wn_word['word'].lower() == word.lower():
                                enhanced_words.append(wn_word)
                                found = True
                                break
                        if not found:
                            enhanced_words.append({'word': word, 'meaning': '', 'example': '', 'source': 'json'})
                    else:
                        enhanced_words.append({'word': word, 'meaning': '', 'example': '', 'source': 'json'})
                else:
                    enhanced_words.append(word)
            return enhanced_words[:count]
        
        # 2. Try WordNet for English
        if use_wordnet and language == 'en':
            wordnet_words = wordnet_service.get_words('en', count)
            if wordnet_words and len(wordnet_words) >= count:
                print(f"📚 Got {len(wordnet_words)} words from WordNet")
                return wordnet_words[:count]
        
        # 3. Try AI generation
        if use_ai:
            ai_words = self.get_words_from_ai(language, category, count)
            if ai_words:
                return ai_words
        
        # 4. Ultimate fallback
        print(f"⚠️ Using fallback words for {language}")
        fallback_words = {
            'en': ['hello', 'world', 'learn', 'practice', 'language'],
            'es': ['hola', 'mundo', 'aprender', 'practicar', 'idioma'],
            'fr': ['bonjour', 'monde', 'apprendre', 'pratiquer', 'langue'],
            'ar': ['مرحبا', 'عالم', 'تعلم', 'ممارسة', 'لغة'],
            'pt': ['olá', 'mundo', 'aprender', 'praticar', 'idioma']
        }
        
        fb_words = fallback_words.get(language, fallback_words['en'])
        return [{'word': w, 'meaning': 'Common word', 'example': f'Example using {w}', 'source': 'fallback'} 
                for w in fb_words[:count]]
    
    def get_word_bank(self, language='en', level='beginner'):
        """Get word bank for sentence building"""
        data = self.get_language_file(language)
        result = {"theme": "Basic Words", "words": [], "source": "fallback"}
        
        if isinstance(data, dict):
            # Check for various possible structures
            structures_to_try = [
                ('word_banks', level),
                ('themes', level),
                (level, None),
                ('sentences', None),
                ('examples', None)
            ]
            
            for key, subkey in structures_to_try:
                if key in data:
                    if subkey and isinstance(data[key], dict) and subkey in data[key]:
                        bank = data[key][subkey]
                        if isinstance(bank, dict):
                            result.update(bank)
                            result['source'] = f'json.{key}.{subkey}'
                        elif isinstance(bank, list):
                            result['words'] = bank
                            result['source'] = f'json.{key}.{subkey}'
                        break
                    elif isinstance(data[key], list):
                        result['words'] = data[key]
                        result['source'] = f'json.{key}'
                        break
                    elif isinstance(data[key], dict) and 'words' in data[key]:
                        result.update(data[key])
                        result['source'] = f'json.{key}'
                        break
        
        # Ensure we have words
        if not result.get('words'):
            # Try to get from WordNet for English
            if language == 'en':
                wordnet_words = wordnet_service.get_words('en', 8)
                if wordnet_words:
                    result['words'] = [w['word'] for w in wordnet_words]
                    result['theme'] = 'WordNet Vocabulary'
                    result['source'] = 'wordnet'
            else:
                result['words'] = ["I", "like", "to", "learn", "languages", "every", "day"]
                result['source'] = 'hardcoded'
        
        return result
    
    def get_phrases(self, language='en', scenario='greeting', count=5):
        """Get phrases from JSON or generate"""
        data = self.get_language_file(language)
        phrases = []
        
        if isinstance(data, dict):
            if 'phrases' in data:
                phrases = data['phrases']
            elif scenario in data:
                phrases = data[scenario]
            elif 'sentences' in data:
                phrases = data['sentences']
            elif 'examples' in data:
                phrases = data['examples']
        
        if phrases:
            if phrases and isinstance(phrases[0], str):
                phrases = [{"phrase": p, "translation": ""} for p in phrases]
            return phrases[:count]
        
        # Try AI generation for phrases
        try:
            from config import config
            lang_name = config.SUPPORTED_LANGUAGES.get(language, {}).get("name", language.upper())
            prompt = f"Generate {count} common {lang_name} phrases for {scenario} scenario. Return JSON: {{'phrases': [{{'phrase': '', 'translation': ''}}]}}"
            result = ai_service.generate_json(prompt, temperature=0.7, max_tokens=600)
            ai_phrases = result.get('phrases', [])
            if ai_phrases:
                return ai_phrases[:count]
        except Exception as e:
            print(f"AI phrase generation error: {e}")
        
        # Fallback phrases
        fallback_phrases = {
            'en': [
                {"phrase": "Hello, how are you?", "translation": "Greeting"},
                {"phrase": "Nice to meet you!", "translation": "Introduction"},
                {"phrase": "Thank you very much!", "translation": "Gratitude"},
                {"phrase": "Have a nice day!", "translation": "Farewell"},
                {"phrase": "I'm learning a new language.", "translation": "Statement"}
            ]
        }
        return fallback_phrases.get(language, fallback_phrases['en'])[:count]
    
    def get_exercises(self, language='en', exercise_type='spelling', count=5):
        """Get exercises from JSON"""
        data = self.get_language_file(language)
        
        if isinstance(data, dict):
            if exercise_type in data:
                exercises = data[exercise_type]
                if exercises and len(exercises) >= count:
                    return random.sample(exercises, count)
                return exercises[:count]
            elif 'exercises' in data and exercise_type in data['exercises']:
                exercises = data['exercises'][exercise_type]
                return exercises[:count]
        
        # Use words for spelling exercises
        words = self.get_words_from_json(language, 'general', count)
        if words:
            return words
        
        # Use WordNet for English
        if language == 'en':
            wordnet_words = wordnet_service.get_words('en', count)
            if wordnet_words:
                return [w['word'] for w in wordnet_words]
        
        # Ultimate fallback
        return ['hello', 'world', 'beautiful', 'necessary', 'language'][:count]
    
    def get_word_details(self, language='en', word=None):
        """Get detailed word information"""
        # Try JSON first
        data = self.get_language_file(language)
        if data and isinstance(data, dict) and word and word in data:
            return data[word]
        
        # Try WordNet for English
        if language == 'en' and word:
            try:
                from nltk.corpus import wordnet as wn
                synsets = wn.synsets(word)
                if synsets:
                    syn = synsets[0]
                    return {
                        'word': word,
                        'meaning': syn.definition(),
                        'example': syn.examples()[0] if syn.examples() else f"Example using {word}",
                        'pronunciation': word,
                        'source': 'wordnet'
                    }
            except:
                pass
        
        return None
    
    def get_all_themes(self, language='en'):
        """Get all available themes/categories"""
        data = self.get_language_file(language)
        
        if isinstance(data, dict):
            exclude = ['words', 'vocabulary', 'phrases', 'sentences', 'exercises', 'metadata', 'common_words']
            themes = [k for k in data.keys() if k not in exclude and isinstance(data[k], (list, dict))]
            if themes:
                return themes
        
        return ['greetings', 'family', 'travel', 'food', 'work', 'hobbies']
    
    def list_available_languages(self):
        """List all languages with wordbank files"""
        languages = []
        for file in self.json_folder.glob("wordbank_*.json"):
            lang_code = file.stem.replace('wordbank_', '')
            languages.append(lang_code)
        
        # Also check for words.json
        if self._load_json('words.json'):
            languages.append('words_json_fallback')
        
        return languages
    
    def reload_cache(self):
        """Reload all JSON files"""
        self.cache = {}
        print("🔄 Reloading all JSON files...")
        for file in self.json_folder.glob("*.json"):
            self._load_json(file.name)
        print("✅ Cache reloaded")

# Create singleton instance
print("🚀 Creating WordService instance...")
word_service = WordService()
print("✅ WordService initialized")
