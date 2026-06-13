import { useState, useRef, useEffect } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

function SourceBadge({ file, score }) {
  return <span className="source-badge">{file} · {score}</span>
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`message ${isUser ? 'user' : 'agent'}`}>
      <div className="avatar">{isUser ? 'You' : '🤖'}</div>
      <div className="bubble-wrap">
        <div className="bubble">
          {msg.image && <img className="msg-image" src={msg.image} alt="" />}
          {msg.content && <div className="bubble-text">{msg.content}</div>}
        </div>
        {msg.download && (
          <a className="msg-download" href={msg.download} download="edited.png">
            ⬇ Download image
          </a>
        )}
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
  const [imageEditingEnabled, setImageEditingEnabled] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [attachedImage, setAttachedImage] = useState(null)
  const [attachedPreview, setAttachedPreview] = useState(null)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)
  const sessionId = useRef(crypto.randomUUID())

  // Fetch the assistant's name and set the welcome message.
  useEffect(() => {
    fetch(`${API_URL}/info`)
      .then(r => r.json())
      .then(data => {
        const name = data.name || 'AI Assistant'
        setAssistantName(name)
        setImageEditingEnabled(!!data.image_editing)
        setMessages([{
          role: 'agent',
          content: data.image_editing
            ? `Hi! I'm ${name}'s AI assistant. Ask me about their work — or attach a photo and tell me how to edit it.`
            : `Hi! I'm ${name}'s AI assistant. Ask me anything about their work, services, or how to get in touch.`,
        }])
      })
      .catch(() => {
        setMessages([{ role: 'agent', content: 'Hi! Ask me anything, or attach a photo to edit.' }])
      })
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  function resetTextarea() {
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  function pickFile(e) {
    const file = e.target.files?.[0]
    e.target.value = ''  // allow re-selecting the same file later
    if (!file || !file.type.startsWith('image/')) return
    setAttachedImage(file)
    setAttachedPreview(URL.createObjectURL(file))
  }

  function clearAttachment() {
    setAttachedImage(null)
    setAttachedPreview(null)
  }

  async function send() {
    const text = input.trim()
    if (!text || loading) return

    // ── Image-edit flow (a photo is attached) ──
    if (attachedImage) {
      const fileToSend = attachedImage
      const previewUrl = attachedPreview
      setInput('')
      resetTextarea()
      clearAttachment()
      setMessages(prev => [...prev, { role: 'user', content: text, image: previewUrl }])
      setLoading(true)
      try {
        const form = new FormData()
        form.append('prompt', text)
        form.append('image', fileToSend)
        const res = await fetch(`${API_URL}/edit-image`, { method: 'POST', body: form })
        if (!res.ok) {
          let detail = `Server returned ${res.status}.`
          try { detail = (await res.json()).detail || detail } catch { /* not JSON */ }
          throw new Error(detail)
        }
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        setMessages(prev => [...prev, { role: 'agent', content: '', image: url, download: url }])
      } catch (err) {
        setMessages(prev => [...prev, { role: 'agent', content: `Sorry — ${err.message}` }])
      } finally {
        setLoading(false)
      }
      return
    }

    // ── Text RAG flow (no photo attached) ──
    setInput('')
    resetTextarea()
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, session_id: sessionId.current }),
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || `Server error ${res.status}`)
      }
      setMessages(prev => [...prev, { role: 'agent', content: data.answer, sources: data.sources }])
    } catch {
      setMessages(prev => [...prev, { role: 'agent', content: "Sorry, I couldn't reach the server. Make sure the backend is running." }])
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
          <p>AI Assistant · RAG + Image editing</p>
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
        {imageEditingEnabled && attachedPreview && (
          <div className="attachment-preview">
            <img src={attachedPreview} alt="to edit" />
            <button className="remove-attachment" onClick={clearAttachment} aria-label="Remove image">×</button>
          </div>
        )}
        <div className="input-row">
          <input type="file" accept="image/*" ref={fileInputRef} onChange={pickFile} hidden />
          {imageEditingEnabled && <button
            className="attach-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            aria-label="Attach an image to edit"
            title="Attach an image to edit"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="M21 15l-5-5L5 21" />
            </svg>
          </button>}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKey}
            placeholder={attachedImage ? 'Describe the edit you want…' : 'Ask me anything…'}
            rows={1}
            disabled={loading}
          />
          <button onClick={send} disabled={!input.trim() || loading} aria-label="Send">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </footer>
    </div>
  )
}
