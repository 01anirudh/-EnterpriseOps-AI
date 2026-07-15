import { useEffect, useState } from 'react'
import { FileText, Download, Code, Layout, Calendar } from 'lucide-react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import Sidebar from '../components/Sidebar'
import { useWorkflowStore } from '../store/workflowStore'

export default function Reports() {
  const { tasks, fetchTasks } = useWorkflowStore()
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [reportMarkdown, setReportMarkdown] = useState<string>('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchTasks()
  }, [])

  const reports = tasks.filter(t => t.report_path)

  useEffect(() => {
    if (reports.length > 0 && !selectedTaskId) {
      setSelectedTaskId(reports[0].id)
    }
  }, [reports])

  useEffect(() => {
    const fetchReport = async () => {
      if (!selectedTaskId) return
      setLoading(true)
      try {
        const res = await axios.get(`/api/reports/${selectedTaskId}?format=markdown`)
        setReportMarkdown(res.data)
      } catch (e) {
        setReportMarkdown('Failed to load report.')
      } finally {
        setLoading(false)
      }
    }
    fetchReport()
  }, [selectedTaskId])

  const handleDownloadPDF = async () => {
    if (!selectedTaskId) return
    window.open(`http://localhost:8000/api/reports/${selectedTaskId}?format=pdf`, '_blank')
  }

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="main-content page-enter" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', padding: 0 }}>
        
        <header style={{ padding: '2rem 2rem 1.5rem', borderBottom: '1px solid var(--border)' }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: '0 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <FileText color="#6366f1" size={28} />
            Executive Reports
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
            Generated Markdown reports with embedded charts and KPI tables.
          </p>
        </header>

        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          
          {/* Sidebar list */}
          <div style={{ width: 320, borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', background: 'rgba(15,23,42,0.3)' }}>
            <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)', fontWeight: 600, color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              Generated Reports ({reports.length})
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
              {reports.map(r => (
                <div
                  key={r.id}
                  onClick={() => setSelectedTaskId(r.id)}
                  style={{
                    padding: '1rem', borderRadius: 10, cursor: 'pointer', marginBottom: '0.5rem',
                    background: selectedTaskId === r.id ? 'rgba(99,102,241,0.15)' : 'transparent',
                    border: selectedTaskId === r.id ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent',
                    transition: 'all 0.2s',
                  }}
                >
                  <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {r.prompt}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <Calendar size={12} /> {new Date(r.completed_at || r.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
              {reports.length === 0 && (
                <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No reports generated yet. Run a workflow first.
                </div>
              )}
            </div>
          </div>

          {/* Report Viewer */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
            {selectedTaskId ? (
              <>
                <div style={{ padding: '1rem 2rem', borderBottom: '1px solid var(--border)', background: 'rgba(15,23,42,0.8)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <span className="badge badge-primary"><Layout size={12} /> Markdown</span>
                  </div>
                  <button onClick={handleDownloadPDF} className="btn btn-secondary btn-sm">
                    <Download size={14} /> Download PDF
                  </button>
                </div>
                
                <div style={{ flex: 1, overflowY: 'auto', padding: '2rem', display: 'flex', justifyContent: 'center' }}>
                  {loading ? (
                    <div style={{ marginTop: '4rem' }}><div className="spinner" /></div>
                  ) : (
                    <div className="glass-card" style={{ width: '100%', maxWidth: 850, padding: '3rem', background: '#ffffff', color: '#1e293b' }}>
                      <div className="markdown-body">
                        <ReactMarkdown>{reportMarkdown}</ReactMarkdown>
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div style={{ margin: 'auto', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <FileText size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                Select a report to view
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  )
}
