import { useEffect, useRef, useState } from 'react'
import { useChatStream } from './hooks/useChatStream'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import WelcomeScreen from './components/WelcomeScreen'
import MessageList from './components/MessageList'
import Composer from './components/Composer'
import ProblemForm from './components/ProblemForm'
import HelpPanel from './components/HelpPanel'
import PracticePanel from './components/PracticePanel'

export default function App() {
  const { messages, isWaiting, send, solveStructured, reset } = useChatStream()
  const [dark, setDark] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const [showPractice, setShowPractice] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const hasChat = messages.length > 0
  const toggleTheme = () => setDark((d) => !d)

  return (
    <div className="flex h-full bg-slate-50 text-slate-800 dark:bg-slate-950 dark:text-slate-100">
      {/* Sidebar (desktop) */}
      <Sidebar
        dark={dark}
        hasChat={hasChat}
        onOpenPractice={() => setShowPractice(true)}
        onOpenForm={() => setShowForm(true)}
        onOpenHelp={() => setShowHelp(true)}
        onReset={reset}
        onToggleTheme={toggleTheme}
        onQuick={send}
      />

      {/* Cột chính */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Header chỉ hiện trên mobile (desktop dùng sidebar) */}
        <div className="lg:hidden">
          <Header
            dark={dark}
            onToggleTheme={toggleTheme}
            onReset={reset}
            onOpenHelp={() => setShowHelp(true)}
            onOpenPractice={() => setShowPractice(true)}
            hasChat={hasChat}
          />
        </div>

        <main ref={scrollRef} className="scroll-thin flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-4xl px-4 py-6">
            {hasChat ? (
              <MessageList messages={messages} onSuggestion={send} isWaiting={isWaiting} />
            ) : (
              <WelcomeScreen onPick={send} onOpenForm={() => setShowForm(true)} />
            )}
          </div>
        </main>

        <Composer onSend={send} disabled={isWaiting} onOpenForm={() => setShowForm(true)} />
      </div>

      {showForm && <ProblemForm onClose={() => setShowForm(false)} onSolve={solveStructured} />}
      {showHelp && <HelpPanel onClose={() => setShowHelp(false)} />}
      {showPractice && <PracticePanel onClose={() => setShowPractice(false)} />}
    </div>
  )
}
