# LP_Chatbot — Frontend (React + Vite)

Giao diện chat hiện đại cho trợ lý Quy hoạch tuyến tính: streaming SSE, render LaTeX
(KaTeX) cho lời giải từng bước, dark mode, responsive.

## Công nghệ
- **React 18** + **Vite 5** (build nhanh, HMR)
- **Tailwind CSS 3** (design system, dark mode)
- **KaTeX** (render công thức toán), **marked** (markdown)
- **lucide-react** (icon)

## Cấu trúc
```
frontend/
├── src/
│   ├── lib/        api.js (SSE/REST), markdown.js (LaTeX-safe), session.js
│   ├── hooks/      useChatStream.js — quản lý luồng streaming
│   ├── components/ Header, WelcomeScreen, MessageList, MessageBubble, Composer, …
│   ├── App.jsx     khung ứng dụng + theme
│   └── index.css   design tokens + style markdown/tableau
├── vite.config.js  proxy API sang backend (dev) + build ra ../static/app
└── tailwind.config.js
```

## Phát triển (dev)
Cần backend FastAPI chạy ở cổng 8000 (`uvicorn main:app --reload`).
```bash
cd frontend
npm install
npm run dev          # http://localhost:5173  (proxy API → :8000)
```

## Build cho production
```bash
cd frontend
npm run build        # xuất ra ../static/app
```
Sau khi build, FastAPI tự phục vụ SPA tại `http://localhost:8000/app/` (root `/`
cũng tự chuyển hướng tới đó). Docker đã tự động build bước này.

## Hợp đồng API (backend)
- `POST /send_message` (form `message`, header `X-Session-Id`) → SSE: `chunk` |
  `chunk_escaped` | `complete` | `error`.
- `POST /reset_chat_session` → JSON.
- `POST /api/v1/lp/solve` → JSON (giải trực tiếp).
