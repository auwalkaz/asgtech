// ===================== VOCABULARY LOADER =====================
// Shared JavaScript for all pages to access JSON files

const API_BASE = '/api';

// Get current language from dashboard
function getCurrentLanguage() {
    // Check sessionStorage (passed from dashboard when clicking cards)
    const sessionLang = sessionStorage.getItem('selectedLanguage');
    if (sessionLang) {
        localStorage.setItem('preferredLanguage', sessionLang);
        return sessionLang;
    }
    // Check localStorage
    const savedLang = localStorage.getItem('preferredLanguage');
    if (savedLang) return savedLang;
    // Check URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const urlLang = urlParams.get('lang');
    if (urlLang) return urlLang;
    // Default to English
    return 'en';
}

// Get current level from dashboard
function getCurrentLevel() {
    const sessionLevel = sessionStorage.getItem('selectedLevel');
    if (sessionLevel) {
        localStorage.setItem('userLevel', sessionLevel);
        return sessionLevel;
    }
    const urlLevel = new URLSearchParams(window.location.search).get('level');
    if (urlLevel) return urlLevel;
    return localStorage.getItem('userLevel') || 'beginner';
}

// Get language name from code
function getLanguageName(code) {
    const names = {
        'en': 'English', 'fr': 'Français', 'es': 'Español', 'pt': 'Português',
        'sw': 'Kiswahili', 'de': 'Deutsch', 'it': 'Italiano', 'zh': '中文',
        'ja': '日本語', 'ko': '한국어', 'ar': 'العربية', 'hi': 'हिन्दी',
        'ru': 'Русский', 'tr': 'Türkçe', 'nl': 'Nederlands'
    };
    return names[code] || 'English';
}

// Get flag emoji from language code
function getFlag(code) {
    const flags = {
        'en': '🇬🇧', 'fr': '🇫🇷', 'es': '🇪🇸', 'pt': '🇵🇹',
        'sw': '🇹🇿', 'de': '🇩🇪', 'it': '🇮🇹', 'zh': '🇨🇳',
        'ja': '🇯🇵', 'ko': '🇰🇷', 'ar': '🇸🇦', 'hi': '🇮🇳',
        'ru': '🇷🇺', 'tr': '🇹🇷', 'nl': '🇳🇱'
    };
    return flags[code] || '🌍';
}

// Fetch vocabulary from JSON API
async function fetchVocabulary(language, level = null) {
    try {
        let url = `${API_BASE}/json/${language}`;
        if (level && level !== 'all') {
            url += `/level/${level}`;
        }
        
        console.log(`Fetching vocabulary from: ${url}`);
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success && data.words) {
            console.log(`✅ Loaded ${data.words.length} words for ${language}`);
            return data.words;
        } else {
            console.log('No words from API, using fallback');
            return getFallbackVocabulary(language, level);
        }
    } catch (error) {
        console.error('Error fetching vocabulary:', error);
        return getFallbackVocabulary(language, level);
    }
}

// Fetch vocabulary by specific level
async function fetchVocabularyByLevel(language, level) {
    return fetchVocabulary(language, level);
}

// Get random words
async function getRandomWords(language, level, count = 10) {
    const words = await fetchVocabulary(language, level);
    if (words.length === 0) return [];
    
    // Shuffle array
    for (let i = words.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [words[i], words[j]] = [words[j], words[i]];
    }
    return words.slice(0, count);
}

// Speak word using browser TTS
function speakWord(word, language) {
    if (!('speechSynthesis' in window)) {
        console.log('Speech not supported');
        showToast('🔊 Voice not supported in this browser', 'warning');
        return;
    }
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(word);
    const langMap = {
        'en': 'en-US', 'sw': 'sw-KE', 'fr': 'fr-FR', 'es': 'es-ES',
        'ar': 'ar-SA', 'pt': 'pt-PT', 'de': 'de-DE', 'it': 'it-IT',
        'zh': 'zh-CN', 'hi': 'hi-IN', 'ja': 'ja-JP', 'ko': 'ko-KR',
        'ru': 'ru-RU', 'tr': 'tr-TR', 'nl': 'nl-NL'
    };
    utterance.lang = langMap[language] || 'en-US';
    utterance.rate = 0.8;
    utterance.pitch = 1.0;
    
    utterance.onerror = (e) => {
        console.error('Speech error:', e);
        showToast('🔊 Voice error, try again', 'error');
    };
    
    window.speechSynthesis.speak(utterance);
}

// Save progress to backend
async function saveProgress(word, action, points = 10, language = null) {
    try {
        const currentLang = language || getCurrentLanguage();
        await fetch(`${API_BASE}/activity/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: action,
                points: points,
                language: currentLang,
                word: word,
                timestamp: new Date().toISOString()
            })
        });
        console.log(`✅ Progress saved: ${action} - ${word}`);
    } catch (error) {
        console.error('Error saving progress:', error);
    }
}

// Update dashboard stats
async function updateDashboardStats() {
    try {
        const language = getCurrentLanguage();
        const response = await fetch(`${API_BASE}/dashboard/stats?language=${language}`);
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            // Update elements if they exist
            if (document.getElementById('totalScore')) {
                document.getElementById('totalScore').textContent = stats.overall_progress || 0;
            }
            if (document.getElementById('streakCount')) {
                document.getElementById('streakCount').textContent = stats.daily_streak || 0;
            }
            if (document.getElementById('masteredCount')) {
                document.getElementById('masteredCount').textContent = stats.words_learned || 0;
            }
            if (document.getElementById('quizScore')) {
                document.getElementById('quizScore').textContent = stats.quiz_score || 0;
            }
        }
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Show toast message
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.padding = '12px 20px';
    toast.style.borderRadius = '8px';
    toast.style.zIndex = '9999';
    toast.style.animation = 'slideIn 0.3s ease';
    toast.style.background = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6';
    toast.style.color = 'white';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Fallback vocabulary if API fails
function getFallbackVocabulary(language, level) {
    const fallback = {
        en: {
            beginner: [
                { word: "cat", meaning: "a small furry pet animal", example: "The cat sleeps.", tip: "Cats say Meow!", part_of_speech: "noun" },
                { word: "dog", meaning: "a loyal pet animal", example: "The dog runs.", tip: "Dog is man's best friend", part_of_speech: "noun" },
                { word: "house", meaning: "a building where people live", example: "Big house.", tip: "Home sweet home", part_of_speech: "noun" },
                { word: "car", meaning: "a vehicle for driving", example: "Red car.", tip: "Transportation", part_of_speech: "noun" },
                { word: "happy", meaning: "feeling joy", example: "Happy day!", tip: "Smile", part_of_speech: "adjective" }
            ],
            intermediate: [
                { word: "analyze", meaning: "to study carefully", example: "Analyze data.", tip: "Examine", part_of_speech: "verb" }
            ],
            advanced: [
                { word: "ubiquitous", meaning: "found everywhere", example: "Smartphones are ubiquitous.", tip: "Everywhere", part_of_speech: "adjective" }
            ]
        },
        sw: {
            beginner: [
                { word: "paka", meaning: "a small furry pet animal", example: "Paka analala.", tip: "Meow!", part_of_speech: "noun" },
                { word: "mbwa", meaning: "a loyal pet animal", example: "Mbwa anakimbia.", tip: "Best friend", part_of_speech: "noun" },
                { word: "nyumba", meaning: "a building where people live", example: "Nyumba kubwa.", tip: "Home", part_of_speech: "noun" }
            ]
        }
    };
    
    const langData = fallback[language] || fallback.en;
    const levelData = langData[level] || langData.beginner;
    return levelData;
}

// Add CSS animation for toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;
document.head.appendChild(style);

console.log('✅ Vocabulary loader initialized');
