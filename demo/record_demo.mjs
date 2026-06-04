// Quay video demo LP_Chatbot bằng Playwright (Node). Backend phải chạy ở http://localhost:8000
// Chạy:  node demo/record_demo.mjs   (từ thư mục gốc repo)
import { createRequire } from 'module'
import { fileURLToPath } from 'url'
import path from 'path'
import fs from 'fs'

const require = createRequire(import.meta.url)
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const { chromium } = require(path.join(ROOT, 'frontend', 'node_modules', 'playwright'))

const RAW_DIR = path.join(ROOT, 'demo', 'raw')
const OCR_IMG = path.join(ROOT, 'demo', 'assets', 'ocr_problem.png')
const BASE = 'http://localhost:8000/app/'
const VW = 1280, VH = 800
fs.mkdirSync(RAW_DIR, { recursive: true })

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// ───────── helpers ─────────
async function caption(page, text, sub = '') {
  await page.evaluate(([t, s]) => {
    let el = document.getElementById('demo-caption')
    if (!el) {
      el = document.createElement('div')
      el.id = 'demo-caption'
      el.style.cssText =
        'position:fixed;left:50%;bottom:104px;transform:translateX(-50%);z-index:99998;' +
        'background:rgba(13,148,136,.96);color:#fff;padding:11px 20px;border-radius:9999px;' +
        'font:600 16px/1.3 system-ui,Segoe UI,sans-serif;box-shadow:0 10px 30px rgba(0,0,0,.3);' +
        'display:flex;gap:9px;align-items:center;transition:opacity .35s;pointer-events:none'
      document.body.appendChild(el)
    }
    el.style.opacity = '1'
    el.innerHTML = s
      ? '<b>' + t + '</b><span style="opacity:.85;font-weight:400">— ' + s + '</span>'
      : t
  }, [text, sub])
}
async function captionHide(page) {
  await page.evaluate(() => {
    const el = document.getElementById('demo-caption')
    if (el) el.style.opacity = '0'
  })
}
async function overlay(page, title, subtitle) {
  await page.evaluate(([t, s]) => {
    let o = document.getElementById('demo-overlay')
    if (!o) {
      o = document.createElement('div')
      o.id = 'demo-overlay'
      document.body.appendChild(o)
    }
    o.style.cssText =
      'position:fixed;inset:0;z-index:100000;display:flex;flex-direction:column;align-items:center;' +
      'justify-content:center;background:linear-gradient(135deg,#0f766e 0%,#0d9488 60%,#10b981 100%);' +
      'color:#fff;font-family:system-ui,Segoe UI,sans-serif;opacity:1;transition:opacity .5s'
    o.innerHTML =
      '<div style="display:flex;align-items:center;gap:14px">' +
      '<div style="width:64px;height:64px;border-radius:18px;background:rgba(255,255,255,.18);' +
      'display:flex;align-items:center;justify-content:center;font-size:38px;font-weight:800">&#8721;</div>' +
      '<div style="font-size:46px;font-weight:800;letter-spacing:-1px">' + t + '</div></div>' +
      '<div style="margin-top:16px;font-size:21px;opacity:.92;max-width:780px;text-align:center">' + s + '</div>'
  }, [title, subtitle])
}
async function overlayOut(page) {
  await page.evaluate(() => {
    const o = document.getElementById('demo-overlay')
    if (o) { o.style.opacity = '0'; setTimeout(() => o.remove(), 520) }
  })
}
async function waitDone(page, timeout = 70000) {
  try { await page.waitForSelector('textarea:not([disabled])', { timeout }) } catch {}
  await sleep(600)
}
async function scrollTo(page, top) {
  await page.evaluate((y) => { const el = document.querySelector('main'); if (el) el.scrollTop = y }, top)
}
async function slowScroll(page, ms = 5500) {
  await page.evaluate((d) => new Promise((res) => {
    const el = document.querySelector('main'); if (!el) return res()
    const start = el.scrollTop, end = el.scrollHeight - el.clientHeight, t0 = performance.now()
    if (end <= start) return res()
    function step(t) {
      const k = Math.min(1, (t - t0) / d)
      el.scrollTop = start + (end - start) * k
      if (k < 1) requestAnimationFrame(step); else res()
    }
    requestAnimationFrame(step)
  }), ms)
}
async function typeProblem(page, text, delay = 32) {
  const ta = page.locator('textarea')
  await ta.click()
  await ta.fill('')
  await ta.pressSequentially(text, { delay })
  await sleep(400)
}
async function selectMethod(page, idx) {
  await page.locator('button[title="Chọn phương pháp giải"]').click()
  await sleep(550)
  await page.locator('div.absolute.bottom-full button').nth(idx).click()
  await sleep(450)
}
async function send(page) { await page.locator('textarea').press('Enter') }
async function resetChat(page) {
  const btn = page.getByRole('button', { name: 'Làm mới hội thoại' })
  if (await btn.count()) { await btn.first().click(); await sleep(900) }
}
async function scene(name, fn) {
  try { await fn() } catch (e) { console.error('SCENE ERROR [' + name + ']:', e.message) }
}

// ───────── storyboard ─────────
async function run(page) {
  await page.goto(BASE, { waitUntil: 'networkidle' })
  await sleep(1200)

  // 0 · INTRO
  await overlay(page, 'LP_Chatbot', 'Trợ lý AI giải Quy hoạch tuyến tính — mô hình hoá &amp; giải từng bước')
  await sleep(3200); await overlayOut(page); await sleep(1400)
  await caption(page, 'Màn hình chính', 'nhập đề bằng công thức, lời, ảnh hoặc biểu mẫu')
  await sleep(2800)

  // 1 · ĐƠN HÌNH từng bước
  await scene('simplex', async () => {
    await caption(page, '1 · Phương pháp Đơn hình', 'lời giải từng bước dạng từ vựng')
    await typeProblem(page, 'Tối đa hóa 3x + 5y với điều kiện x <= 4, 2y <= 12, 3x + 2y <= 18, x, y >= 0')
    await selectMethod(page, 1)
    await send(page)
    await waitDone(page)
    await sleep(900); await scrollTo(page, 0); await sleep(1600)
    await slowScroll(page, 6500); await sleep(1800)
  })

  // 2 · HÌNH HỌC
  await scene('geometric', async () => {
    await resetChat(page)
    await caption(page, '2 · Phương pháp Hình học', 'vẽ miền nghiệm & điểm tối ưu (bài 2 biến)')
    await typeProblem(page, 'Tối thiểu 2x + 3y với x + y >= 4, x + 3y >= 6, x, y >= 0')
    await selectMethod(page, 5)
    await send(page)
    await waitDone(page)
    try { await page.waitForSelector('img[alt="Đồ thị miền nghiệm"]', { timeout: 30000 }) } catch {}
    await sleep(800); await scrollTo(page, 0); await sleep(1400)
    await slowScroll(page, 4500); await sleep(2400)
  })

  // 3 · NHẬP BẰNG LỜI (NLP)
  await scene('nlp', async () => {
    await resetChat(page)
    await caption(page, '3 · Nhập bằng lời', 'AI tự mô hình hoá bài toán thực tế')
    const story = 'Một xưởng làm bàn và ghế. Mỗi bàn lãi 3, mỗi ghế lãi 5. ' +
      'Bàn cần 1 giờ máy, ghế cần 2 giờ, có 12 giờ. Tối đa 4 bàn. Hãy tối đa lợi nhuận.'
    await typeProblem(page, story, 14)
    await send(page)
    await waitDone(page)
    await sleep(900); await scrollTo(page, 0); await sleep(1500)
    await slowScroll(page, 5500); await sleep(1600)
  })

  // 4 · OCR (đọc đề từ ảnh)
  await scene('ocr', async () => {
    await resetChat(page)
    await caption(page, '4 · Đọc đề từ ảnh (OCR)', 'tải ảnh đề — AI đọc rồi điền sẵn')
    const [fc] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.locator('button[title^="Chụp/tải ảnh"]').click(),
    ])
    await fc.setFiles(OCR_IMG)
    try {
      await page.waitForFunction(() => {
        const t = document.querySelector('textarea')
        return t && t.value.trim().length > 5
      }, null, { timeout: 60000 })
    } catch {}
    await sleep(2400)
    await send(page)
    await waitDone(page)
    await sleep(900); await scrollTo(page, 0); await sleep(1400)
    await slowScroll(page, 4500); await sleep(1500)
  })

  // 5 · SO SÁNH PHƯƠNG PHÁP
  await scene('compare', async () => {
    await caption(page, '5 · So sánh phương pháp', 'đối chiếu kết quả nhiều thuật toán')
    const cmp = page.getByRole('button', { name: 'So sánh phương pháp' })
    if (await cmp.count()) {
      await cmp.first().click()
      await waitDone(page)
      await sleep(900); await scrollTo(page, 0); await sleep(1300)
      await slowScroll(page, 4500); await sleep(1600)
    }
  })

  // 6 · LUYỆN TẬP CÓ CHẤM ĐIỂM
  await scene('practice', async () => {
    await caption(page, '6 · Luyện tập có chấm điểm', 'tự sinh đề, tự giải, theo dõi tiến độ')
    const prac = page.getByRole('button', { name: 'Luyện tập có chấm điểm' })
    if (await prac.count()) { await prac.first().click(); await sleep(5000) }
    await sleep(2500)
  })

  // 7 · OUTRO
  await captionHide(page)
  await overlay(page, 'LP_Chatbot', 'Đúng (solver thật, 0 sai lệch so với PuLP) · Trực quan · Hỗ trợ học tập')
  await sleep(3600); await overlayOut(page); await sleep(900)
}

async function main() {
  const browser = await chromium.launch({ headless: true, args: ['--force-color-profile=srgb'] })
  const context = await browser.newContext({
    viewport: { width: VW, height: VH },
    recordVideo: { dir: RAW_DIR, size: { width: VW, height: VH } },
    deviceScaleFactor: 1,
    locale: 'vi-VN',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(30000)
  const video = page.video()
  try {
    await run(page)
  } catch (e) {
    console.error('FATAL:', e.message)
  } finally {
    await context.close()
    await browser.close()
  }
  try {
    const p = await video.path()
    console.log('RAW_VIDEO:' + p)
  } catch (e) {
    console.error('NO VIDEO PATH:', e.message)
  }
}
main()
