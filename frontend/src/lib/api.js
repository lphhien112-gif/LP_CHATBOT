// Lớp API — bám sát contract backend:
//   POST /send_message        → SSE stream (chunk | chunk_escaped | complete | error)
//   POST /reset_chat_session   → JSON
//   POST /api/v1/lp/solve      → JSON
import { getSessionId } from './session'

/**
 * Gửi tin nhắn chat và đọc luồng SSE.
 * @param {string} message
 * @param {object|null} context
 * @param {{ onChunk:(content:string,isMarkdown:boolean)=>void,
 *           onComplete:(result:object)=>void,
 *           onError:(err:Error)=>void }} cb
 * @param {AbortSignal} [signal]
 */
export async function sendChatMessage(message, context, cb, signal) {
  const form = new FormData()
  form.append('message', message)
  if (context) form.append('context', JSON.stringify(context))

  let res
  try {
    res = await fetch('/send_message', {
      method: 'POST',
      body: form,
      headers: { 'X-Session-Id': getSessionId() },
      signal,
    })
  } catch (e) {
    if (e?.name === 'AbortError') return
    cb.onError(new Error('Không thể kết nối tới server. Kiểm tra kết nối mạng.'))
    return
  }

  if (!res.ok) {
    let detail = `Lỗi server: ${res.status} ${res.statusText}`
    try {
      const j = await res.json()
      detail = j.detail || j.message || detail
      if (typeof detail === 'object') detail = detail.message || JSON.stringify(detail)
    } catch {
      /* ignore */
    }
    cb.onError(new Error(detail))
    return
  }
  if (!res.body) {
    cb.onError(new Error('Trình duyệt không hỗ trợ streaming.'))
    return
  }

  await readSSE(res, cb)
}

/** Đọc luồng SSE (data: {json}\n\n) và phân phối sự kiện. Dùng chung cho chat & form. */
async function readSSE(res, cb) {
  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  const flush = (part) => {
    if (!part.startsWith('data: ')) return
    let parsed
    try {
      parsed = JSON.parse(part.slice(6))
    } catch {
      return
    }
    dispatch(parsed, cb)
  }
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop()
      for (const p of parts) flush(p)
    }
    if (buffer.startsWith('data: ')) flush(buffer)
  } catch (e) {
    if (e?.name === 'AbortError') return
    cb.onError(new Error('Mất kết nối khi nhận phản hồi từ server.'))
  }
}

/**
 * Giải bài toán nhập từ FORM có cấu trúc (bỏ qua parser). Stream SSE như chat.
 * @param {{objective_type:string, variables:string[], objective_coeffs:number[],
 *          constraints:{coeffs:number[],op:string,rhs:number}[]}} problem
 * @param {string} solver
 */
export async function solveStructured(problem, solver, cb, signal) {
  let res
  try {
    res = await fetch('/solve_structured', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Session-Id': getSessionId() },
      body: JSON.stringify({ problem, solver }),
      signal,
    })
  } catch (e) {
    if (e?.name === 'AbortError') return
    cb.onError(new Error('Không thể kết nối tới server.'))
    return
  }
  if (!res.ok || !res.body) {
    cb.onError(new Error(`Lỗi server: ${res.status}`))
    return
  }
  await readSSE(res, cb)
}

function dispatch(data, cb) {
  switch (data.type) {
    case 'chunk':
      cb.onChunk(data.content || '', false) // HTML đã render sẵn
      break
    case 'chunk_escaped':
      cb.onChunk(data.content || '', true) // markdown thô
      break
    case 'complete': {
      const result = data.result || {}
      const bot = result.bot_response || result
      cb.onComplete({
        textResponse: bot.text_response || '',
        allowHtml: bot.allow_html ?? false,
        suggestions: bot.suggestions || [],
        plotImageBase64: bot.plot_image_base64 || result.plot_image_base64 || null,
        problemContext:
          result.problem_context || (result.bot_response && result.bot_response.problem_context) || null,
      })
      break
    }
    case 'error':
      cb.onError(new Error(data.message || 'Server trả về lỗi không xác định.'))
      break
    default:
      break
  }
}

/** Reset phiên hội thoại hiện tại. */
export async function resetChatSession() {
  const res = await fetch('/reset_chat_session', {
    method: 'POST',
    headers: { 'X-Session-Id': getSessionId() },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** Đọc đề bài LP từ ảnh (OCR). Trả về { text } hoặc ném lỗi. */
export async function extractImage(dataUrl) {
  const res = await fetch('/extract_image', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Session-Id': getSessionId() },
    body: JSON.stringify({ image: dataUrl }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.error || `Lỗi đọc ảnh (HTTP ${res.status})`)
  }
  return res.json()
}

/** Tạo một bài luyện tập mới (chế độ tutor). */
export async function practiceNew() {
  const res = await fetch('/practice/new', {
    method: 'POST',
    headers: { 'X-Session-Id': getSessionId() },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** Chấm nghiệm sinh viên nhập cho bài luyện tập hiện tại. */
export async function practiceGrade(answers) {
  const res = await fetch('/practice/grade', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Session-Id': getSessionId() },
    body: JSON.stringify({ answers }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/** Giải trực tiếp một bài toán LP qua REST API. */
export async function solveLP(opts) {
  const res = await fetch('/api/v1/lp/solve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Session-Id': getSessionId() },
    body: JSON.stringify({
      problem_text: opts.problemText || undefined,
      problem_data: opts.problemData || undefined,
      solver_name: opts.solverName || 'pulp_cbc',
      max_iterations: opts.maxIterations || 50,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const msg =
      typeof err.detail === 'string' ? err.detail : err.detail?.message || `HTTP ${res.status}`
    throw new Error(msg)
  }
  return res.json()
}
