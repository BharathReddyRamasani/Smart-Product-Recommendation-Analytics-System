import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Loader2, Bot, User } from 'lucide-react'
import { sendChatMessage } from '../services/api'
import { Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function ChatAssistant() {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState([
    { 
        role: 'assistant', 
        text: "Hi! I'm your AI Shopping Assistant. Looking for a gaming laptop, some new books, or anything else? Just ask!",
        isWelcome: true
    }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(() => Math.random().toString(36).substring(7))
  const messagesEndRef = useRef(null)

  const SUGGESTIONS = [
    "Show me some wireless noise-canceling headphones that are under $200.",
    "I'm looking for a laptop good for gaming with 16GB RAM.",
    "Based on my browsing, what do you recommend?"
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (text) => {
    if (!text.trim() || isLoading) return

    const userMessage = { role: 'user', text }
    setMessages((prev) => [...prev, userMessage])
    setQuery('')
    setIsLoading(true)

    try {
      const data = await sendChatMessage(userMessage.text, sessionId)
      
      const assistantMessage = {
        role: 'assistant',
        text: data.answer,
        products: data.recommended_products
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', text: "Oops, I encountered an error connecting to my brain. Please check your API keys and try again later." }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    sendMessage(query)
  }

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 p-4 bg-brand-600 text-white rounded-full shadow-lg hover:bg-brand-500 transition-all z-50 flex items-center justify-center focus:outline-none focus:ring-4 focus:ring-brand-500/50"
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 max-w-[calc(100vw-3rem)] h-[600px] max-h-[80vh] bg-slate-900 border border-white/10 rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden flex flex-col backdrop-blur-xl bg-opacity-95">
          
          {/* Header */}
          <div className="p-4 bg-brand-600 border-b border-white/10 flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-full">
              <Bot size={20} className="text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-white">AI Shopping Assistant</h3>
              <p className="text-xs text-white/70">Powered by RAG & Gemini</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`p-2 rounded-full h-8 w-8 flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-brand-600' : 'bg-slate-800 border border-white/10 text-brand-400'}`}>
                  {msg.role === 'user' ? <User size={16} className="text-white" /> : <Bot size={16} />}
                </div>
                <div className={`flex flex-col gap-2 max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`p-3 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-brand-600 text-white rounded-tr-none shadow-md' : 'bg-slate-800 text-gray-200 border border-white/10 rounded-tl-none shadow-sm'}`}>
                    {msg.role === 'user' ? (
                      msg.text
                    ) : (
                      <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-slate-900 prose-a:text-brand-400 hover:prose-a:text-brand-300 prose-ul:my-1 prose-li:my-0 prose-strong:text-white">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.text}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>

                  {/* Suggestion Chips */}
                  {msg.isWelcome && messages.length === 1 && (
                    <div className="flex flex-col gap-2 mt-2 w-full pr-4">
                      <span className="text-xs text-brand-400 font-medium px-1">Try asking:</span>
                      {SUGGESTIONS.map((sug, i) => (
                        <button
                          key={i}
                          onClick={() => sendMessage(sug)}
                          disabled={isLoading}
                          className="text-left text-xs bg-brand-600/10 border border-brand-500/20 hover:bg-brand-600/20 hover:border-brand-500/50 text-brand-100 p-2.5 rounded-xl transition-all w-full"
                        >
                          {sug}
                        </button>
                      ))}
                    </div>
                  )}
                  
                  {/* Recommended Products */}
                  {msg.products && msg.products.length > 0 && (
                    <div className="flex gap-2 overflow-x-auto w-full pb-2 snap-x">
                      {msg.products.map(p => (
                        <Link 
                          to={`/products/${p.mongo_id}`} 
                          key={p.mongo_id}
                          className="flex-shrink-0 w-40 bg-slate-800 border border-white/10 rounded-xl p-3 snap-start hover:border-brand-500/50 hover:bg-slate-700 transition-all shadow-sm group"
                        >
                          <div className="text-xs font-semibold text-gray-200 truncate group-hover:text-brand-400">{p.name}</div>
                          <div className="text-xs text-brand-400 mt-1">${p.price}</div>
                          <div className="text-[10px] text-gray-500 mt-1 uppercase tracking-wider">{p.category}</div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-3">
                <div className="p-2 rounded-full h-8 w-8 flex items-center justify-center shrink-0 bg-slate-800 border border-white/10 text-brand-400">
                  <Bot size={16} />
                </div>
                <div className="p-3 rounded-2xl text-sm bg-slate-800 text-gray-200 border border-white/10 rounded-tl-none flex items-center gap-3 shadow-sm">
                  <Loader2 size={16} className="animate-spin text-brand-400" />
                  Thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <form onSubmit={handleSend} className="p-4 border-t border-white/10 bg-slate-900 flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask for a recommendation..."
              className="flex-1 bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50 placeholder-gray-400 shadow-inner"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="p-2 bg-brand-600 text-white rounded-xl hover:bg-brand-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      )}
    </>
  )
}
