import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Play, Terminal, Activity, CheckCircle2, XCircle, PauseCircle, ChevronRight, BrainCircuit } from 'lucide-react'
import { useWorkflowStore, LogEntry } from '../store/workflowStore'
import Sidebar from '../components/Sidebar'

const AGENTS = [
  'Planner', 'Knowledge', 'SQL', 'Analytics', 'Report', 'Human Approval', 'Email', 'Slack', 'GitHub'
]

export default function Workflow() {
  const [prompt, setPrompt] = useState('')
  const { submitWorkflow, startStreaming, logs, isStreaming, activeTaskId } = useWorkflowStore()
  const logsEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim() || isStreaming) return
    const taskId = await submitWorkflow(prompt)
    startStreaming(taskId, () => {})
    setPrompt('')
  }

  // Determine current active agent for the pipeline visualizer
  const currentAgent = logs.length > 0 ? logs[logs.length - 1].agent : null
  const currentStatus = logs.length > 0 ? logs[logs.length - 1].status : null

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="main-content page-enter" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', padding: 0 }}>
        
        <header style={{ padding: '2rem 2rem 1.5rem', borderBottom: '1px solid var(--border)', background: 'var(--bg-primary)', zIndex: 10 }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: '0 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <BrainCircuit color="#6366f1" size={28} />
            Agentic Workflow
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
            Submit an enterprise request and watch the multi-agent pipeline execute in real-time.
          </p>
        </header>

        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          
          {/* Left Panel - Input & Pipeline */}
          <div style={{ width: '45%', padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem', borderRight: '1px solid var(--border)', overflowY: 'auto' }}>
            
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1rem', fontSize: '1.1rem' }}>Submit Request</h3>
              <form onSubmit={handleSubmit}>
                <textarea
                  className="input"
                  placeholder="e.g. Analyze Q2 sales from the database, retrieve our discount policy, generate an executive report, and email the finance team."
                  value={prompt}
                  onChange={e => setPrompt(e.target.value)}
                  disabled={isStreaming}
                  style={{ minHeight: 120, marginBottom: '1rem' }}
                />
                <button type="submit" className="btn btn-primary" disabled={!prompt.trim() || isStreaming} style={{ width: '100%', justifyContent: 'center' }}>
                  {isStreaming ? (
                    <><div className="spinner" style={{ width: 16, height: 16 }} /> Agents Working...</>
                  ) : (
                    <><Play size={16} /> Execute Workflow</>
                  )}
                </button>
              </form>
            </div>

            <div className="glass-card" style={{ padding: '1.5rem', flex: 1 }}>
              <h3 style={{ margin: '0 0 1.5rem', fontSize: '1.1rem' }}>Agent Pipeline</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {AGENTS.map((agent, i) => {
                  const isPast = logs.some(l => l.agent === agent && l.status === 'success')
                  const isCurrent = currentAgent === agent && (currentStatus === 'running' || currentStatus === 'paused')
                  const isFailed = currentAgent === agent && currentStatus === 'failed'
                  
                  let icon = <div style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid var(--border)' }} />
                  if (isPast) icon = <CheckCircle2 size={16} color="#10b981" />
                  else if (isFailed) icon = <XCircle size={16} color="#ef4444" />
                  else if (isCurrent && currentStatus === 'paused') icon = <PauseCircle size={16} color="#f59e0b" />
                  else if (isCurrent) icon = <div className="spinner" style={{ width: 14, height: 14 }} />

                  return (
                    <div key={agent} style={{ display: 'flex', alignItems: 'center', gap: '1rem', opacity: (isPast || isCurrent || isFailed) ? 1 : 0.4 }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 24 }}>
                        {icon}
                        {i < AGENTS.length - 1 && <div style={{ width: 2, height: 24, background: isPast ? '#10b981' : 'var(--border)', margin: '4px 0' }} />}
                      </div>
                      <div style={{ paddingBottom: i < AGENTS.length - 1 ? 28 : 0 }}>
                        <div style={{ fontWeight: isCurrent ? 700 : 500, color: isCurrent ? 'var(--accent-primary)' : isPast ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                          {agent} Agent
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

          </div>

          {/* Right Panel - Live Logs */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
            <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border)', background: 'rgba(15,23,42,0.8)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
                <Terminal size={18} color="#94a3b8" /> Live Execution Logs
                {isStreaming && <div className="pulse-dot pulse-dot-green" style={{ marginLeft: '0.5rem' }} />}
              </div>
              {activeTaskId && (
                <span className="badge badge-neutral" style={{ fontFamily: 'JetBrains Mono' }}>
                  ID: {activeTaskId.split('-')[0]}
                </span>
              )}
            </div>
            
            <div style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontFamily: 'JetBrains Mono' }}>
              {logs.length === 0 ? (
                <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <Terminal size={48} style={{ opacity: 0.2, margin: '0 auto 1rem' }} />
                  Submit a request to start the agent pipeline.
                </div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className={`log-entry log-entry-${log.status}`}>
                    <div style={{ width: 75, flexShrink: 0, color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp ? log.timestamp * 1000 : Date.now()).toLocaleTimeString([], { hour12: false })}
                    </div>
                    <div style={{ width: 120, flexShrink: 0, fontWeight: 600, color: log.status === 'failed' ? '#ef4444' : log.status === 'paused' ? '#f59e0b' : 'var(--text-primary)' }}>
                      [{log.agent}]
                    </div>
                    <div style={{ flex: 1, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {log.message}
                      {log.type === 'awaiting_approval' && (
                        <div style={{ marginTop: '0.5rem' }}>
                          <Link to="/approvals" className="btn btn-warning btn-sm" style={{ display: 'inline-flex' }}>
                            Go to Approvals <ChevronRight size={14} />
                          </Link>
                        </div>
                      )}
                      {log.type === 'completed' && log.report_path && (
                        <div style={{ marginTop: '0.5rem' }}>
                          <Link to="/reports" className="btn btn-success btn-sm" style={{ display: 'inline-flex' }}>
                            View Generated Report <ChevronRight size={14} />
                          </Link>
                        </div>
                      )}
                    </div>
                    {log.execution_time_ms && (
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                        {log.execution_time_ms.toFixed(0)}ms
                      </div>
                    )}
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
