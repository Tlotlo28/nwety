const userId = window.CURRENT_USER_ID;
const container = document.getElementById('discover');

async function load() {
    const [wordRes, libRes, usersRes] = await Promise.all([
        fetch(`/api/words/today/${userId}`),
        fetch(`/api/content/library/${userId}`),
        fetch('/api/users'),
    ]);
    const word = await wordRes.json();
    const library = await libRes.json();
    const users = await usersRes.json();

    const learningLabel = library.learning_language === 'pt' ? 'Portuguese' : 'English';

    container.innerHTML = `
        <div class="card">
            <span class="label">Word of the day · ${learningLabel}</span>
            <div class="word-hero">${word.word}</div>
            <div class="word-translation">${word.translation}</div>
            ${word.pronunciation_hint ? `<div class="word-pronunciation">${word.pronunciation_hint}</div>` : ''}
            <button class="play-btn" id="say-word">${Icons.speaker}<span>Hear it</span></button>
            ${word.example_sentence ? `
                <div class="word-example">
                    <div class="en">${word.example_sentence}</div>
                    <div class="trans">${word.example_translation || ''}</div>
                    <button class="play-btn" id="say-example" style="margin-top: 10px;">${Icons.speaker}<span>Hear example</span></button>
                </div>` : ''}
        </div>

        <div class="card">
            <span class="label">Watch & learn</span>
            <h2>TV shows & channels</h2>
            <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 8px;">When you can't chat, watch.</p>
            ${library.shows.map(s => `
                <div class="show-item">
                    <strong>${s.title}</strong>
                    <p>${s.description}</p>
                    <div class="meta">${s.level} · ${s.where}</div>
                </div>
            `).join('')}
        </div>

        <div class="card">
            <span class="label">Quick tips</span>
            <h2>${learningLabel} basics</h2>
            ${library.tips.map(t => `<div class="tip">${t}</div>`).join('')}
        </div>
    `;

    document.getElementById('say-word').onclick = () => Speech.speak(word.word, word.language);
    const exBtn = document.getElementById('say-example');
    if (exBtn) exBtn.onclick = () => Speech.speak(word.example_sentence, word.language);
}

load();