import { useEffect, useState, useRef } from 'react'
import toast from 'react-hot-toast'
import { Send, Plus, MessageSquare, Bot, User, BookOpen } from 'lucide-react'
import { createChatSession, listChatSessions, sendMessage, getMessages } from '../services/api'

export default function ChatPage() {
  const [sessions, setSessions] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    listChatSessions().then(r => setSessions(r.data.sessions)).catch(console.error)
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const selectSession = async (session) => {
    setActiveSession(session)
    try {
      const { data } = await getMessages(session.id)
      setMessages(data.messages)
    } catch { toast.error('Failed to load messages') }
  }

  const newSession = async () => {
    try {
      const { data } = await createChatSession('New Conversation')
      setSessions(p => [data, ...p])
      setActiveSession(data)
      setMessages([])
    } catch { toast.error('Failed to create session') }
  }

  const handleSend = async () => {
    if (!input.trim() || !activeSession || sending) return
    const text = input.trim()
    setInput('')
    setMessages(p => [...p, { id: Date.now(), role: 'user', content: text }])
    setSending(true)
    try {
      const { data } = await sendMessage(activeSession.id, { message: text })
      setMessages(p => [...p, {
        id: data.message_id, role: 'assistant',
        content: data.answer, sources: data.sources
      }])
    } catch { toast.error('Failed to send message') }
    finally { setSending(false) }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 64px)', margin: '-28px -32px', overflow: 'hidden' }}>
      {/* Sessions sidebar */}
      <div className="chat-sidebar">
        <button id="btn-new-chat" className="btn btn-primary w-full" style={{ justifyContent: 'center', marginBottom: 12 }}
          onClick={newSession}>
          <Plus size={15} /> New Chat
        </button>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', padding: '4px 0 8px', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Conversations</div>
        {sessions.map(s => (
          <button key={s.id} className={`nav-item ${activeSession?.id === s.id ? 'active' : ''}`}
            onClick={() => selectSession(s)} style={{ width: '100%' }}>
            <MessageSquare size={14} />
            <span className="truncate">{s.title || 'New Chat'}</span>
          </button>
        ))}
        {sessions.length === 0 && (
          <div style={{ textAlign: 'center', padding: '30px 10px', color: 'var(--text-muted)', fontSize: 12 }}>
            <Bot size={32} style={{ margin: '0 auto 8px', display: 'block', opacity: 0.4 }} />
            No conversations yet
          </div>
        )}
      </div>

      {/* Chat main */}
      <div className="chat-main">
        {!activeSession ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16, color: 'var(--text-muted)' }}>
            <div style={{ width: 80, height: 80, borderRadius: 20, background: 'linear-gradient(135deg, var(--accent), var(--accent2))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 40 }}>🤖</div>
            <h2 style={{ fontSize: '1.3rem', color: 'var(--text-primary)' }}>Enterprise RAG Assistant</h2>
            <p style={{ textAlign: 'center', maxWidth: 400 }}>Ask questions about your uploaded documents. The AI retrieves context and provides cited answers.</p>
            <button className="btn btn-primary" onClick={newSession}><Plus size={15} /> Start New Conversation</button>
          </div>
        ) : (
          <>
            <div className="chat-messages" style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                  <Bot size={40} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.4 }} />
                  <p>Ask anything about your company documents...</p>
                  <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 16, flexWrap: 'wrap' }}>
                    {['What are the payment terms?', 'Summarize contract risks', 'List all vendor names'].map(q => (
                      <button key={q} className="btn btn-secondary btn-sm" onClick={() => setInput(q)}>{q}</button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map(msg => (
                <div key={msg.id} className={`message ${msg.role} fade-in`}>
                  <div className={`message-avatar ${msg.role === 'assistant' ? 'msg-ai-avatar' : 'msg-user-avatar'}`}>
                    {msg.role === 'assistant' ? '🤖' : '👤'}
                  </div>
                  <div>
                    <div className="message-bubble" style={{ whiteSpace: 'pre-wrap', fontSize: 14 }}>{msg.content}</div>
                    {msg.sources?.length > 0 && (
                      <div className="message-sources">
                        <BookOpen size={12} style={{ color: 'var(--text-muted)', marginTop: 2 }} />
                        {msg.sources.map((s, i) => (
                          <span key={i} className="source-chip" title={`Relevance: ${(s.relevance * 100).toFixed(0)}%`}>
                            📄 {s.filename}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {sending && (
                <div className="message assistant">
                  <div className="message-avatar msg-ai-avatar">🤖</div>
                  <div className="message-bubble" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <div className="spinner" style={{ width: 14, height: 14 }} />
                    <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>Retrieving context & generating answer...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            <div className="chat-input-bar">
              <textarea id="chat-input" className="chat-input" rows={1} placeholder="Ask about your documents... (Enter to send, Shift+Enter for newline)"
                value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown} />
              <button id="btn-send-message" className="btn btn-primary" onClick={handleSend} disabled={!input.trim() || sending}>
                <Send size={15} />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
