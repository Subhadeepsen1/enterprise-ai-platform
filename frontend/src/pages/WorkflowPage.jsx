import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, XCircle, Clock, AlertTriangle, Shield, ArrowRight } from 'lucide-react'
import { listWorkflows, updateWorkflow } from '../services/api'
import { useAuthStore } from '../store/authStore'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const STATUS_COLORS = { pending: 'badge-gray', in_review: 'badge-blue', approved: 'badge-green', rejected: 'badge-red', escalated: 'badge-amber', on_hold: 'badge-amber' }

export default function WorkflowPage() {
  const [workflows, setWorkflows] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const canApprove = user?.role === 'admin' || user?.role === 'manager'

  const loadData = () => {
    setLoading(true)
    listWorkflows({ status: filter || undefined })
      .then(r => setWorkflows(r.data.items))
      .catch(() => toast.error('Failed to load workflows'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadData() }, [filter])

  const handleAction = async (id, status, e) => {
    e.stopPropagation()
    try {
      await updateWorkflow(id, { status, notes: `Quick ${status} from dashboard` })
      toast.success(`Workflow ${status}`)
      loadData()
    } catch { toast.error('Action failed') }
  }

  return (
    <div className="fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1>Workflow Automation</h1>
          <p>Manage document approvals and AI recommendations</p>
        </div>
        <select className="form-select" style={{ width: 160 }} value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="in_review">In Review</option>
          <option value="escalated">Escalated</option>
          <option value="approved">Approved</option>
        </select>
      </div>

      <div className="grid-3">
        {loading ? (
          <div style={{ gridColumn: '1 / -1', padding: 60, textAlign: 'center' }}><div className="spinner" style={{ margin: '0 auto' }} /></div>
        ) : workflows.length === 0 ? (
          <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
            <div className="empty-icon">⚡</div>
            <p>No workflows found.</p>
          </div>
        ) : workflows.map(wf => (
          <div key={wf.id} className="workflow-card cursor-pointer" onClick={() => navigate(`/documents/${wf.document_id}`)} style={{ cursor: 'pointer' }}>
            <div className="workflow-header">
              <div>
                <div className="workflow-title flex items-center gap-2">
                  Workflow #{wf.id}
                </div>
                <div className="workflow-meta">{format(new Date(wf.created_at), 'MMM d, yyyy HH:mm')}</div>
              </div>
              <span className={`badge ${STATUS_COLORS[wf.status] || 'badge-gray'}`}>{wf.status.replace('_', ' ')}</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
              <div className="flex justify-between items-center" style={{ fontSize: 12 }}>
                <span className="text-muted">AI Recommendation</span>
                <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{wf.ai_recommendation?.replace('_', ' ')}</span>
              </div>
              <div className="flex justify-between items-center" style={{ fontSize: 12 }}>
                <span className="text-muted">Risk Score</span>
                <span style={{ fontWeight: 600, color: wf.risk_score > 60 ? 'var(--danger)' : 'var(--warning)' }}>{wf.risk_score?.toFixed(0)}/100</span>
              </div>
              <div className="flex justify-between items-center" style={{ fontSize: 12 }}>
                <span className="text-muted">Confidence</span>
                <span style={{ fontWeight: 600 }}>{wf.confidence ? `${(wf.confidence * 100).toFixed(0)}%` : '—'}</span>
              </div>
            </div>

            {wf.missing_fields?.length > 0 && (
              <div className="mb-4">
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Missing Fields</div>
                <div className="flex gap-1 flex-wrap">
                  {wf.missing_fields.map((f, i) => <span key={i} className="badge badge-amber">{f}</span>)}
                </div>
              </div>
            )}

            <div className="divider" style={{ margin: '12px 0' }} />

            <div className="flex justify-between items-center">
              <span style={{ fontSize: 12, color: 'var(--accent-light)' }} className="flex items-center gap-1">
                View Details <ArrowRight size={12} />
              </span>
              {canApprove && !['approved', 'rejected'].includes(wf.status) && (
                <div className="flex gap-2">
                  <button className="btn-icon" style={{ color: 'var(--success)' }} onClick={e => handleAction(wf.id, 'approved', e)} title="Approve"><CheckCircle size={14} /></button>
                  <button className="btn-icon" style={{ color: 'var(--danger)' }} onClick={e => handleAction(wf.id, 'rejected', e)} title="Reject"><XCircle size={14} /></button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
