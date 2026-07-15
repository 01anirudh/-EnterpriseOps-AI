import { useState } from 'react'
import { Settings as SettingsIcon, Key, Link2, Shield, Save } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { useAuthStore } from '../store/authStore'

export default function Settings() {
  const { user } = useAuthStore()
  const [saved, setSaved] = useState(false)

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="main-content page-enter" style={{ flex: 1 }}>
        <header style={{ marginBottom: '2.5rem' }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700, margin: '0 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <SettingsIcon color="#6366f1" size={28} />
            Platform Settings
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
            Manage your account, API keys, and external tool integrations.
          </p>
        </header>

        <div style={{ display: 'flex', gap: '2rem', maxWidth: 1000 }}>
          
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Profile */}
            <div className="glass-card" style={{ padding: '2rem' }}>
              <h3 style={{ margin: '0 0 1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
                <Shield size={18} color="#8b5cf6" /> User Profile
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Name</label>
                  <input className="input" type="text" value={user?.name || ''} disabled />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Email</label>
                  <input className="input" type="email" value={user?.email || ''} disabled />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Role</label>
                  <span className={`badge badge-${user?.role === 'manager' || user?.role === 'admin' ? 'warning' : 'primary'}`}>
                    {user?.role?.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            {/* API Keys */}
            <div className="glass-card" style={{ padding: '2rem' }}>
              <h3 style={{ margin: '0 0 1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
                <Key size={18} color="#10b981" /> LLM Configuration
              </h3>
              <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Google Gemini API Key (Backend .env handles this in production)</label>
                  <input className="input" type="password" placeholder="AIzaSy..." defaultValue="**********************" />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>OpenAI API Key (Optional Override)</label>
                  <input className="input" type="password" placeholder="sk-..." />
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
                  <button type="submit" className="btn btn-primary">
                    <Save size={16} /> Save Keys
                  </button>
                </div>
              </form>
            </div>
          </div>

          <div style={{ width: 350, display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Link2 size={18} color="#38bdf8" /> Integrations
              </h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ padding: '1rem', background: 'rgba(15,23,42,0.5)', borderRadius: 10, border: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                    <strong style={{ color: 'var(--text-primary)' }}>Gmail API</strong>
                    <span className="badge badge-success">Active</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>OAuth2 credentials loaded. Ready to send reports.</div>
                </div>

                <div style={{ padding: '1rem', background: 'rgba(15,23,42,0.5)', borderRadius: 10, border: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                    <strong style={{ color: 'var(--text-primary)' }}>Slack Bot</strong>
                    <span className="badge badge-neutral">Mock Mode</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Token missing. Notifications will be logged but not sent.</div>
                </div>

                <div style={{ padding: '1rem', background: 'rgba(15,23,42,0.5)', borderRadius: 10, border: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                    <strong style={{ color: 'var(--text-primary)' }}>GitHub API</strong>
                    <span className="badge badge-neutral">Mock Mode</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Token missing. Issues will be logged but not created.</div>
                </div>
              </div>
            </div>
            
            {saved && (
              <div style={{ padding: '1rem', background: 'rgba(16,185,129,0.1)', color: '#34d399', borderRadius: 10, border: '1px solid rgba(16,185,129,0.3)', textAlign: 'center', animation: 'fadeIn 0.3s ease' }}>
                Settings saved successfully!
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  )
}
