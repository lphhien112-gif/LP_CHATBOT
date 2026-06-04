// Render markdown an toàn với LaTeX: tách các khối toán ra placeholder trước khi
// chạy marked (tránh marked phá cú pháp $...$, \[...\]), sau đó render KaTeX.

import { marked } from 'marked'
import renderMathInElement from 'katex/contrib/auto-render'

marked.setOptions({ gfm: true, breaks: true })

/** Escape HTML cho preview thô (khi chưa có marked). */
export function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/\n/g, '<br>')
}

// Sentinel cho placeholder LaTeX, dùng ký tự điều khiển STX(0x02)/ETX(0x03).
// Các ký tự này không bao giờ xuất hiện trong văn bản người dùng hay output của
// marked, nên tránh lỗi đụng độ kiểu placeholder "L0" trùng với text thật.
const STX = String.fromCharCode(2)
const ETX = String.fromCharCode(3)
const tokenFor = (i) => `${STX}KX${i}${ETX}`

/**
 * Chuyển markdown → HTML, bảo toàn các khối LaTeX.
 * @param {string} text
 * @returns {string} HTML
 */
export function renderMarkdown(text) {
  if (!text) return ''
  const saved = []
  const save = (s) => {
    const key = tokenFor(saved.length)
    saved.push(s)
    return key
  }
  let t = text
    .replace(/\$\$[\s\S]*?\$\$/g, save) // $$ ... $$
    .replace(/\\\[[\s\S]*?\\\]/g, save) // \[ ... \]
    .replace(/\\\([\s\S]*?\\\)/g, save) // \( ... \)
    .replace(/\$[^$\n]+?\$/g, save) // $ ... $

  // Phòng thủ: chuyển các lệnh LaTeX text-mode còn sót NGOÀI math mode sang
  // markdown/HTML, để không hiện chữ thô nếu solver/LLM lỡ xuất \textbf{...},
  // \underline{...}, \textit{...} hay \\ (xuống dòng LaTeX) ngoài $...$.
  t = t
    .replace(/\\underline\s*\{([^{}]*)\}/g, '<u>$1</u>')
    .replace(/\\textbf\s*\{([^{}]*)\}/g, '**$1**')
    .replace(/\\textit\s*\{([^{}]*)\}/g, '*$1*')
    .replace(/\\text\s*\{([^{}]*)\}/g, '$1')
    .replace(/\\\\(?=\s|$)/g, '  \n')

  let html = marked.parse(t)
  saved.forEach((blk, i) => {
    html = html.replace(tokenFor(i), blk)
  })
  return html
}

/** Render mọi công thức KaTeX bên trong một phần tử DOM. */
export function renderKatex(el) {
  if (!el) return
  try {
    renderMathInElement(el, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '\\[', right: '\\]', display: true },
        { left: '\\(', right: '\\)', display: false },
        { left: '$', right: '$', display: false },
      ],
      throwOnError: false,
      errorCallback: (msg, expr) => {
        // Log để dễ debug công thức lỗi, nhưng không ném lỗi (giữ giao diện ổn định).
        if (typeof console !== 'undefined') {
          console.warn('[KaTeX]', msg, '·', String(expr).slice(0, 80))
        }
      },
    })
  } catch {
    /* bỏ qua lỗi render công thức để không vỡ giao diện */
  }
}
