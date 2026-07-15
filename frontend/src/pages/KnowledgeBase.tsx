import { useEffect } from 'react'
import { Database, Trash2, FileText, RefreshCw, File } from 'lucide-react'
import { useDocumentStore } from '../store/documentStore'
import Sidebar from '../components/Sidebar'

export default function KnowledgeBase() {
  const { documents, fetchDocuments, deleteDocument } = useDocumentStore()

  useEffect(() => {
    fetchDocuments()
  }, [])

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="main-content page-enter" style={{ flex: 1 }}>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
          <div>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: '0 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Database color="#6366f1" size={28} />
              Enterprise Knowledge Base
            </h1>
            <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
              Documents embedded in the Qdrant vector database for RAG retrieval.
            </p>
          </div>
          <button onClick={() => fetchDocuments()} className="btn btn-secondary">
            <RefreshCw size={16} /> Refresh
          </button>
        </header>

        <div className="glass-card" style={{ overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: 'rgba(15,23,42,0.8)', borderBottom: '1px solid var(--border)' }}>
                <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Document</th>
                <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Type</th>
                <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Size</th>
                <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Status</th>
                <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Chunks</th>
                <th style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Uploaded</th>
                <th style={{ padding: '1rem', textAlign: 'right' }}></th>
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <FileText size={48} style={{ opacity: 0.3, margin: '0 auto 1rem' }} />
                    No documents in the knowledge base yet.
                  </td>
                </tr>
              ) : (
                documents.map(doc => (
                  <tr key={doc.id} style={{ borderBottom: '1px solid rgba(51,65,85,0.4)', transition: 'background 0.2s' }}>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ padding: '0.5rem', background: 'rgba(99,102,241,0.1)', borderRadius: 8 }}>
                          <File size={16} color="#6366f1" />
                        </div>
                        <span style={{ fontWeight: 500 }}>{doc.original_filename}</span>
                      </div>
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>
                      <span className="badge badge-neutral">{doc.file_type.toUpperCase()}</span>
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span className={`badge badge-${doc.embedding_status === 'done' ? 'success' : doc.embedding_status === 'failed' ? 'danger' : 'warning'}`}>
                        {doc.embedding_status === 'processing' && <div className="spinner" style={{ width: 10, height: 10, borderWidth: 2, borderTopColor: 'inherit', marginRight: 4 }} />}
                        {doc.embedding_status}
                      </span>
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>
                      {doc.chunk_count} vectors
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      <button onClick={() => deleteDocument(doc.id)} className="btn btn-secondary btn-sm" style={{ color: '#ef4444', borderColor: 'rgba(239,68,68,0.2)' }}>
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
