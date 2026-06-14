import { useState } from 'react'
import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [form, setForm] = useState({ username: '', password: '' })
  const { login, loading, error } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    const ok = await login(form.username, form.password)
    if (ok) {
      toast.success('Welcome back!')
      navigate('/dashboard')
    } else {
      toast.error(error || 'Login failed')
    }
  }

  const fillDemo = (role) => {
    const creds = {
      admin: { username: 'admin', password: 'Admin123!' },
      manager: { username: 'manager', password: 'Manager123!' },
      employee: { username: 'employee', password: 'Employee123!' },
    }
    setForm(creds[role])
  }

  return (
    <div className="login-page">
      <div className="login-card fade-in">
        <div className="login-logo">
          <div className="logo-big">🧠</div>
          <h1>Enterprise AI Platform</h1>
          <p>Workflow Intelligence & Document Processing</p>
        </div>

        {/* Demo credentials */}
        <div style={{ marginBottom: 20, padding: '12px 14px', background: 'rgba(59,130,246,0.08)', borderRadius: 8, border: '1px solid rgba(59,130,246,0.15)' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Quick Demo Access</div>
          <div style={{ display: 'flex', gap: 6 }}>
            {['admin', 'manager', 'employee'].map(role => (
              <button key={role} onClick={() => fillDemo(role)} className="btn btn-sm btn-secondary" id={`demo-${role}`}
                style={{ flex: 1, fontSize: 11, textTransform: 'capitalize' }}>
                {role}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input id="input-username" className="form-input" placeholder="Enter username" value={form.username}
              onChange={e => setForm(p => ({ ...p, username: e.target.value }))} required />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input id="input-password" type="password" className="form-input" placeholder="Enter password" value={form.password}
              onChange={e => setForm(p => ({ ...p, password: e.target.value }))} required />
          </div>
          <button id="btn-login" className="btn btn-primary w-full" type="submit" disabled={loading}
            style={{ marginTop: 8, justifyContent: 'center', padding: '12px' }}>
            {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Signing in...</> : '→  Sign In'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 24, fontSize: 12, color: 'var(--text-muted)' }}>
          Secured with JWT · Role-based access control
        </p>
      </div>
    </div>
  )
}
