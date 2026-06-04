import { useEffect, useRef, useState } from 'react'
import { Check, Copy, Sigma, User } from 'lucide-react'
import { renderMarkdown, renderKatex } from '../lib/markdown'
import SuggestionPills from './SuggestionPills'
import TypingIndicator from './TypingIndicator'

function RenderedContent({ html }) {
  const ref = useRef(null)
  useEffect(() => {
    if (ref.current) renderKatex(ref.current)
  }, [html])
  return (
    <div
      ref={ref}
      className="prose-chat"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

// Nội dung khi đang stream: render LIVE markdown + KaTeX để công thức hiện đẹp
// ngay trong lúc nhận dữ liệu (không còn hiện LaTeX thô). htmlChunks (tóm tắt bài
// toán, HTML thô) được bọc trong <div> riêng để tránh thẻ hở làm vỡ layout;
// mdChunks (markdown + LaTeX) đi qua renderMarkdown. KaTeX dùng throwOnError:false
// nên khối LaTeX chưa nhận đủ sẽ tạm hiện thô rồi tự render khi hoàn tất.
function StreamingContent({ htmlChunks, mdChunks }) {
  const ref = useRef(null)
  const html =
    (htmlChunks ? `<div>${htmlChunks}</div>` : '') +
    (mdChunks ? renderMarkdown(mdChunks) : '')
  useEffect(() => {
    if (ref.current) renderKatex(ref.current)
  }, [html])
  return <div ref={ref} className="prose-chat" dangerouslySetInnerHTML={{ __html: html }} />
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      /* ignore */
    }
  }
  return (
    <button
      onClick={copy}
      title="Sao chép"
      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-slate-400 opacity-0 transition hover:text-slate-700 group-hover:opacity-100 dark:hover:text-slate-200"
    >
      {copied ? <Check size={13} /> : <Copy size={13} />}
      {copied ? 'Đã chép' : 'Chép'}
    </button>
  )
}

export default function MessageBubble({ message, onSuggestion, isWaiting }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex animate-fade-in-up justify-end gap-2.5">
        <div className="max-w-[85%] rounded-2xl rounded-tr-md bg-brand-600 px-4 py-2.5 text-[15px] leading-relaxed text-white shadow-sm">
          {message.text}
        </div>
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-300">
          <User size={16} />
        </div>
      </div>
    )
  }

  // ── Bot message ──────────────────────────────────────────────────────────
  const streaming = message.status === 'streaming'
  const isError = message.status === 'error'

  let body
  if (streaming) {
    const hasContent = message.htmlChunks || message.mdChunks
    body = hasContent ? (
      <StreamingContent htmlChunks={message.htmlChunks} mdChunks={message.mdChunks} />
    ) : (
      <TypingIndicator />
    )
  } else {
    body = <RenderedContent html={renderMarkdown(message.text)} />
  }

  return (
    <div className="group flex animate-fade-in-up gap-2.5">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-sm">
        <Sigma size={16} />
      </div>
      <div className="min-w-0 max-w-[88%] flex-1">
        <div
          className={`rounded-2xl rounded-tl-md border px-4 py-3 shadow-sm ${
            isError
              ? 'border-red-200 bg-red-50 dark:border-red-900/50 dark:bg-red-950/30'
              : 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900'
          }`}
        >
          {body}

          {message.plotImageBase64 && (
            <img
              src={
                message.plotImageBase64.startsWith('data:')
                  ? message.plotImageBase64
                  : `data:image/png;base64,${message.plotImageBase64}`
              }
              alt="Đồ thị miền nghiệm"
              className="mt-3 max-w-full rounded-xl border border-slate-200 dark:border-slate-700"
            />
          )}
        </div>

        {!streaming && (
          <div className="mt-1 flex items-center gap-2 pl-1">
            {message.text && <CopyButton text={message.text} />}
          </div>
        )}

        {!streaming && (
          <SuggestionPills
            suggestions={message.suggestions}
            onPick={onSuggestion}
            disabled={isWaiting}
          />
        )}
      </div>
    </div>
  )
}
