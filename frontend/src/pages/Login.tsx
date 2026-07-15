import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Zap, LogIn, UserPlus } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

export default function Login() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(email, password)
      } else {
        await register(name, email, password)
        await login(email, password)
      }
      navigate('/dashboard')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(ellipse at 20% 50%, rgba(99,102,241,0.12) 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, rgba(139,92,246,0.1) 0%, transparent 60%), var(--bg-primary)',
      padding: '1rem',
    }}>
      {/* Background grid */}
      <div style={{
        position: 'fixed', inset: 0, backgroundImage: 'linear-gradient(rgba(51,65,85,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(51,65,85,0.3) 1px, transparent 1px)',
        backgroundSize: '40px 40px', pointerEvents: 'none', opacity: 0.4,
      }} />

      <div className="page-enter" style={{ width: '100%', maxWidth: 420, position: 'relative', zIndex: 1 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            width: 60, height: 60, borderRadius: 16, margin: '0 auto 1rem',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 8px 32px rgba(99,102,241,0.4)',
          }}>
            <Zap size={28} color="white" />
          </div>
          <h1 style={{ fontWeight: 800, fontSize: '1.75rem', margin: 0 }}>
            <span className="gradient-text">EnterpriseOps AI</span>
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.4rem' }}>
            Autonomous Multi-Agent Platform
          </p>
        </div>

        {/* Card */}
        <div className="glass-card" style={{ padding: '2rem' }}>
          {/* Tab switcher */}
          <div style={{
            display: 'flex', background: 'rgba(15,23,42,0.6)', borderRadius: 10, padding: 4, marginBottom: '1.5rem',
          }}>
            {(['login', 'register'] as const).map((m) => (
              <button key={m} onClick={() => setMode(m)} className="btn" style={{
                flex: 1, justifyContent: 'center', padding: '0.5rem',
                background: mode === m ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent',
                boxShadow: mode === m ? '0 4px 12px rgba(99,102,241,0.3)' : 'none',
                color: mode === m ? 'white' : 'var(--text-muted)',
                borderRadius: 8,
              }}>
                {m === 'login' ? <><LogIn size={14} /> Sign In</> : <><UserPlus size={14} /> Register</>}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {mode === 'register' && (
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500, display: 'block', marginBottom: 4 }}>Full Name</label>
                <input id="name" className="input" type="text" placeholder="John Smith" value={name} onChange={e => setName(e.target.value)} required />
              </div>
            )}

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500, display: 'block', marginBottom: 4 }}>Email</label>
              <input id="email" className="input" type="email" placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} required />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500, display: 'block', marginBottom: 4 }}>Password</label>
              <div style={{ position: 'relative' }}>
                <input id="password" className="input" type={showPass ? 'text' : 'password'} placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} required style={{ paddingRight: '2.5rem' }} />
                <button type="button" onClick={() => setShowPass(!showPass)} style={{
                  position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)',
                }}>
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div style={{ padding: '0.625rem 0.875rem', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, fontSize: '0.8rem', color: '#f87171' }}>
                {error}
              </div>
            )}

            <button id="submit-btn" className="btn btn-primary btn-lg" type="submit" disabled={loading} style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
              {loading ? <><div className="spinner" style={{ width: 18, height: 18 }} /> Processing...</> : (mode === 'login' ? 'Sign In' : 'Create Account')}
            </button>
          </form>

          {mode === 'login' && (
            <p style={{ textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '1.25rem' }}>
              Demo: <strong style={{ color: 'var(--text-secondary)' }}>admin@demo.com</strong> / <strong style={{ color: 'var(--text-secondary)' }}>admin123</strong>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
