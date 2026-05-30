import os
import json
from config import config

class VocabularyService:
    def __init__(self):
        self.static_vocab = {}
        self.load_all()
    
    def load_all(self):
        """Load all JSON vocabulary files"""
        for lang_code in config.SUPPORTED_LANGUAGES.keys():
            filepath = os.path.join(config.DATA_FOLDER, f"{lang_code}.json")
            self.static_vocab[lang_code] = {"beginner": [], "intermediate": [], "advanced": []}
            
            try:
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        if isinstance(data, list):
                            for item in data:
                                level = item.get('level', 'beginner')
                                if level in ['beginner', 'intermediate', 'advanced']:
                                    self.static_vocab[lang_code][level].append(item)
                        elif isinstance(data, dict) and 'beginner' in data:
                            for level in ['beginner', 'intermediate', 'advanced']:
                                if level in data:
                                    self.static_vocab[lang_code][level] = data[level]
                        
                        print(f"✅ Loaded {lang_code}: {len(self.static_vocab[lang_code]['beginner'])} words")
            except Exception as e:
                print(f"❌ Error loading {lang_code}: {e}")
    
    def get_words(self, language, level, limit=50):
        if language not in self.static_vocab:
            language = "en"
        return self.static_vocab[language].get(level, [])[:limit]
    
    def search(self, language, query):
        results = []
        for level in ['beginner', 'intermediate', 'advanced']:
            for word in self.static_vocab.get(language, {}).get(level, []):
                if query in word.get('word', '').lower() or query in word.get('meaning', '').lower():
                    word['level'] = level
                    results.append(word)
        return results[:30]

vocab_service = VocabularyService()