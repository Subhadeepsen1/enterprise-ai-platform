import { useEffect, useState } from 'react'
import { listUsers } from '../services/api'
import { Users, Shield, CheckCircle, XCircle } from 'lucide-react'
import { format } from 'date-fns'

export default function UsersPage() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listUsers()
      .then(r => setUsers(r.data.users))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>User Management</h1>
        <p>Admin panel for managing platform access and roles</p>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <div className="table-container" style={{ border: 'none' }}>
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Department</th>
                <th>Status</th>
                <th>Registered</th>
                <th>Last Login</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></td></tr>
              ) : users.map(u => (
                <tr key={u.id}>
                  <td>
                    <div className="flex items-center gap-3">
                      <div className="user-avatar">{u.full_name[0]}</div>
                      <div>
                        <div style={{ fontWeight: 600 }}>{u.full_name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{u.email}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`badge badge-${u.role === 'admin' ? 'purple' : u.role === 'manager' ? 'blue' : 'gray'}`}>
                      {u.role === 'admin' && <Shield size={10} />} {u.role}
                    </span>
                  </td>
                  <td>{u.department || '—'}</td>
                  <td>
                    <div className="flex items-center gap-1" style={{ color: u.is_active ? 'var(--success)' : 'var(--danger)', fontSize: 12 }}>
                      {u.is_active ? <CheckCircle size={14} /> : <XCircle size={14} />}
                      {u.is_active ? 'Active' : 'Inactive'}
                    </div>
                  </td>
                  <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{format(new Date(u.created_at), 'MMM d, yyyy')}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{u.last_login ? format(new Date(u.last_login), 'MMM d, yyyy HH:mm') : 'Never'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
