/**
 * ui.js — UI Component Library
 * Reusable, accessible UI building blocks for the LP Chatbot.
 * No direct API calls here — only DOM operations.
 */

// ── LaTeX-safe Markdown renderer ──────────────────────────────────────────────
/**
 * Renders markdown to HTML while preserving LaTeX delimiters from marked.js.
 * Strategy: extract LaTeX → placeholders → marked.parse → restore.
 * @param {string} text
 * @returns {string} HTML string
 */
export function renderMarkdown(text) {
    if (!window.marked) return escapeHtml(text).replace(/\n/g, '<br>');
    const saved = [];
    const save = (s) => { const k = `\x02L${saved.length}\x03`; saved.push(s); return k; };
    text = text.replace(/\$\$[\s\S]*?\$\$/g, save);
    text = text.replace(/\\\[[\s\S]*?\\\]/g, save);
    text = text.replace(/\\\([\s\S]*?\\\)/g, save);
    text = text.replace(/\$[^$\n]+?\$/g, save);
    let html = marked.parse(text);
    saved.forEach((blk, i) => { html = html.replace(`\x02L${i}\x03`, blk); });
    return html;
}

/**
 * Triggers KaTeX auto-rendering on a DOM element.
 * @param {HTMLElement} el
 */
export function renderKatex(el) {
    if (!window.renderMathInElement) return;
    renderMathInElement(el, {
        delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$',  right: '$',  display: false },
            { left: '\\[', right: '\\]', display: true },
            { left: '\\(', right: '\\)', display: false },
        ],
        throwOnError: false,
    });
}

// ── Message Builders ──────────────────────────────────────────────────────────

/**
 * Creates and appends a user message bubble.
 * @param {HTMLElement} container
 * @param {string} text — raw text (will be escaped)
 */
export function appendUserMessage(container, text) {
    const el = document.createElement('div');
    el.className = 'msg msg-user';
    el.setAttribute('role', 'listitem');
    el.innerHTML = `<div class="msg-bubble msg-bubble-user">${escapeHtml(text)}</div>`;
    container.appendChild(el);
    scrollLatest(el);
    return el;
}

/** Bot avatar SVG (reused across components) */
const BOT_AVATAR = `
<div class="bot-avatar" aria-hidden="true">
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
    <path stroke-linecap="round" stroke-linejoin="round"
      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0
         002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002
         2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0
         01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
</div>`;

/**
 * Creates and appends a bot message bubble.
 * @param {HTMLElement} container
 * @param {string} html — may be empty initially (for streaming)
 * @param {boolean} streaming — if streaming, don't add copy button yet
 * @returns {{ wrapper: HTMLElement, textEl: HTMLElement, finalise: Function }}
 */
export function appendBotMessage(container, html = '', streaming = false) {
    const wrapper = document.createElement('div');
    wrapper.className = 'msg msg-bot';
    wrapper.setAttribute('role', 'listitem');

    const textEl = document.createElement('div');
    textEl.className = 'msg-bubble msg-bubble-bot bot-text';
    if (html) textEl.innerHTML = html;

    wrapper.insertAdjacentHTML('beforeend', BOT_AVATAR);
    wrapper.appendChild(textEl);
    container.appendChild(wrapper);
    scrollLatest(wrapper);

    function finalise() {
        // Add copy-to-clipboard button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.title = 'Sao chép';
        copyBtn.setAttribute('aria-label', 'Sao chép nội dung tin nhắn');
        copyBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="copy-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>`;
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(textEl.innerText).then(() => {
                copyBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="copy-icon"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>`;
                setTimeout(() => {
                    copyBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="copy-icon"><path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>`;
                }, 2000);
            });
        });
        wrapper.appendChild(copyBtn);
    }

    return { wrapper, textEl, finalise };
}

/**
 * Creates and appends the typing indicator (three animated dots).
 * @param {HTMLElement} container
 * @returns {HTMLElement}
 */
export function appendTypingIndicator(container) {
    const el = document.createElement('div');
    el.className = 'msg msg-bot';
    el.setAttribute('aria-label', 'Bot đang soạn...');
    el.setAttribute('role', 'status');
    el.innerHTML = `${BOT_AVATAR}
        <div class="msg-bubble msg-bubble-bot typing-bubble">
            <span class="typing-dot" aria-hidden="true"></span>
            <span class="typing-dot" aria-hidden="true"></span>
            <span class="typing-dot" aria-hidden="true"></span>
        </div>`;
    container.appendChild(el);
    scrollLatest(el);
    return el;
}

/**
 * Shows an error message as a bot bubble with distinct styling.
 * @param {HTMLElement} container
 * @param {string} text — error description
 */
export function appendErrorMessage(container, text) {
    const el = document.createElement('div');
    el.className = 'msg msg-bot';
    el.setAttribute('role', 'alert');
    el.innerHTML = `${BOT_AVATAR}
        <div class="msg-bubble msg-bubble-error">
            <span class="error-icon">⚠️</span>
            <span>${escapeHtml(text)}</span>
        </div>`;
    container.appendChild(el);
    scrollLatest(el);
}

// ── Empty / Welcome State ───────────────────────────────────────────────────

/**
 * Shows a welcome/empty-state message block with quick-start suggestions.
 * @param {HTMLElement} container
 * @param {HTMLElement} suggArea
 * @param {(text: string) => void} onSuggClick
 */
export function showWelcomeState(container, suggArea, onSuggClick) {
    const { textEl, finalise } = appendBotMessage(container,
        'Xin chào! Tôi là <strong>LP Chatbot</strong> — trợ lý AI chuyên về Quy hoạch Tuyến tính.<br><br>' +
        'Tôi có thể giúp bạn:<br>' +
        '• Nhận diện và giải bài toán LP từ văn bản tự nhiên<br>' +
        '• Giải thích các bước giải (Simplex, 2-pha, Dual, CBC...)<br>' +
        '• Vẽ đồ thị miền khả thi (Geometric method)<br><br>' +
        'Hãy thử bắt đầu bằng một câu hỏi hoặc bài toán! 🚀',
        false
    );
    finalise();
    displaySuggestions(suggArea, [
        'Giải bài toán mẫu',
        'Simplex là gì?',
        'Phương pháp 2 pha là gì?',
        'Bài toán không khả thi là sao?',
    ], onSuggClick);
}

// ── Suggestions ─────────────────────────────────────────────────────────────

/**
 * @param {HTMLElement} area
 * @param {string[]} texts
 * @param {(text: string) => void} onClick
 */
export function displaySuggestions(area, texts, onClick) {
    area.innerHTML = '';
    texts.forEach(text => {
        const btn = document.createElement('button');
        btn.className = 'suggestion-pill';
        btn.textContent = text.replace(/✨/g, '').trim();
        btn.setAttribute('aria-label', `Gợi ý: ${btn.textContent}`);
        btn.addEventListener('click', () => onClick(text));
        area.appendChild(btn);
    });
}

// ── Status Badge ─────────────────────────────────────────────────────────────

/**
 * @param {HTMLElement} badge
 * @param {'ready'|'waiting'|'error'} state
 */
export function setStatusBadge(badge, state) {
    const states = {
        ready:   { dot: 'dot-green',  label: 'Sẵn sàng' },
        waiting: { dot: 'dot-yellow', label: 'Đang phản hồi...' },
        error:   { dot: 'dot-red',    label: 'Lỗi kết nối' },
    };
    const { dot, label } = states[state] || states.ready;
    badge.innerHTML = `<span class="status-dot ${dot}" aria-hidden="true"></span><span>${label}</span>`;
}

// ── Scroll ───────────────────────────────────────────────────────────────────

/** Smooth-scrolls a new element into view at the bottom of the chat. */
export function scrollLatest(el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

// ── Input Validation ─────────────────────────────────────────────────────────

/**
 * Validates user input before sending.
 * @param {string} text
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateInput(text) {
    const t = text.trim();
    if (!t) return { valid: false, error: 'Vui lòng nhập nội dung trước khi gửi.' };
    if (t.length < 3) return { valid: false, error: 'Tin nhắn quá ngắn (tối thiểu 3 ký tự).' };
    if (t.length > 5000) return { valid: false, error: 'Tin nhắn quá dài (tối đa 5000 ký tự).' };
    return { valid: true };
}

// ── Utils ─────────────────────────────────────────────────────────────────────

/** Safely escapes HTML to prevent XSS. */
export function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/\n/g, '<br>');
}
