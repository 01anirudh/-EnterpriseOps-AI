import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { GitBranch, Database, FileText, CheckCircle2, Clock, AlertTriangle, ArrowRight, Activity, FileCheck2, Bot } from 'lucide-react'
import { useWorkflowStore, Task } from '../store/workflowStore'
import { useDocumentStore } from '../store/documentStore'
import { useAuthStore } from '../store/authStore'
import Sidebar from '../components/Sidebar'

export default function Dashboard() {
  const { user } = useAuthStore()
  const { tasks, pendingApprovals, fetchTasks, fetchPendingApprovals } = useWorkflowStore()
  const { documents, fetchDocuments } = useDocumentStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      await Promise.all([fetchTasks(), fetchPendingApprovals(), fetchDocuments()])
      setLoading(false)
    }
    load()
  }, [])

  const stats = [
    { label: 'Active Agents', value: '9/9', icon: Bot, color: 'primary' },
    { label: 'Pending Approvals', value: pendingApprovals.length, icon: CheckCircle2, color: pendingApprovals.length > 0 ? 'warning' : 'neutral' },
    { label: 'Documents in RAG', value: documents.filter(d => d.embedding_status === 'done').length, icon: Database, color: 'success' },
    { label: 'Completed Workflows', value: tasks.filter(t => t.status === 'completed').length, icon: GitBranch, color: 'info' },
  ]

  if (loading) return (
    <div className="main-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="spinner" />
    </div>
  )

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="main-content page-enter" style={{ flex: 1 }}>
        <header style={{ marginBottom: '2.5rem' }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: '0 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Activity color="#6366f1" size={28} />
            Operations Dashboard
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
            Welcome back, {user?.name}. Here's an overview of your AI workforce.
          </p>
        </header>

        {/* Stats Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
          {stats.map((s, i) => (
            <div key={i} className="stat-card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{s.label}</span>
                <span className={`badge badge-${s.color}`} style={{ padding: '0.35rem' }}>
                  <s.icon size={14} />
                </span>
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                {s.value}
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
          {/* Recent Activity */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Clock size={18} color="#8b5cf6" /> Recent Workflows
              </h3>
              <Link to="/workflow" className="btn btn-secondary btn-sm">View All <ArrowRight size={14} /></Link>
            </div>
            
            {tasks.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                <GitBranch size={32} style={{ opacity: 0.5, margin: '0 auto 1rem' }} />
                No workflows executed yet.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {tasks.slice(0, 4).map(t => (
                  <div key={t.id} style={{ padding: '1rem', background: 'rgba(15,23,42,0.5)', borderRadius: 12, border: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span className={`badge badge-${t.status === 'completed' ? 'success' : t.status === 'failed' ? 'danger' : t.status === 'awaiting_approval' ? 'warning' : 'primary'}`}>
                        {t.status.replace('_', ' ')}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {new Date(t.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {t.prompt}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Pending Action / Quick Links */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {pendingApprovals.length > 0 && (
              <div className="glass-card" style={{ padding: '1.5rem', borderColor: 'rgba(245,158,11,0.4)', background: 'linear-gradient(to bottom, rgba(245,158,11,0.05), transparent)' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                  <div style={{ padding: '0.75rem', background: 'rgba(245,158,11,0.15)', borderRadius: 12, color: '#fbbf24' }}>
                    <AlertTriangle size={24} />
                  </div>
                  <div>
                    <h3 style={{ margin: '0 0 0.5rem', color: '#fbbf24' }}>Manager Approval Required</h3>
                    <p style={{ margin: '0 0 1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                      {pendingApprovals.length} workflow{pendingApprovals.length > 1 ? 's are' : ' is'} paused awaiting human review before executing external actions (Email, Slack, GitHub).
                    </p>
                    <Link to="/approvals" className="btn btn-warning" style={{ background: '#f59e0b', color: 'white', border: 'none' }}>
                      Review Actions
                    </Link>
                  </div>
                </div>
              </div>
            )}

            <div className="glass-card" style={{ padding: '1.5rem' }}>
               <h3 style={{ margin: '0 0 1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FileCheck2 size={18} color="#10b981" /> Latest Reports
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {tasks.filter(t => t.report_path).slice(0, 3).map(t => (
                  <Link key={t.id} to="/reports" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.875rem', background: 'rgba(15,23,42,0.5)', borderRadius: 10, textDecoration: 'none', border: '1px solid var(--border)' }} className="glass-card-hover">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <FileText size={16} color="#94a3b8" />
                      <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>Report {t.id.slice(0,8)}</span>
                    </div>
                    <ArrowRight size={14} color="#6366f1" />
                  </Link>
                ))}
                {tasks.filter(t => t.report_path).length === 0 && (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No reports generated yet.</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
