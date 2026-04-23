const userId = window.CURRENT_USER_ID;
let currentUser = null;
let otherUser = null;
const renderedIds = new Set();

const messagesEl = document.getElementById('messages');
const textInput = document.getElementById('text-input');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const whoLabel = document.getElementById('who-label');

// Paint SVG icons into composer buttons
if (window.Icons) {
    micBtn.innerHTML = Icons.mic;
    sendBtn.innerHTML = Icons.send;
} else {
    console.error('Icons not loaded — check that /static/js/icons.js is included before chat.js in base.html');
    micBtn.textContent = 'Mic';
    sendBtn.textContent = 'Send';
}

const CHAT_LABELS = {
    en: {
        who: (me, other) => `You're ${me} — chatting with ${other}`,
        switch: "Switch",
        chat: "Chat",
        discover: "Discover",
        emptyTitle: "Say hello",
        emptySub: "Whatever you type will be translated instantly.",
        placeholder: "Type in English…",
        sendErr: "Could not send — check your connection.",
        breakingDown: "Breaking it down…",
        breakdownErr: "Could not load breakdown.",
        delete: "Delete",
        confirmDelete: "Delete this message? This will remove it for both of you.",
        deleted: "Message deleted",
        undo: "Undo",
        deleteErr: "Could not delete — try again.",
    },
    pt: {
        who: (me, other) => `És a ${me} — a conversar com ${other}`,
        switch: "Trocar",
        chat: "Conversa",
        discover: "Descobrir",
        emptyTitle: "Diz olá",
        emptySub: "O que escreveres será traduzido na hora.",
        placeholder: "Escreve em português…",
        sendErr: "Não foi possível enviar — verifica a tua ligação.",
        breakingDown: "A explicar…",
        breakdownErr: "Não foi possível explicar a frase.",
        delete: "Apagar",
        confirmDelete: "Apagar esta mensagem? Vai desaparecer para os dois.",
        deleted: "Mensagem apagada",
        undo: "Anular",
        deleteErr: "Não foi possível apagar — tenta de novo.",
    },
};
let LBL = CHAT_LABELS.en;

// In-memory snapshot of recently-deleted messages so we can undo
const recentlyDeleted = new Map();

function showToast(message, actionLabel, onAction) {
    // Remove any existing toast
    document.querySelector('.toast')?.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <span>${message}</span>
        ${actionLabel ? `<button class="toast-action">${actionLabel}</button>` : ''}
    `;
    document.body.appendChild(toast);

    if (actionLabel && onAction) {
        toast.querySelector('.toast-action').onclick = () => {
            onAction();
            toast.remove();
        };
    }

    // Auto-dismiss after 5s
    setTimeout(() => toast.remove(), 5000);
}

async function deleteMessage(message, element) {
    if (!confirm(LBL.confirmDelete)) return;

    const parent = element.parentNode;
    const nextSibling = element.nextSibling;
    element.remove();
    renderedIds.delete(message.id);

    try {
        const res = await fetch(`/api/chat/messages/${message.id}?user_id=${userId}`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error('Failed');
        showToast(LBL.deleted);
    } catch {
        if (nextSibling) parent.insertBefore(element, nextSibling);
        else parent.appendChild(element);
        renderedIds.add(message.id);
        alert(LBL.deleteErr);
    }
}


async function loadUsers() {
    const res = await fetch('/api/users');
    const users = await res.json();
    currentUser = users.find(u => u.id === userId);
    otherUser = users.find(u => u.id !== userId);
    LBL = CHAT_LABELS[currentUser.language] || CHAT_LABELS.en;

    whoLabel.textContent = LBL.who(currentUser.name, otherUser.name);
    textInput.placeholder = LBL.placeholder;
    document.getElementById('switch-link').textContent = LBL.switch;
    document.getElementById('nav-chat').textContent = LBL.chat;
    document.getElementById('nav-discover').textContent = LBL.discover;

    const emptyTitle = document.getElementById('empty-title');
    const emptySub = document.getElementById('empty-sub');
    if (emptyTitle) emptyTitle.textContent = LBL.emptyTitle;
    if (emptySub) emptySub.textContent = LBL.emptySub;
}

function formatTime(iso) {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function renderBreakdownTokens(tokens) {
    if (!tokens || tokens.length === 0) {
        return '<em style="color: var(--text-muted); font-size: 13px;">No breakdown available.</em>';
    }
    return tokens.filter(t => !t.is_punct).map(t => `
        <span class="token">
            <span class="word">${t.word}</span>
            <span class="arrow">→</span>
            <span class="trans">${t.translation}</span>
            <span class="pos">${t.pos}</span>
        </span>
    `).join('');
}

function renderMessage(m) {
    const isMine = m.sender_id === userId;
    const div = document.createElement('div');
    div.className = `message ${isMine ? 'mine' : 'theirs'}`;

    const primary = isMine ? m.original_text : m.translated_text;
    const secondary = isMine ? m.translated_text : m.original_text;

    // For learning, we always want the breakdown of the OTHER language:
    //  - my message: the translated version (what they'll read)
    //  - their message: the original they wrote (what I should learn to understand)
    const whichForBreakdown = isMine ? 'translation' : 'original';

    div.innerHTML = `
        <div class="original">${primary}</div>
        <div class="translated">${secondary}</div>
         <div class="tools">
            <button class="speak">${Icons.speaker}<span>Pronounce</span></button>
            <button class="learn">${Icons.book}<span>Break down</span></button>
            <button class="delete-btn" aria-label="${LBL.delete}">${Icons.trash}<span>${LBL.delete}</span></button>
        </div>
        <div class="breakdown-panel"></div>
        <div class="time">${formatTime(m.created_at)}</div>
    `;
    const speakText = isMine ? m.translated_text : m.original_text;
    const speakLang = isMine ? m.translated_language : m.original_language;
    div.querySelector('.speak').onclick = () => Speech.speak(speakText, speakLang);

    const panel = div.querySelector('.breakdown-panel');
    const learnBtn = div.querySelector('.learn');
    learnBtn.onclick = async () => {
        if (panel.classList.contains('open')) {
            panel.classList.remove('open');
            return;
        }
        panel.innerHTML = `<em style="color: var(--text-muted); font-size: 13px;">${LBL.breakingDown}</em>`;
        panel.classList.add('open');
        try {
            const res = await fetch(`/api/chat/messages/${m.id}/breakdown?which=${whichForBreakdown}`);
            const data = await res.json();
            panel.innerHTML = renderBreakdownTokens(data.tokens);
        } catch {
            panel.innerHTML = `<em style="color: var(--amber); font-size: 13px;">${LBL.breakdownErr}</em>`;
        }
    };
    div.querySelector('.delete-btn').onclick = () => deleteMessage(m, div);
    return div;
}

function clearEmptyState() {
    const empty = messagesEl.querySelector('.empty');
    if (empty) messagesEl.innerHTML = '';
}

async function loadMessages() {
    const res = await fetch('/api/chat/messages?limit=100');
    const messages = await res.json();

    if (messages.length === 0) {
        if (renderedIds.size === 0) {
            messagesEl.innerHTML = `
                <div class="empty" id="empty-state">
                    <h3>${LBL.emptyTitle}</h3>
                    <p>${LBL.emptySub}</p>
                </div>`;
        }
        return;
    }

    clearEmptyState();
    let appended = false;
    messages.forEach(m => {
        if (!renderedIds.has(m.id)) {
            renderedIds.add(m.id);
            messagesEl.appendChild(renderMessage(m));
            appended = true;
        }
    });
    if (appended) messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendMessage() {
    const text = textInput.value.trim();
    if (!text) return;
    sendBtn.disabled = true;
    sendBtn.classList.add('sending');
    try {
        const res = await fetch('/api/chat/messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, sender_id: userId })
        });
        if (!res.ok) throw new Error('Failed');
        const newMessage = await res.json();

        // Append immediately — no waiting for the next poll.
        clearEmptyState();
        if (!renderedIds.has(newMessage.id)) {
            renderedIds.add(newMessage.id);
            messagesEl.appendChild(renderMessage(newMessage));
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        textInput.value = '';
        textInput.style.height = 'auto';
    } catch {
        alert(LBL.sendErr);
    } finally {
        sendBtn.disabled = false;
        sendBtn.classList.remove('sending');
        textInput.focus();
    }
}

textInput.addEventListener('input', () => {
    textInput.style.height = 'auto';
    textInput.style.height = Math.min(textInput.scrollHeight, 120) + 'px';
});

textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

micBtn.addEventListener('click', () => {
    if (!currentUser) return;
    micBtn.classList.add('listening');
    Speech.listen(currentUser.language,
        (text) => { textInput.value = text; textInput.focus(); },
        () => micBtn.classList.remove('listening'));
});

async function markAsRead() {
    try {
        await fetch(`/api/chat/mark-read/${userId}`, { method: 'POST' });
    } catch { /* non-fatal */ }
}

(async () => {
    await loadUsers();
    await loadMessages();
    await markAsRead();
    setInterval(async () => {
        await loadMessages();
        await markAsRead();
    }, 5000);
})();