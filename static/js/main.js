/**
 * main.js — App Entry Point
 * Binds events, manages app state, orchestrates api.js + ui.js.
 * Imported as type="module" from index.html.
 */
import { sendChatMessage } from './api.js';
import {
    renderMarkdown, renderKatex,
    appendUserMessage, appendBotMessage, appendTypingIndicator,
    appendErrorMessage, showWelcomeState, displaySuggestions,
    setStatusBadge, validateInput, escapeHtml,
} from './ui.js';

// ── DOM References ────────────────────────────────────────────────────────────
const messagesInner = document.getElementById('messages-inner');
const chatMessages  = document.getElementById('chat-messages');
const chatForm      = document.getElementById('chat-form');
const messageInput  = document.getElementById('message-input');
const suggestionArea= document.getElementById('suggestion-area');
const sendButton    = document.getElementById('send-button');
const statusBadge   = document.getElementById('status-badge');
const charCounter   = document.getElementById('char-counter');

// ── App State ─────────────────────────────────────────────────────────────────
let lastProblemContext = null;
let isWaiting = false;

// ── Input Handling ────────────────────────────────────────────────────────────
messageInput.addEventListener('input', () => {
    // Auto-grow textarea
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 160) + 'px';

    const len = messageInput.value.trim().length;
    sendButton.disabled = len === 0 || isWaiting;

    // Character counter visual feedback
    if (charCounter) {
        charCounter.textContent = len > 0 ? `${len}/5000` : '';
        charCounter.classList.toggle('counter-warn', len > 4500);
    }
});

// Enter sends, Shift+Enter inserts newline
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendButton.disabled && !isWaiting) {
            chatForm.dispatchEvent(new Event('submit', { cancelable: true }));
        }
    }
});

// ── Form Submit ───────────────────────────────────────────────────────────────
chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const rawText = messageInput.value;
    const { valid, error } = validateInput(rawText);
    if (!valid) {
        showInputError(error);
        return;
    }
    const text = rawText.trim();
    suggestionArea.innerHTML = '';
    messageInput.value = '';
    messageInput.style.height = 'auto';
    sendButton.disabled = true;
    if (charCounter) charCounter.textContent = '';
    _handleSend(text);
});

// ── Core Message Flow ─────────────────────────────────────────────────────────

/**
 * Streaming strategy:
 *
 * During streaming, we accumulate chunks and show a LIVE PREVIEW.
 * When the 'complete' event fires, we REPLACE the preview with the
 * fully-rendered final content (renderMarkdown + renderKatex).
 *
 * This ensures LaTeX \[...\] blocks (which can be split across chunks)
 * are always rendered correctly in one pass at the end.
 */
async function _handleSend(text) {
    if (isWaiting) return;
    isWaiting = true;
    setStatusBadge(statusBadge, 'waiting');

    appendUserMessage(messagesInner, text);
    const typingEl = appendTypingIndicator(messagesInner);

    let botMsg = null;   // { wrapper, textEl, finalise }
    // We track two separate accumulators:
    // - rawChunks: raw content for streaming preview
    // - seenComplete: whether onComplete has fired
    let rawChunks = '';
    let seenComplete = false;

    await sendChatMessage(text, lastProblemContext, {
        onChunk(content, isMarkdown) {
            if (typingEl.parentNode) typingEl.remove();
            if (!botMsg) botMsg = appendBotMessage(messagesInner, '', true);

            rawChunks += content;

            // Live preview: for markdown chunks, show as monospace preview.
            // For HTML chunks, inject directly (they contain problem summary etc.)
            if (isMarkdown) {
                // Replace entire textEl with a preview showing the accumulated raw text
                botMsg.textEl.innerHTML = `<div class="streaming-preview">${escapeHtml(rawChunks)}</div>`;
            } else {
                // HTML chunk — inject directly for immediate display
                botMsg.textEl.innerHTML = rawChunks;
            }
            botMsg.textEl.scrollIntoView({ behavior: 'smooth', block: 'end' });
        },

        onComplete({ textResponse, allowHtml, suggestions, problemContext }) {
            seenComplete = true;
            if (typingEl.parentNode) typingEl.remove();
            if (!botMsg) botMsg = appendBotMessage(messagesInner, '', false);

            // FINAL RENDER: Parse markdown (preserving LaTeX) → inject → KaTeX render
            // renderMarkdown protects \[...\] and $..$ via placeholders before marked.js,
            // so HTML + LaTeX + Markdown all work correctly in one pass.
            const finalHtml = renderMarkdown(textResponse);
            botMsg.textEl.innerHTML = finalHtml;
            renderKatex(botMsg.textEl);
            botMsg.finalise();  // add copy button

            // Update context for follow-up questions
            if (problemContext) lastProblemContext = problemContext;
            else if (text.toLowerCase().includes('bài toán mới')) lastProblemContext = null;

            if (suggestions && suggestions.length) {
                displaySuggestions(suggestionArea, suggestions, _sendSuggestion);
            }

            botMsg.textEl.scrollIntoView({ behavior: 'smooth', block: 'end' });
        },

        onError(err) {
            if (typingEl.parentNode) typingEl.remove();
            appendErrorMessage(messagesInner, err.message);
            setStatusBadge(statusBadge, 'error');
        },
    });

    // Safety: if stream ended without a 'complete' event, render what we have
    if (!seenComplete && rawChunks && botMsg) {
        const finalHtml = renderMarkdown(rawChunks);
        botMsg.textEl.innerHTML = finalHtml;
        renderKatex(botMsg.textEl);
        botMsg.finalise();
    }

    isWaiting = false;
    setStatusBadge(statusBadge, 'ready');
    sendButton.disabled = messageInput.value.trim() === '';
    messageInput.focus();
}

// ── Suggestion Pills ──────────────────────────────────────────────────────────
function _sendSuggestion(text) {
    const cleanText = text.replace(/✨/g, '').trim();
    suggestionArea.innerHTML = '';
    messageInput.value = '';
    _handleSend(cleanText);
}

// ── Input Validation Error ────────────────────────────────────────────────────
function showInputError(msg) {
    const hint = document.getElementById('input-hint');
    if (!hint) return;
    hint.textContent = msg;
    hint.classList.add('hint-error');
    setTimeout(() => {
        hint.textContent = 'Nhấn Enter để gửi · Shift+Enter để xuống dòng';
        hint.classList.remove('hint-error');
    }, 3000);
}

// ── Initialise ────────────────────────────────────────────────────────────────
function init() {
    // Diagnostics: ensure CDN libs loaded
    if (!window.marked) console.warn('[LP Chatbot] marked.js not loaded — markdown will NOT render');
    if (!window.renderMathInElement) console.warn('[LP Chatbot] KaTeX auto-render not loaded — math will NOT render');
    showWelcomeState(messagesInner, suggestionArea, _sendSuggestion);
    messageInput.focus();
}

init();
