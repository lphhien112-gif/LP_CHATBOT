import { useCallback, useRef, useState } from 'react'
import { sendChatMessage, solveStructured as solveStructuredApi, resetChatSession } from '../lib/api'
import { resetSessionId } from '../lib/session'

let _id = 0
const nextId = () => `m${++_id}`

const newBotMsg = (id) => ({
  id,
  role: 'bot',
  status: 'streaming',
  htmlChunks: '',
  mdChunks: '',
  text: '',
  allowHtml: false,
  suggestions: [],
  plotImageBase64: null,
})

/**
 * Hook quản lý luồng hội thoại streaming (chat tự do + giải từ form có cấu trúc).
 * Tách riêng accumulator html/markdown để chunk HTML không bị escape khi chunk
 * markdown tới sau.
 */
export function useChatStream() {
  const [messages, setMessages] = useState([])
  const [isWaiting, setIsWaiting] = useState(false)
  const contextRef = useRef(null)
  const abortRef = useRef(null)

  const patch = useCallback((id, updater) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, ...(typeof updater === 'function' ? updater(m) : updater) } : m)),
    )
  }, [])

  // Runner dùng chung: tạo bong bóng user (nếu có) + bot, rồi chạy transport stream.
  const run = useCallback(
    async (userText, transport) => {
      if (isWaiting) return
      setIsWaiting(true)

      const toAdd = []
      if (userText) toAdd.push({ id: nextId(), role: 'user', text: userText })
      const botId = nextId()
      toAdd.push(newBotMsg(botId))
      setMessages((prev) => [...prev, ...toAdd])

      const controller = new AbortController()
      abortRef.current = controller

      await transport(
        {
          onChunk(content, isMarkdown) {
            patch(botId, (m) =>
              isMarkdown ? { mdChunks: m.mdChunks + content } : { htmlChunks: m.htmlChunks + content },
            )
          },
          onComplete(result) {
            if (result.problemContext !== undefined && result.problemContext !== null) {
              contextRef.current = result.problemContext
            }
            patch(botId, {
              status: 'done',
              text: result.textResponse,
              allowHtml: result.allowHtml,
              suggestions: result.suggestions,
              plotImageBase64: result.plotImageBase64,
            })
          },
          onError(err) {
            patch(botId, (m) => ({
              status: 'error',
              text: m.text || `⚠️ ${err.message}`,
              suggestions: ['Thử lại', 'Giải bài toán mẫu'],
            }))
          },
        },
        controller.signal,
      )

      patch(botId, (m) =>
        m.status === 'streaming' ? { status: 'done', text: m.text || m.mdChunks || m.htmlChunks } : m,
      )
      setIsWaiting(false)
      abortRef.current = null
    },
    [isWaiting, patch],
  )

  const send = useCallback(
    (text) => {
      const clean = (text || '').trim()
      if (!clean || isWaiting) return
      if (clean.toLowerCase().includes('bài toán mới')) contextRef.current = null
      return run(clean, (cb, signal) => sendChatMessage(clean, contextRef.current, cb, signal))
    },
    [isWaiting, run],
  )

  // Giải bài toán nhập từ form có cấu trúc. userSummary hiển thị ở bong bóng người dùng.
  const solveStructured = useCallback(
    (problem, solver, userSummary) => {
      if (isWaiting) return
      return run(userSummary, (cb, signal) => solveStructuredApi(problem, solver, cb, signal))
    },
    [isWaiting, run],
  )

  const reset = useCallback(async () => {
    abortRef.current?.abort()
    try {
      await resetChatSession()
    } catch {
      /* ignore */
    }
    resetSessionId()
    contextRef.current = null
    setMessages([])
    setIsWaiting(false)
  }, [])

  return { messages, isWaiting, send, solveStructured, reset }
}
