import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import {
  LayoutDashboard, FileText, GitBranch, MessageSquare,
  BarChart3, Users, LogOut, Zap, Shield, Activity
} from 'lucide-react'

const navItems = [
  { section: 'Main' },
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { section: 'Documents' },
  { path: '/documents', label: 'Documents', icon: FileText },
  { path: '/workflow', label: 'Workflow', icon: GitBranch },
  { section: 'Intelligence' },
  { path: '/chat', label: 'AI Assistant', icon: MessageSquare },
  { section: 'Admin', adminOnly: true },
  { path: '/users', label: 'User Management', icon: Users, adminOnly: true },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">🧠</div>
          <div>
            <div className="logo-text">EnterpriseAI</div>
            <div className="logo-sub">Workflow Intelligence</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item, i) => {
            if (item.section) {
              if (item.adminOnly && user?.role !== 'admin') return null
              return <div key={i} className="sidebar-section-label">{item.section}</div>
            }
            if (item.adminOnly && user?.role !== 'admin') return null
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <button key={item.path} className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => navigate(item.path)} id={`nav-${item.label.replace(/\s+/g, '-').toLowerCase()}`}>
                <Icon className="nav-icon" size={16} />
                {item.label}
              </button>
            )
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="user-card">
            <div className="user-avatar">{user?.full_name?.[0] || user?.username?.[0] || 'U'}</div>
            <div className="user-info">
              <div className="user-name">{user?.full_name || user?.username}</div>
              <div className="user-role">{user?.role}</div>
            </div>
            <button className="logout-btn" onClick={logout} title="Logout" id="btn-logout">
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main area */}
      <div className="main-area">
        <header className="header">
          <div className="flex items-center gap-2">
            <Activity size={16} style={{ color: 'var(--accent-light)' }} />
            <span className="header-title">
              {navItems.find(n => n.path === location.pathname)?.label || 'Platform'}
            </span>
          </div>
          <div className="header-right">
            <span className="header-badge badge-success">
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--success)', display: 'inline-block' }} />
              System Operational
            </span>
            <span className="badge badge-blue">{user?.department || user?.role}</span>
          </div>
        </header>
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
