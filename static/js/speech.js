// Wraps the browser's Web Speech API for text-to-speech and speech recognition.
// Works on iOS Safari, Chrome, Edge, and most modern browsers. Zero cost.

window.Speech = {
    _voices: [],

    _loadVoices() {
        return new Promise((resolve) => {
            const pick = () => {
                const vs = speechSynthesis.getVoices();
                if (vs.length > 0) {
                    this._voices = vs;
                    resolve(vs);
                }
            };
            pick();
            if (this._voices.length === 0) {
                speechSynthesis.onvoiceschanged = pick;
                setTimeout(pick, 500);
            }
        });
    },

    async speak(text, langCode) {
        if (!window.speechSynthesis) return;
        await this._loadVoices();

        const targetLang = langCode === 'pt' ? 'pt-PT' : 'en-GB';
        // Prefer exact locale, then any matching language
        let voice = this._voices.find(v => v.lang === targetLang)
                 || this._voices.find(v => v.lang.startsWith(langCode));

        const utter = new SpeechSynthesisUtterance(text);
        if (voice) utter.voice = voice;
        utter.lang = voice ? voice.lang : targetLang;
        utter.rate = 0.95;
        utter.pitch = 1.0;
        speechSynthesis.cancel();
        speechSynthesis.speak(utter);
    },

    listen(langCode, onResult, onEnd) {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {
            alert('Voice input is not supported on this browser. Try Chrome or Safari.');
            return null;
        }
        const recog = new SR();
        recog.lang = langCode === 'pt' ? 'pt-PT' : 'en-GB';
        recog.interimResults = false;
        recog.maxAlternatives = 1;
        recog.onresult = (e) => onResult(e.results[0][0].transcript);
        recog.onend = () => onEnd && onEnd();
        recog.onerror = () => onEnd && onEnd();
        recog.start();
        return recog;
    }
};