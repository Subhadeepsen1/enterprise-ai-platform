import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import { Upload, Filter, Search, Trash2, Eye, RefreshCw } from 'lucide-react'
import { listDocuments, uploadDocument, deleteDocument } from '../services/api'
import { format } from 'date-fns'

const DOC_TYPE_EMOJI = { invoice: '🧾', contract: '📜', report: '📊', policy: '📋', purchase_order: '🛒', unknown: '📄' }
const STATUS_BADGE = { processed: 'badge-green', processing: 'badge-blue', uploaded: 'badge-gray', failed: 'badge-red', archived: 'badge-gray' }
const RISK_BADGE = { low: 'badge-green', medium: 'badge-amber', high: 'badge-red', critical: 'badge-red' }

export default function DocumentsPage() {
  const [docs, setDocs] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState('')
  const [page, setPage] = useState(1)
  const navigate = useNavigate()

  const loadDocs = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await listDocuments({ page, page_size: 15, doc_type: filterType || undefined })
      setDocs(data.items)
      setTotal(data.total)
    } catch { toast.error('Failed to load documents') }
    finally { setLoading(false) }
  }, [page, filterType])

  useEffect(() => { loadDocs() }, [loadDocs])

  const onDrop = useCallback(async (files) => {
    if (!files.length) return
    setUploading(true)
    setUploadProgress(0)
    const toastId = toast.loading(`Processing ${files[0].name}...`)
    try {
      await uploadDocument(files[0], setUploadProgress)
      toast.success('Document processed successfully!', { id: toastId })
      loadDocs()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed', { id: toastId })
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }, [loadDocs])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'application/pdf': [], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [], 'text/plain': [] },
    maxFiles: 1, disabled: uploading,
  })

  const handleDelete = async (id, name, e) => {
    e.stopPropagation()
    if (!confirm(`Delete "${name}"?`)) return
    try {
      await deleteDocument(id)
      toast.success('Document deleted')
      loadDocs()
    } catch { toast.error('Delete failed') }
  }

  const filtered = search ? docs.filter(d => d.original_filename.toLowerCase().includes(search.toLowerCase())) : docs

  return (
    <div className="fade-in">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1>Document Processing</h1>
          <p>Upload, classify, and extract insights from business documents using AI</p>
        </div>
        <span className="badge badge-blue">{total} Total Documents</span>
      </div>

      {/* Dropzone */}
      <div {...getRootProps()} className={`dropzone mb-6 ${isDragActive ? 'active' : ''} ${uploading ? 'active' : ''}`}>
        <input {...getInputProps()} id="file-upload-input" />
        <div className="dz-icon">{uploading ? '⚙️' : isDragActive ? '📂' : '📤'}</div>
        {uploading ? (
          <>
            <h3>Processing Document...</h3>
            <p>AI pipeline: Extract → Classify → Analyze → Index</p>
            <div style={{ width: '60%', margin: '16px auto 0', height: 6, background: 'var(--bg-surface)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: `${uploadProgress}%`, height: '100%', background: 'linear-gradient(90deg, var(--accent), var(--accent2))', borderRadius: 3, transition: 'width 0.3s ease' }} />
            </div>
            <p style={{ marginTop: 8 }}>{uploadProgress}%</p>
          </>
        ) : (
          <>
            <h3>Drop document here, or click to upload</h3>
            <p>Supports PDF, DOCX, TXT · Max 50MB · AI-powered processing</p>
          </>
        )}
      </div>

      {/* Pipeline indicator */}
      <div className="pipeline-steps mb-6">
        {['📤 Upload', '📝 Extract Text', '🔍 Classify', '🧬 Extract Entities', '⚠️ Risk Analysis', '🗂️ Vector Index', '⚡ Workflow'].map((s, i) => (
          <div key={i} className="pipeline-step">{s}</div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div style={{ position: 'relative', flex: 1, maxWidth: 300 }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input className="form-input" placeholder="Search documents..." value={search}
            onChange={e => setSearch(e.target.value)} style={{ paddingLeft: 32 }} />
        </div>
        <select className="form-select" style={{ width: 160 }} value={filterType}
          onChange={e => { setFilterType(e.target.value); setPage(1) }}>
          <option value="">All Types</option>
          {['invoice', 'contract', 'report', 'policy', 'purchase_order'].map(t => (
            <option key={t} value={t}>{t.replace('_', ' ')}</option>
          ))}
        </select>
        <button className="btn-icon" onClick={loadDocs} title="Refresh"><RefreshCw size={15} /></button>
      </div>

      {/* Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Document</th><th>Type</th><th>Status</th>
              <th>Risk</th><th>Confidence</th><th>Uploaded</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={7}><div className="empty-state"><div className="empty-icon">📄</div><p>No documents found. Upload one above!</p></div></td></tr>
            ) : filtered.map(doc => (
              <tr key={doc.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/documents/${doc.id}`)}>
                <td>
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: 18 }}>{DOC_TYPE_EMOJI[doc.document_type] || '📄'}</span>
                    <div>
                      <div className="truncate" style={{ maxWidth: 240, fontWeight: 500 }}>{doc.original_filename}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{(doc.file_size / 1024).toFixed(1)} KB</div>
                    </div>
                  </div>
                </td>
                <td><span className="badge badge-blue" style={{ textTransform: 'capitalize' }}>{doc.document_type?.replace('_', ' ')}</span></td>
                <td><span className={`badge ${STATUS_BADGE[doc.status] || 'badge-gray'}`}>{doc.status}</span></td>
                <td>
                  {doc.risk_score != null && (
                    <div className="risk-meter" style={{ minWidth: 100 }}>
                      <div className="risk-bar">
                        <div className={`risk-fill risk-${doc.risk_level || 'low'}`} style={{ width: `${doc.risk_score}%` }} />
                      </div>
                      <span style={{ fontSize: 11, minWidth: 28 }}>{doc.risk_score?.toFixed(0)}</span>
                    </div>
                  )}
                </td>
                <td>{doc.confidence_score ? `${(doc.confidence_score * 100).toFixed(0)}%` : '—'}</td>
                <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {doc.created_at ? format(new Date(doc.created_at), 'MMM d, yyyy') : '—'}
                </td>
                <td>
                  <div className="flex items-center gap-2">
                    <button className="btn-icon" onClick={e => { e.stopPropagation(); navigate(`/documents/${doc.id}`) }} title="View"><Eye size={14} /></button>
                    <button className="btn-icon" onClick={e => handleDelete(doc.id, doc.original_filename, e)} title="Delete" style={{ color: 'var(--danger)' }}><Trash2 size={14} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > 15 && (
        <div className="flex items-center justify-between" style={{ marginTop: 16 }}>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Showing {(page - 1) * 15 + 1}–{Math.min(page * 15, total)} of {total}</span>
          <div className="flex gap-2">
            <button className="btn btn-sm btn-secondary" onClick={() => setPage(p => p - 1)} disabled={page === 1}>← Prev</button>
            <button className="btn btn-sm btn-secondary" onClick={() => setPage(p => p + 1)} disabled={page * 15 >= total}>Next →</button>
          </div>
        </div>
      )}
    </div>
  )
}
