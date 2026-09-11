import { useState, useRef, useEffect } from 'react'
import { sendChatMessage } from '../services/api'
import { MessageCircle, X, Send, Bot, User, Minimize2, AlertCircle } from 'lucide-react'

function MessageText({ text }) {
  const lines = text.split('\n')
  return (
    <div style={{ fontSize: '0.85rem', lineHeight: 1.65 }}>
      {lines.map((line, i) => {
        if (!line.trim()) return <br key={i} />
        if (line.trim().startsWith('* ') || line.trim().startsWith('- ')) {
          const content = line.trim().slice(2)
          return (
            <div key={i} style={{ display: 'flex', gap: 6, marginBottom: 2 }}>
              <span style={{ color: 'var(--teal)', flexShrink: 0, marginTop: 2 }}>•</span>
              <span dangerouslySetInnerHTML={{ __html: boldify(content) }} />
            </div>
          )
        }
        return <p key={i} style={{ marginBottom: 4 }} dangerouslySetInnerHTML={{ __html: boldify(line) }} />
      })}
    </div>
  )
}

function boldify(text) {
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

const SUGGESTED = [
  'What are common diabetes symptoms?',
  'How do I lower high blood pressure naturally?',
  'What does chest pain indicate?',
  'Tips for a heart-healthy diet?',
]

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false)
  const [minimized, setMinimized] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! I'm **MediBot**, your AI medical assistant. I can help with health questions, symptom information, and general wellness advice.\n\n⚠️ Always consult a qualified doctor for diagnosis or treatment."
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [unread, setUnread] = useState(0)
  const bottomRef = useRef()
  const inputRef = useRef()

  useEffect(() => {
    if (open) {
      setUnread(0)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [open])

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  const send = async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')

    // Add user message to display
    const userMsg = { role: 'user', content: msg }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      // Send PREVIOUS messages as history (skip welcome message at index 0)
      // Current message is sent separately as body.message
      const history = messages
        .slice(1)                          // skip the welcome assistant message
        .map(m => ({ role: m.role, content: m.content }))

      const { data } = await sendChatMessage(msg, history)
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }])
      if (!open) setUnread(u => u + 1)
    } catch (err) {
      const status = err?.response?.status
      const detail = err?.response?.data?.detail

      let errorMsg = "Sorry, I'm having trouble connecting. Please try again."
      if (status === 429 || detail === 'rate_limit') {
        errorMsg = "⏳ Too many requests right now (free tier limit). Please wait **20–30 seconds** and try again."
      } else if (status === 503 || detail === 'unavailable') {
        errorMsg = "MediBot is temporarily unavailable. Please check the backend is running and your Gemini API key is set in `.env`."
      }

      setMessages(prev => [...prev, { role: 'assistant', content: errorMsg }])
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <>
      {!open && (
        <button onClick={() => setOpen(true)} style={{
          position: 'fixed', bottom: 28, right: 28, zIndex: 1000,
          width: 56, height: 56, borderRadius: '50%',
          background: 'linear-gradient(135deg, #0db4d6, #0891b2)',
          border: 'none', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 24px #0db4d650', transition: 'transform 0.2s',
        }}
          onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.08)'}
          onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
        >
          <MessageCircle size={24} color="#03080d" fill="#03080d" />
          {unread > 0 && (
            <div style={{
              position: 'absolute', top: -4, right: -4,
              background: 'var(--red)', color: '#fff', borderRadius: '50%',
              width: 20, height: 20, fontSize: '0.7rem', fontWeight: 700,
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>{unread}</div>
          )}
        </button>
      )}

      {open && (
        <div style={{
          position: 'fixed', bottom: 28, right: 28, zIndex: 1000,
          width: 380, borderRadius: 16,
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          boxShadow: '0 8px 48px #000c',
          display: 'flex', flexDirection: 'column',
          height: minimized ? 'auto' : 560,
          overflow: 'hidden',
          animation: 'chatSlideUp 0.25s cubic-bezier(.4,0,.2,1)',
        }}>

          {/* Header */}
          <div style={{
            padding: '14px 16px',
            background: 'linear-gradient(135deg, #0d2035, #0a1825)',
            borderBottom: '1px solid var(--border)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            flexShrink: 0,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 34, height: 34, borderRadius: '50%',
                background: 'var(--teal-dim)', border: '1px solid var(--teal)',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                <Bot size={18} color="var(--teal)" />
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>MediBot</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--green)', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ width: 6, height: 6, background: 'var(--green)', borderRadius: '50%', display: 'inline-block' }} />
                  AI Medical Assistant
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 4 }}>
              <button onClick={() => setMinimized(m => !m)} style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--text-mid)', padding: 4, borderRadius: 6,
                display: 'flex', alignItems: 'center'
              }}><Minimize2 size={15} /></button>
              <button onClick={() => setOpen(false)} style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--text-mid)', padding: 4, borderRadius: 6,
                display: 'flex', alignItems: 'center'
              }}><X size={15} /></button>
            </div>
          </div>

          {!minimized && (
            <>
              {/* Messages */}
              <div style={{
                flex: 1, overflowY: 'auto', padding: '16px 14px',
                display: 'flex', flexDirection: 'column', gap: 12,
              }}>
                {messages.map((msg, i) => (
                  <div key={i} style={{
                    display: 'flex', gap: 8,
                    flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                    alignItems: 'flex-start',
                  }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                      background: msg.role === 'user' ? 'var(--teal-mid)' : '#0d2035',
                      border: `1px solid ${msg.role === 'user' ? 'var(--teal)' : 'var(--border)'}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      {msg.role === 'user'
                        ? <User size={14} color="var(--teal)" />
                        : <Bot size={14} color="var(--teal)" />}
                    </div>
                    <div style={{
                      maxWidth: '80%', padding: '10px 13px', borderRadius: 12,
                      background: msg.role === 'user' ? 'var(--teal)' : 'var(--bg-elevated)',
                      color: msg.role === 'user' ? '#03080d' : 'var(--text)',
                      border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
                      borderTopRightRadius: msg.role === 'user' ? 4 : 12,
                      borderTopLeftRadius: msg.role === 'assistant' ? 4 : 12,
                    }}>
                      <MessageText text={msg.content} />
                    </div>
                  </div>
                ))}

                {loading && (
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%',
                      background: '#0d2035', border: '1px solid var(--border)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                    }}>
                      <Bot size={14} color="var(--teal)" />
                    </div>
                    <div style={{
                      padding: '12px 16px', background: 'var(--bg-elevated)',
                      border: '1px solid var(--border)', borderRadius: 12, borderTopLeftRadius: 4,
                      display: 'flex', gap: 5, alignItems: 'center',
                    }}>
                      {[0, 0.2, 0.4].map((delay, i) => (
                        <span key={i} style={{
                          width: 7, height: 7, borderRadius: '50%', background: 'var(--teal)',
                          animation: `typingDot 1.2s ${delay}s ease-in-out infinite`,
                          display: 'inline-block',
                        }} />
                      ))}
                    </div>
                  </div>
                )}

                {messages.length === 1 && !loading && (
                  <div style={{ marginTop: 4 }}>
                    <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Suggested questions
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {SUGGESTED.map((q, i) => (
                        <button key={i} onClick={() => send(q)} style={{
                          background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                          borderRadius: 8, padding: '8px 12px', cursor: 'pointer',
                          color: 'var(--text-mid)', fontSize: '0.78rem', textAlign: 'left',
                          fontFamily: 'var(--font-sans)', transition: 'all 0.15s',
                        }}
                          onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--teal)'; e.currentTarget.style.color = 'var(--teal)' }}
                          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-mid)' }}
                        >{q}</button>
                      ))}
                    </div>
                  </div>
                )}

                <div ref={bottomRef} />
              </div>

              {/* Disclaimer */}
              <div style={{
                padding: '6px 14px', background: '#f5a62308',
                borderTop: '1px solid #f5a62320',
                display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0,
              }}>
                <AlertCircle size={11} color="var(--amber)" style={{ flexShrink: 0 }} />
                <span style={{ fontSize: '0.68rem', color: 'var(--amber)', opacity: 0.8 }}>
                  Not a substitute for professional medical advice
                </span>
              </div>

              {/* Input */}
              <div style={{
                padding: '12px 14px', borderTop: '1px solid var(--border)',
                display: 'flex', gap: 8, alignItems: 'flex-end', flexShrink: 0,
                background: 'var(--bg-card)',
              }}>
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKey}
                  placeholder="Ask a health question..."
                  rows={1}
                  style={{
                    flex: 1, resize: 'none', background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)', borderRadius: 10,
                    padding: '9px 12px', color: 'var(--text)',
                    fontFamily: 'var(--font-sans)', fontSize: '0.85rem',
                    outline: 'none', lineHeight: 1.5, maxHeight: 100,
                    transition: 'border-color 0.15s',
                  }}
                  onFocus={e => e.target.style.borderColor = 'var(--teal)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border)'}
                />
                <button onClick={() => send()} disabled={!input.trim() || loading} style={{
                  width: 36, height: 36, borderRadius: 10, flexShrink: 0,
                  background: input.trim() && !loading ? 'var(--teal)' : 'var(--bg-elevated)',
                  border: `1px solid ${input.trim() && !loading ? 'var(--teal)' : 'var(--border)'}`,
                  cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all 0.15s',
                }}>
                  <Send size={15} color={input.trim() && !loading ? '#03080d' : 'var(--text-dim)'} />
                </button>
              </div>
            </>
          )}
        </div>
      )}

      <style>{`
        @keyframes chatSlideUp {
          from { opacity: 0; transform: translateY(20px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes typingDot {
          0%, 100% { transform: translateY(0); opacity: 0.4; }
          50%       { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </>
  )
}
