import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload } from 'lucide-react';
import { adminAPI, documentsAPI, ticketsAPI } from '../services/api';

const CATEGORIES = [
  'General FAQ', 'Account', 'KYC', 'Loan', 'Credit Card', 'Debit Card',
  'Banking Charges', 'Fund Transfer', 'Interest Rates', 'Complaints', 'Other',
];

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadCategory, setUploadCategory] = useState('Other');
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [analyticsRes, docsRes, ticketsRes] = await Promise.all([
        adminAPI.analytics(),
        documentsAPI.list(),
        ticketsAPI.list(),
      ]);
      setAnalytics(analyticsRes.data);
      setDocuments(docsRes.data);
      setTickets(ticketsRes.data);
    } catch {
      setMessage('Failed to load admin data');
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;
    setUploading(true);
    setMessage('');
    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('category', uploadCategory);
    try {
      const { data } = await documentsAPI.upload(formData);
      setMessage(`Uploaded: ${data.filename} (${data.chunk_count} chunks indexed)`);
      setUploadFile(null);
      loadData();
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this document from the knowledge base?')) return;
    try {
      await documentsAPI.delete(id);
      setMessage('Document deleted');
      loadData();
    } catch {
      setMessage('Delete failed');
    }
  };

  const handleReindex = async (id) => {
    try {
      const { data } = await documentsAPI.reindex(id);
      setMessage(`Re-indexed: ${data.filename}`);
      loadData();
    } catch {
      setMessage('Re-index failed');
    }
  };

  return (
    <div className="layout">
      <div className="admin-page" style={{ width: '100%' }}>
        <div className="admin-header">
          <button className="btn-secondary" onClick={() => navigate('/')} style={{ marginBottom: 12 }}>
            <ArrowLeft size={14} /> Back to Chat
          </button>
          <h1>Admin Dashboard</h1>
        </div>

        {message && (
          <div style={{ padding: '10px 14px', background: '#f0f9ff', borderRadius: 8, marginBottom: 16, fontSize: 14 }}>
            {message}
          </div>
        )}

        {analytics && (
          <div className="stats-grid">
            <div className="stat-card"><div className="stat-value">{analytics.total_users}</div><div className="stat-label">Users</div></div>
            <div className="stat-card"><div className="stat-value">{analytics.total_sessions}</div><div className="stat-label">Chat Sessions</div></div>
            <div className="stat-card"><div className="stat-value">{analytics.total_messages}</div><div className="stat-label">Messages</div></div>
            <div className="stat-card"><div className="stat-value">{analytics.total_documents}</div><div className="stat-label">Documents</div></div>
            <div className="stat-card"><div className="stat-value">{analytics.open_tickets}</div><div className="stat-label">Open Tickets</div></div>
            <div className="stat-card"><div className="stat-value">{analytics.feedback_positive}</div><div className="stat-label">Positive Feedback</div></div>
          </div>
        )}

        <div className="admin-section">
          <h2>Upload Document</h2>
          <div className="upload-area" onClick={() => document.getElementById('file-input').click()}>
            <Upload size={32} style={{ color: '#64748b', marginBottom: 8 }} />
            <p>{uploadFile ? uploadFile.name : 'Click to select PDF or TXT file'}</p>
            <input
              id="file-input"
              type="file"
              accept=".pdf,.txt"
              style={{ display: 'none' }}
              onChange={(e) => setUploadFile(e.target.files[0])}
            />
          </div>
          <div style={{ display: 'flex', gap: 12, marginTop: 16, alignItems: 'center' }}>
            <select value={uploadCategory} onChange={(e) => setUploadCategory(e.target.value)}>
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <button className="btn-primary" onClick={handleUpload} disabled={!uploadFile || uploading} style={{ padding: '10px 24px' }}>
              {uploading ? 'Uploading...' : 'Upload & Index'}
            </button>
          </div>
        </div>

        <div className="admin-section">
          <h2>Documents ({documents.length})</h2>
          <table className="data-table">
            <thead>
              <tr><th>Filename</th><th>Category</th><th>Chunks</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td>{doc.filename}</td>
                  <td>{doc.category}</td>
                  <td>{doc.chunk_count}</td>
                  <td><span className={`status-badge status-${doc.status}`}>{doc.status}</span></td>
                  <td>
                    <button className="btn-secondary" onClick={() => handleReindex(doc.id)} style={{ marginRight: 8 }}>Re-index</button>
                    <button className="btn-danger" onClick={() => handleDelete(doc.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="admin-section">
          <h2>Support Tickets ({tickets.length})</h2>
          <table className="data-table">
            <thead>
              <tr><th>Ticket ID</th><th>Issue</th><th>Status</th><th>Created</th></tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.ticket_id}>
                  <td>{t.ticket_id}</td>
                  <td>{t.issue.substring(0, 80)}...</td>
                  <td><span className={`status-badge status-${t.status}`}>{t.status}</span></td>
                  <td>{new Date(t.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {analytics?.frequent_questions?.length > 0 && (
          <div className="admin-section">
            <h2>Frequently Asked Questions</h2>
            <table className="data-table">
              <thead><tr><th>Question</th><th>Count</th></tr></thead>
              <tbody>
                {analytics.frequent_questions.map((q, i) => (
                  <tr key={i}><td>{q.question}</td><td>{q.count}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
