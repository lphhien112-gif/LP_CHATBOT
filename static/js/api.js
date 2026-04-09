/**
 * api.js — API Layer
 * Strictly follows the backend API contract:
 *   POST /send_message  → SSE stream
 *   POST /api/v1/lp/solve → JSON response
 */

/** @typedef {{ type: string, content?: string, result?: object }} SSEEvent */

/**
 * Sends a chat message and reads the SSE response stream.
 * @param {string} message
 * @param {object|null} context
 * @param {{ onChunk: (html: string) => void, onComplete: (result: object) => void, onError: (err: Error) => void }} callbacks
 */
export async function sendChatMessage(message, context, callbacks) {
    const formData = new FormData();
    formData.append('message', message);
    if (context) formData.append('context', JSON.stringify(context));

    let response;
    try {
        response = await fetch('/send_message', { method: 'POST', body: formData });
    } catch (networkErr) {
        callbacks.onError(new Error('Không thể kết nối tới server. Kiểm tra kết nối mạng.'));
        return;
    }

    if (!response.ok) {
        // Try to parse JSON error body
        let detail = `Lỗi server: ${response.status} ${response.statusText}`;
        try {
            const errJson = await response.json();
            detail = errJson.detail || errJson.message || detail;
            if (typeof detail === 'object') detail = detail.message || JSON.stringify(detail);
        } catch (_) { /* ignore */ }
        callbacks.onError(new Error(detail));
        return;
    }

    if (!response.body) {
        callbacks.onError(new Error('Trình duyệt không hỗ trợ streaming.'));
        return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop(); // keep incomplete chunk

            for (const part of parts) {
                if (!part.startsWith('data: ')) continue;
                let parsed;
                try { parsed = JSON.parse(part.substring(6)); }
                catch (_) { continue; }
                _dispatchSSEEvent(parsed, callbacks);
            }
        }
        // Handle any remaining buffer
        if (buffer.startsWith('data: ')) {
            try {
                const parsed = JSON.parse(buffer.substring(6));
                _dispatchSSEEvent(parsed, callbacks);
            } catch (_) { /* incomplete chunk, ignore */ }
        }
    } catch (streamErr) {
        callbacks.onError(new Error('Mất kết nối khi nhận phản hồi từ server.'));
    }
}

/**
 * Dispatches a parsed SSE event to the correct callback.
 * @param {SSEEvent} data
 * @param {{ onChunk: Function, onComplete: Function }} callbacks
 */
function _dispatchSSEEvent(data, callbacks) {
    if (data.type === 'chunk') {
        // Already-rendered HTML from backend (problem summary, images, etc.)
        callbacks.onChunk(data.content || '', false);
    } else if (data.type === 'chunk_escaped') {
        // Raw Markdown from backend (simplex tableaus, LLM text chunks)
        callbacks.onChunk(data.content || '', true);
    } else if (data.type === 'complete') {
        // Backend sends result FLAT (primary) or nested under bot_response (fallback)
        const result = data.result || {};
        const botRes = result.bot_response || result;
        callbacks.onComplete({
            textResponse: botRes.text_response || '',
            allowHtml:    botRes.allow_html    ?? false,
            suggestions:  botRes.suggestions   || [],
            problemContext: result.problem_context
                         || (result.bot_response && result.bot_response.problem_context)
                         || null,
        });
    } else if (data.type === 'error') {
        callbacks.onError(new Error(data.message || 'Server trả về lỗi không xác định.'));
    }
}

/**
 * Directly solves an LP problem via the REST API.
 * @param {{ problemText?: string, problemData?: object, solverName?: string, maxIterations?: number }} opts
 * @returns {Promise<{ solution: object|null, logs: string[], message: string }>}
 */
export async function solveLP(opts) {
    const res = await fetch('/api/v1/lp/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            problem_text:  opts.problemText   || undefined,
            problem_data:  opts.problemData   || undefined,
            solver_name:   opts.solverName    || 'pulp_cbc',
            max_iterations: opts.maxIterations || 50,
        }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const msg = typeof err.detail === 'string' ? err.detail
                   : err.detail?.message || `HTTP ${res.status}`;
        throw new Error(msg);
    }
    return res.json();
}
