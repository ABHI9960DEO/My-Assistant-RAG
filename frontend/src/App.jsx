import { useState, useRef, useEffect } from 'react'
import './App.css'

const API_URL = 'http://localhost:8001'

function SourceBadge({ file, score }) {
  return <span className="source-badge">{file} · {score}</span>
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`message ${isUser ? 'user' : 'agent'}`}>
      <div className="avatar">{isUser ? 'You' : '🤖'}</div>
      <div className="bubble-wrap">
        <div className="bubble">{msg.content}</div>
        {msg.sources?.length > 0 && (
          <div className="sources">
            <span className="sources-label">Sources:</span>
            {msg.sources.map((s, i) => (
              <SourceBadge key={i} file={s.file} score={s.score} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="message agent">
      <div className="avatar">🤖</div>
      <div className="bubble-wrap">
        <div className="bubble typing">
          <span /><span /><span />
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [assistantName, setAssistantName] = useState('AI Assistant')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  // Fetch the assistant's name and set the welcome message.
  useEffect(() => {
    fetch(`${API_URL}/info`)
      .then(r => r.json())
      .then(data => {
        const name = data.name || 'AI Assistant'
        setAssistantName(name)
        setMessages([{
          role: 'agent',
          content: `Hi! I'm ${name}'s AI assistant. Ask me anything about their work, services, or how to get in touch.`,
        }])
      })
      .catch(() => {
        setMessages([{
          role: 'agent',
          content: "Hi! Ask me anything.",
        }])
      })
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function send() {
    const question = input.trim()
    if (!question || loading) return

    setInput('')
    textareaRef.current.style.height = 'auto'
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      const data = await res.json()
      setMessages(prev => [
        ...prev,
        { role: 'agent', content: data.answer, sources: data.sources },
      ])
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'agent', content: "Sorry, I couldn't reach the server. Make sure the backend is running." },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  function handleInput(e) {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  return (
    <div className="app">
      <header>
        <div className="header-logo">🤖</div>
        <div className="header-text">
          <h1>{assistantName}</h1>
          <p>AI Assistant · Powered by RAG + Gemini</p>
        </div>
        <div className="header-status">
          <span className="status-dot" />
          Online
        </div>
      </header>

      <main className="messages">
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </main>

      <footer>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKey}
          placeholder="Ask me anything…"
          rows={1}
          disabled={loading}
        />
        <button onClick={send} disabled={!input.trim() || loading} aria-label="Send">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </footer>
    </div>
  )
}
