import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Shield, FileText, Calendar, DollarSign, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import { getDocument, getWorkflowByDoc, updateWorkflow } from '../services/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

const RISK_BADGE = { low: 'badge-green', medium: 'badge-amber', high: 'badge-red', critical: 'badge-red' }

export default function DocumentDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [doc, setDoc] = useState(null)
  const [workflow, setWorkflow] = useState(null)
  const [loading, setLoading] = useState(true)
  const [approving, setApproving] = useState(false)

  useEffect(() => {
    Promise.all([getDocument(id), getWorkflowByDoc(id).catch(() => null)])
      .then(([d, w]) => { setDoc(d.data); setWorkflow(w?.data || null) })
      .catch(() => toast.error('Failed to load document'))
      .finally(() => setLoading(false))
  }, [id])

  const handleWorkflowAction = async (status, notes = '') => {
    if (!workflow) return
    setApproving(true)
    try {
      const { data } = await updateWorkflow(workflow.id, { status, notes })
      setWorkflow(data)
      toast.success(`Workflow ${status} successfully!`)
    } catch { toast.error('Action failed') }
    finally { setApproving(false) }
  }

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 40, height: 40 }} /></div>
  if (!doc) return <div className="empty-state"><p>Document not found</p></div>

  const e = doc.extracted_entities || {}
  const canApprove = user?.role === 'admin' || user?.role === 'manager'

  return (
    <div className="fade-in">
      <div className="flex items-center gap-3 mb-6">
        <button className="btn-icon" onClick={() => navigate('/documents')}><ArrowLeft size={16} /></button>
        <div>
          <h2 style={{ fontSize: '1.4rem', margin: 0 }}>{doc.original_filename}</h2>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{doc.mime_type} · {(doc.file_size / 1024).toFixed(1)} KB</div>
        </div>
        <div className="flex gap-2" style={{ marginLeft: 'auto' }}>
          <span className="badge badge-blue" style={{ textTransform: 'capitalize' }}>{doc.document_type?.replace('_', ' ')}</span>
          {doc.risk_level && <span className={`badge ${RISK_BADGE[doc.risk_level]}`}>{doc.risk_level} risk</span>}
        </div>
      </div>

      <div className="grid-2 gap-6">
        {/* Left column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* AI Summary */}
          <div className="card">
            <div className="card-header"><div className="card-title">🤖 AI Summary</div></div>
            <p style={{ fontSize: 13, lineHeight: 1.8 }}>{doc.summary || 'Processing...'}</p>
            <div className="divider" />
            <div className="flex gap-4">
              <div><div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Confidence</div><div style={{ fontWeight: 700, color: 'var(--success)' }}>{doc.confidence_score ? `${(doc.confidence_score * 100).toFixed(0)}%` : '—'}</div></div>
              <div><div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Risk Score</div><div style={{ fontWeight: 700, color: doc.risk_score > 60 ? 'var(--danger)' : 'var(--warning)' }}>{doc.risk_score?.toFixed(0) || '—'}/100</div></div>
              <div><div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Indexed</div><div style={{ fontWeight: 700, color: doc.is_indexed ? 'var(--success)' : 'var(--text-muted)' }}>{doc.is_indexed ? '✓ Yes' : '✗ No'}</div></div>
            </div>
          </div>

          {/* Extracted Entities */}
          <div className="card">
            <div className="card-header"><div className="card-title">🧬 Extracted Entities</div></div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { label: 'Invoice #', val: e.invoice_number },
                { label: 'Vendor', val: e.vendor_name },
                { label: 'Total Amount', val: e.total_amount },
                { label: 'Payment Terms', val: e.payment_terms },
                { label: 'Contract Term', val: e.contract_term },
                { label: 'PO Number', val: e.po_number },
              ].filter(f => f.val).map((field, i) => (
                <div key={i} className="flex items-center justify-between" style={{ padding: '8px 12px', background: 'var(--bg-surface)', borderRadius: 8 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{field.label}</span>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{field.val}</span>
                </div>
              ))}
              {e.dates?.length > 0 && (
                <div style={{ padding: '8px 12px', background: 'var(--bg-surface)', borderRadius: 8 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>📅 Dates</div>
                  <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                    {e.dates.map((d, i) => <span key={i} className="badge badge-blue">{d}</span>)}
                  </div>
                </div>
              )}
              {e.amounts?.length > 0 && (
                <div style={{ padding: '8px 12px', background: 'var(--bg-surface)', borderRadius: 8 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>💰 Amounts</div>
                  <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                    {e.amounts.map((a, i) => <span key={i} className="badge badge-green">{a}</span>)}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Risk Analysis */}
          <div className="card">
            <div className="card-header">
              <div className="card-title"><Shield size={14} /> Risk & Compliance</div>
              {doc.risk_level && <span className={`badge ${RISK_BADGE[doc.risk_level]}`}>{doc.risk_level}</span>}
            </div>
            <div className="risk-meter mb-4">
              <div style={{ fontSize: 12, color: 'var(--text-muted)', minWidth: 60 }}>Risk Score</div>
              <div className="risk-bar">
                <div className={`risk-fill risk-${doc.risk_level || 'low'}`} style={{ width: `${doc.risk_score || 0}%` }} />
              </div>
              <span style={{ fontWeight: 700 }}>{doc.risk_score?.toFixed(0) || 0}/100</span>
            </div>
            {doc.risk_factors?.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {doc.risk_factors.map((f, i) => (
                  <div key={i} className={`action-item ${f.severity}`}>
                    <AlertTriangle size={14} style={{ flexShrink: 0, color: f.severity === 'high' ? 'var(--danger)' : 'var(--warning)', marginTop: 1 }} />
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 12 }}>{f.issue}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>→ {f.recommendation}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {(!doc.risk_factors || doc.risk_factors.length === 0) && (
              <div className="flex items-center gap-2" style={{ color: 'var(--success)', fontSize: 13 }}>
                <CheckCircle size={16} /> No risk factors detected
              </div>
            )}
          </div>

          {/* Workflow */}
          {workflow && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">⚡ Workflow Status</div>
                <span className={`badge badge-${workflow.status === 'approved' ? 'green' : workflow.status === 'rejected' ? 'red' : 'amber'}`}>
                  {workflow.status}
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ padding: '12px 14px', background: 'var(--bg-surface)', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>AI Recommendation</div>
                  <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{workflow.ai_recommendation?.replace('_', ' ')}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>{workflow.recommendation_reason}</div>
                </div>
                {workflow.missing_fields?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>Missing Fields</div>
                    <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                      {workflow.missing_fields.map((f, i) => <span key={i} className="badge badge-amber">{f}</span>)}
                    </div>
                  </div>
                )}
                {canApprove && !['approved', 'rejected'].includes(workflow.status) && (
                  <div className="flex gap-2" style={{ marginTop: 8 }}>
                    <button id="btn-approve" className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }}
                      onClick={() => handleWorkflowAction('approved')} disabled={approving}>
                      <CheckCircle size={14} /> Approve
                    </button>
                    <button id="btn-reject" className="btn btn-danger" style={{ flex: 1, justifyContent: 'center' }}
                      onClick={() => handleWorkflowAction('rejected')} disabled={approving}>
                      <XCircle size={14} /> Reject
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
