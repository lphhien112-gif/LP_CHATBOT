// Quản lý session-id phía client (gửi qua header X-Session-Id để mỗi trình duyệt
// có phiên hội thoại riêng, không phụ thuộc IP).

const KEY = 'lp_chatbot_session_id'

function generateId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  return 'sess-' + Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export function getSessionId() {
  let id = localStorage.getItem(KEY)
  if (!id) {
    id = generateId()
    localStorage.setItem(KEY, id)
  }
  return id
}

export function resetSessionId() {
  const id = generateId()
  localStorage.setItem(KEY, id)
  return id
}
