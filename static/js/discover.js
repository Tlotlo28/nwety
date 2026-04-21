const userId = window.CURRENT_USER_ID;
const container = document.getElementById('discover');

const PAGE_LABELS = {
    en: { title: "Discover", subtitle: "Your daily learning", switch: "Switch", chat: "Chat", discover: "Discover" },
    pt: { title: "Descobrir", subtitle: "A tua aprendizagem diária", switch: "Trocar", chat: "Conversa", discover: "Descobrir" },
};

async function load() {
    const [wordRes, libRes, usersRes] = await Promise.all([
        fetch(`/api/words/today/${userId}`),
        fetch(`/api/content/library/${userId}`),
        fetch('/api/users'),
    ]);
    const word = await wordRes.json();
    const library = await libRes.json();
    const users = await usersRes.json();
    const me = users.find(u => u.id === userId);
    const P = PAGE_LABELS[me.language] || PAGE_LABELS.en;
    const L = library.labels;

    document.getElementById('page-title').textContent = P.title;
    document.getElementById('page-subtitle').textContent = P.subtitle;
    document.getElementById('switch-link').textContent = P.switch;
    document.getElementById('nav-chat').textContent = P.chat;
    document.getElementById('nav-discover').textContent = P.discover;

    container.innerHTML = `
        <div class="card">
            <span class="label">${L.word_of_the_day} · ${L.learning_language_display}</span>
            <div class="word-hero">${word.word}</div>
            <div class="word-translation">${word.translation}</div>
            ${word.pronunciation_hint ? `<div class="word-pronunciation">${word.pronunciation_hint}</div>` : ''}
            <button class="play-btn" id="say-word">${Icons.speaker}<span>${L.hear_it}</span></button>
            ${word.example_sentence ? `
                <div class="word-example">
                    <div class="en">${word.example_sentence}</div>
                    <div class="trans">${word.example_translation || ''}</div>
                    <button class="play-btn" id="say-example" style="margin-top: 10px;">${Icons.speaker}<span>${L.hear_example}</span></button>
                </div>` : ''}
        </div>

        <div class="card">
            <span class="label">${L.watch_and_learn}</span>
            <h2>${L.watch_section_heading}</h2>
            <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 8px;">${L.watch_section_subtitle}</p>
            ${library.shows.map(s => `
                <div class="show-item">
                    <strong>${s.title}</strong>
                    <p>${s.description}</p>
                    <div class="meta">${s.level} · ${s.where}</div>
                </div>
            `).join('')}
        </div>

        <div class="card">
            <span class="label">${L.tips_label}</span>
            <h2>${L.tips_heading}</h2>
            ${library.tips.map(t => `<div class="tip">${t}</div>`).join('')}
        </div>
    `;

    document.getElementById('say-word').onclick = () => Speech.speak(word.word, word.language);
    const exBtn = document.getElementById('say-example');
    if (exBtn) exBtn.onclick = () => Speech.speak(word.example_sentence, word.language);
}

load();