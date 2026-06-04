// Theo dõi tiến độ luyện tập, lưu trong localStorage (theo trình duyệt, không cần
// tài khoản). Dùng cho dashboard.

const KEY = 'lp_practice_progress'
const empty = () => ({ total: 0, correct: 0, streak: 0, bestStreak: 0, attempts: [] })

function load() {
  try {
    return { ...empty(), ...(JSON.parse(localStorage.getItem(KEY)) || {}) }
  } catch {
    return empty()
  }
}
function save(d) {
  try {
    localStorage.setItem(KEY, JSON.stringify(d))
  } catch {
    /* ignore quota */
  }
}

export function getProgress() {
  return load()
}

export function recordAttempt(correct) {
  const d = load()
  d.total += 1
  if (correct) {
    d.correct += 1
    d.streak += 1
    d.bestStreak = Math.max(d.bestStreak, d.streak)
  } else {
    d.streak = 0
  }
  d.attempts.unshift({ correct: !!correct, t: Date.now() })
  d.attempts = d.attempts.slice(0, 60)
  save(d)
  return d
}

export function resetProgress() {
  save(empty())
  return empty()
}
