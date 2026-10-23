import { useEffect, useRef, useState } from 'react';
import { Send } from 'lucide-react';
import ChatMessage from './ChatMessage';
import { chatAPI } from '../services/api';

const SUGGESTIONS = [
  'What documents are required for a personal loan?',
  'What is the minimum balance for savings account?',
  'How do I block my debit card?',
  'What are the NEFT charges?',
  'Show my recent transactions',
  'What is my account balance?',
];

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [lastUserMessage, setLastUserMessage] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const loadSessions = async () => {
    try {
      const { data } = await chatAPI.history();
      setSessions(data);
    } catch {
      /* ignore */
    }
  };

  const loadSession = async (id) => {
    try {
      const { data } = await chatAPI.messages(id);
      setMessages(data);
      setSessionId(id);
    } catch {
      /* ignore */
    }
  };

  const sendMessage = async (text, regenerate = false) => {
    const msg = text || input;
    if (!msg.trim() || loading) return;

    if (!regenerate) {
      setMessages((prev) => [...prev, { role: 'user', content: msg.trim() }]);
      setLastUserMessage(msg.trim());
    }
    setInput('');
    setLoading(true);

    try {
      const { data } = await chatAPI.send(msg.trim(), sessionId);
      setSessionId(data.session_id);

      const assistantMsg = {
        id: data.message_id,
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
      };

      if (regenerate) {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = assistantMsg;
          return updated;
        });
      } else {
        setMessages((prev) => [...prev, assistantMsg]);
      }
      loadSessions();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: err.response?.data?.detail || 'Sorry, something went wrong. Please try again.',
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const newChat = () => {
    setMessages([]);
    setSessionId(null);
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-sidebar">
        <div className="chat-sidebar-header">
          <button className="btn-new-chat" onClick={newChat}>+ New Conversation</button>
        </div>
        <div className="session-list">
          {sessions.map((s) => (
            <button
              key={s.id}
              className={`session-item ${sessionId === s.id ? 'active' : ''}`}
              onClick={() => loadSession(s.id)}
            >
              <span>{s.title}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="chat-main">
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-welcome">
              <h2>Welcome to DemoBank AI Support</h2>
              <p>Ask me anything about banking policies, accounts, loans, cards, and more.</p>
              <div className="suggestion-chips">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="chip" onClick={() => sendMessage(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <ChatMessage
              key={i}
              message={msg}
              onRegenerate={
                msg.role === 'assistant' && i === messages.length - 1
                  ? () => sendMessage(lastUserMessage, true)
                  : null
              }
            />
          ))}

          {loading && (
            <div className="typing-indicator">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <form className="chat-input-form" onSubmit={(e) => { e.preventDefault(); sendMessage(); }}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about banking policies, your account, loans..."
              rows={1}
              disabled={loading}
            />
            <button type="submit" className="btn-send" disabled={loading || !input.trim()}>
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
