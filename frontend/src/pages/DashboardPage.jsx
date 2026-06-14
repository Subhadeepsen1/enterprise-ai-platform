import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { FileText, GitBranch, AlertTriangle, CheckCircle, TrendingUp, Clock, Zap, Shield } from 'lucide-react'
import { getAnalyticsOverview, getAnalyticsTrends, getRecentActivity } from '../services/api'
import { format } from 'date-fns'

const RISK_COLORS = { low: '#10b981', medium: '#f59e0b', high: '#f97316', critical: '#ef4444' }
const DOC_TYPE_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444']

function getRiskBadge(level) {
  const map = { low: 'badge-green', medium: 'badge-amber', high: 'badge-red', critical: 'badge-red' }
  return map[level] || 'badge-gray'
}

export default function DashboardPage() {
  const [overview, setOverview] = useState(null)
  const [trends, setTrends] = useState([])
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([getAnalyticsOverview(), getAnalyticsTrends(), getRecentActivity(8)])
      .then(([ov, tr, rc]) => {
        setOverview(ov.data)
        setTrends(tr.data.trends)
        setRecent(rc.data.recent_documents)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 40, height: 40 }} /></div>

  const s = overview?.summary || {}
  const docTypes = Object.entries(overview?.documents_by_type || {}).map(([name, value]) => ({ name, value }))
  const wfStatuses = overview?.workflows_by_status || {}

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Intelligence Dashboard</h1>
        <p>Real-time overview of document processing, workflow status, and AI insights</p>
      </div>

      {/* KPI Stats */}
      <div className="stats-grid">
        {[
          { label: 'Total Documents', value: s.total_documents || 0, icon: '📄', cls: 'blue', change: '↑ AI Processed' },
          { label: 'Pending Approvals', value: s.pending_approvals || 0, icon: '⏳', cls: 'amber', change: 'Requires attention' },
          { label: 'High Risk Detected', value: s.high_risk_count || 0, icon: '🛡️', cls: 'red', change: 'Risk score ≥ 70' },
          { label: 'Avg AI Confidence', value: `${s.avg_confidence_score || 0}%`, icon: '🎯', cls: 'green', change: 'Across all docs' },
          { label: 'Avg Risk Score', value: `${s.avg_risk_score || 0}/100`, icon: '⚠️', cls: 'purple', change: 'Portfolio risk' },
        ].map((stat, i) => (
          <div key={i} className="stat-card">
            <div className={`stat-icon ${stat.cls}`}>{stat.icon}</div>
            <div className="stat-info">
              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
              <div className="stat-change">{stat.change}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid-2 mb-6">
        {/* Trend Chart */}
        <div className="card">
          <div className="card-header">
            <div className="card-title"><TrendingUp size={14} /> Monthly Processing Trends</div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={trends}>
              <defs>
                <linearGradient id="grad1" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" stroke="var(--text-muted)" fontSize={11} />
              <YAxis stroke="var(--text-muted)" fontSize={11} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }} />
              <Area type="monotone" dataKey="document_count" stroke="#3b82f6" fill="url(#grad1)" strokeWidth={2} name="Documents" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Document Type Pie */}
        <div className="card">
          <div className="card-header">
            <div className="card-title"><FileText size={14} /> Document Distribution</div>
          </div>
          {docTypes.length > 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
              <PieChart width={160} height={160}>
                <Pie data={docTypes} cx={75} cy={75} innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value">
                  {docTypes.map((_, i) => <Cell key={i} fill={DOC_TYPE_COLORS[i % DOC_TYPE_COLORS.length]} />)}
                </Pie>
              </PieChart>
              <div style={{ flex: 1 }}>
                {docTypes.map((t, i) => (
                  <div key={i} className="flex items-center gap-2 mb-4" style={{ fontSize: 12 }}>
                    <span style={{ width: 10, height: 10, borderRadius: 2, background: DOC_TYPE_COLORS[i % DOC_TYPE_COLORS.length], flexShrink: 0 }} />
                    <span style={{ color: 'var(--text-secondary)', flex: 1, textTransform: 'capitalize' }}>{t.name.replace('_', ' ')}</span>
                    <span style={{ fontWeight: 700 }}>{t.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty-state"><div className="empty-icon">📊</div><p>Upload documents to see distribution</p></div>
          )}
        </div>
      </div>

      {/* Workflow Status + Recent Activity */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div className="card-title"><GitBranch size={14} /> Workflow Status</div>
            <button className="btn btn-sm btn-secondary" onClick={() => navigate('/workflow')}>View All</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {Object.entries(wfStatuses).length > 0 ? Object.entries(wfStatuses).map(([status, count]) => (
              <div key={status} className="flex items-center gap-3" style={{ fontSize: 13 }}>
                <span className={`badge badge-${status === 'approved' ? 'green' : status === 'rejected' ? 'red' : status === 'escalated' ? 'red' : 'amber'}`}>{status}</span>
                <div style={{ flex: 1, height: 6, background: 'var(--bg-surface)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ height: '100%', background: 'var(--accent)', borderRadius: 3, width: `${Math.min(100, (count / (s.total_documents || 1)) * 100)}%` }} />
                </div>
                <span style={{ fontWeight: 700, minWidth: 24, textAlign: 'right' }}>{count}</span>
              </div>
            )) : <div className="empty-state" style={{ padding: 30 }}><p>No workflows yet</p></div>}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="card-header">
            <div className="card-title"><Clock size={14} /> Recent Documents</div>
            <button className="btn btn-sm btn-secondary" onClick={() => navigate('/documents')}>View All</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {recent.slice(0, 5).map(doc => (
              <div key={doc.id} className="flex items-center gap-10 cursor-pointer" style={{ padding: '8px 10px', borderRadius: 8, background: 'var(--bg-surface)', cursor: 'pointer' }}
                onClick={() => navigate(`/documents/${doc.id}`)}>
                <span style={{ fontSize: 20 }}>
                  {{ invoice: '🧾', contract: '📜', report: '📊', policy: '📋', purchase_order: '🛒' }[doc.document_type] || '📄'}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="truncate" style={{ fontSize: 12, fontWeight: 500 }}>{doc.filename}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{doc.document_type?.replace('_', ' ')}</div>
                </div>
                {doc.risk_level && <span className={`badge ${getRiskBadge(doc.risk_level)}`}>{doc.risk_level}</span>}
              </div>
            ))}
            {recent.length === 0 && <div className="empty-state" style={{ padding: 30 }}><p>No documents yet</p></div>}
          </div>
        </div>
      </div>
    </div>
  )
}
