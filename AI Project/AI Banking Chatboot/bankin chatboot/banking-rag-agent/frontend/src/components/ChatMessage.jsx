import { Copy, RefreshCw, ThumbsDown, ThumbsUp } from 'lucide-react';
import { useState } from 'react';
import { feedbackAPI } from '../services/api';

export default function ChatMessage({ message, onRegenerate }) {
  const [feedback, setFeedback] = useState(message.feedback);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = async (rating) => {
    if (feedback || !message.id) return;
    try {
      await feedbackAPI.submit({ message_id: message.id, rating });
      setFeedback(rating);
    } catch {
      /* ignore */
    }
  };

  const formatSource = (src) => {
    let label = src.filename || 'Document';
    if (src.section) label += ` — ${src.section}`;
    if (src.page) label += ` — Page ${src.page}`;
    return label;
  };

  return (
    <div className={`message ${message.role}`}>
      <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>

      {message.role === 'assistant' && message.sources?.length > 0 && (
        <div className="sources">
          <div className="sources-label">Sources</div>
          {message.sources.map((src, i) => (
            <span key={i} className="source-tag">{formatSource(src)}</span>
          ))}
        </div>
      )}

      {message.role === 'assistant' && (
        <div className="message-actions">
          <button className="msg-action-btn" onClick={handleCopy}>
            <Copy size={14} /> {copied ? 'Copied!' : 'Copy'}
          </button>
          {onRegenerate && (
            <button className="msg-action-btn" onClick={onRegenerate}>
              <RefreshCw size={14} /> Regenerate
            </button>
          )}
          <button
            className={`msg-action-btn ${feedback === 'up' ? 'active-up' : ''}`}
            onClick={() => handleFeedback('up')}
          >
            <ThumbsUp size={14} />
          </button>
          <button
            className={`msg-action-btn ${feedback === 'down' ? 'active-down' : ''}`}
            onClick={() => handleFeedback('down')}
          >
            <ThumbsDown size={14} />
          </button>
        </div>
      )}
    </div>
  );
}
