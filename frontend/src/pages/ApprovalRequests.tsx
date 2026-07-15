import { useEffect, useState } from 'react'
import { CheckSquare, ShieldAlert, Check, X, ArrowRight, ExternalLink } from 'lucide-react'
import { useWorkflowStore } from '../store/workflowStore'
import Sidebar from '../components/Sidebar'

export default function ApprovalRequests() {
  const { pendingApprovals, fetchPendingApprovals, approveTask, rejectTask } = useWorkflowStore()
  const [processingId, setProcessingId] = useState<string | null>(null)

  useEffect(() => {
    fetchPendingApprovals()
  }, [])

  const handleApprove = async (id: string) => {
    setProcessingId(id)
    await approveTask(id)
    setProcessingId(null)
  }

  const handleReject = async (id: string) => {
    setProcessingId(id)
    await rejectTask(id)
    setProcessingId(null)
  }

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="main-content page-enter" style={{ flex: 1 }}>
        <header style={{ marginBottom: '2.5rem' }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: '0 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <CheckSquare color="#f59e0b" size={28} />
            Human Approval Queue
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
            Workflows paused awaiting manager approval before executing external actions.
          </p>
        </header>

        <div style={{ maxWidth: 800 }}>
          {pendingApprovals.length === 0 ? (
            <div className="glass-card" style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <ShieldAlert size={48} style={{ opacity: 0.2, margin: '0 auto 1rem' }} />
              <h3 style={{ margin: '0 0 0.5rem', color: 'var(--text-primary)' }}>All clear</h3>
              <p style={{ margin: 0 }}>There are no workflows awaiting approval at this time.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {pendingApprovals.map(task => (
                <div key={task.id} className="glass-card" style={{ padding: '1.5rem', borderLeft: '4px solid #f59e0b' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <span className="badge badge-warning">Awaiting Approval</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: {task.id.split('-')[0]}</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>• {new Date(task.created_at).toLocaleString()}</span>
                      </div>
                      <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-primary)' }}>{task.prompt}</h3>
                    </div>
                  </div>

                  <div style={{ background: 'rgba(15,23,42,0.6)', padding: '1rem', borderRadius: 8, marginBottom: '1.5rem', fontSize: '0.875rem' }}>
                    <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Proposed Actions (Pending):</div>
                    <ul style={{ margin: 0, paddingLeft: '1.5rem', color: 'var(--text-secondary)' }}>
                      <li>Send executive report via Email</li>
                      <li>Post completion summary to Slack</li>
                      <li>Create tracking issue on GitHub</li>
                    </ul>
                  </div>

                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <button
                      onClick={() => handleApprove(task.id)}
                      disabled={processingId === task.id}
                      className="btn btn-success"
                      style={{ flex: 1, justifyContent: 'center' }}
                    >
                      {processingId === task.id ? <div className="spinner" style={{ width: 14, height: 14 }} /> : <Check size={16} />}
                      Approve & Execute
                    </button>
                    <button
                      onClick={() => handleReject(task.id)}
                      disabled={processingId === task.id}
                      className="btn btn-danger"
                      style={{ flex: 1, justifyContent: 'center' }}
                    >
                      {processingId === task.id ? <div className="spinner" style={{ width: 14, height: 14 }} /> : <X size={16} />}
                      Reject Workflow
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
