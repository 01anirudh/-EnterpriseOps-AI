import { useCallback, useState } from 'react'
import { Upload as UploadIcon, File, X, CheckCircle2, AlertCircle } from 'lucide-react'
import { useDocumentStore } from '../store/documentStore'
import Sidebar from '../components/Sidebar'

export default function Upload() {
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<'idle'|'uploading'|'success'|'error'>('idle')
  const { uploadDocument } = useDocumentStore()

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
      setStatus('idle')
      setProgress(0)
    }
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setStatus('idle')
      setProgress(0)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setStatus('uploading')
    try {
      await uploadDocument(file, (pct) => setProgress(pct))
      setStatus('success')
      setFile(null)
    } catch (e) {
      setStatus('error')
    }
  }

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="main-content page-enter" style={{ flex: 1 }}>
        <header style={{ marginBottom: '2.5rem' }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: '0 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <UploadIcon color="#6366f1" size={28} />
            Document Ingestion
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
            Upload enterprise documents (PDF, DOCX, CSV, Excel) to the RAG knowledge base.
          </p>
        </header>

        <div className="glass-card" style={{ maxWidth: 600, padding: '2rem' }}>
          <div
            className={`upload-zone ${dragActive ? 'drag-over' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <input
              id="file-input"
              type="file"
              style={{ display: 'none' }}
              onChange={handleChange}
              accept=".pdf,.docx,.xlsx,.csv,.txt"
            />
            
            <div style={{ display: 'inline-flex', padding: '1rem', background: 'rgba(99,102,241,0.1)', borderRadius: '50%', marginBottom: '1rem' }}>
              <UploadIcon size={32} color="#6366f1" />
            </div>
            <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.1rem' }}>Click or drag file to upload</h3>
            <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Supports PDF, DOCX, XLSX, CSV up to 50MB
            </p>
          </div>

          {file && (
            <div style={{ marginTop: '2rem', padding: '1.25rem', background: 'rgba(15,23,42,0.6)', borderRadius: 12, border: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: status === 'uploading' ? '1rem' : 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <File size={20} color="#94a3b8" />
                  <div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>{file.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                  </div>
                </div>
                {status === 'idle' && (
                  <button onClick={() => setFile(null)} className="btn btn-secondary btn-sm" style={{ padding: '0.4rem' }}>
                    <X size={16} />
                  </button>
                )}
                {status === 'success' && <CheckCircle2 size={20} color="#10b981" />}
                {status === 'error' && <AlertCircle size={20} color="#ef4444" />}
              </div>

              {status === 'uploading' && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                    <span>Uploading & Extracting...</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${progress}%` }} />
                  </div>
                </div>
              )}
            </div>
          )}

          <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              className="btn btn-primary"
              disabled={!file || status === 'uploading' || status === 'success'}
              onClick={handleUpload}
            >
              {status === 'uploading' ? 'Processing...' : 'Upload & Process'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
