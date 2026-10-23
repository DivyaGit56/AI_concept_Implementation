import { useNavigate } from 'react-router-dom';
import { LayoutDashboard, LogOut, MessageSquare, Shield } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import ChatInterface from '../components/ChatInterface';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>DemoBank</h2>
          <p>AI Customer Support</p>
        </div>
        <nav className="sidebar-nav">
          <button className="nav-item active">
            <MessageSquare size={18} /> Chat Support
          </button>
          {user?.role === 'admin' && (
            <button className="nav-item" onClick={() => navigate('/admin')}>
              <Shield size={18} /> Admin Dashboard
            </button>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="user-info">{user?.name} ({user?.role})</div>
          <button className="btn-logout" onClick={handleLogout}>
            <LogOut size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
            Sign Out
          </button>
        </div>
      </aside>
      <main className="main-content">
        <ChatInterface />
      </main>
    </div>
  );
}
