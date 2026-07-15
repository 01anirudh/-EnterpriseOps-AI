import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Upload, Database, GitBranch,
  ScrollText, FileText, Settings, LogOut,
  CheckSquare, Cpu, ChevronRight, Zap
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'

const nav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/workflow', icon: GitBranch, label: 'Workflow' },
  { to: '/upload', icon: Upload, label: 'Upload Docs' },
  { to: '/knowledge', icon: Database, label: 'Knowledge Base' },
  { to: '/logs', icon: ScrollText, label: 'Agent Logs' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/approvals', icon: CheckSquare, label: 'Approvals' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div style={{
        padding: '1.5rem 1.25rem 1rem',
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: 38, height: 38, borderRadius: 10,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 15px rgba(99,102,241,0.4)',
            flexShrink: 0,
          }}>
            <Zap size={20} color="white" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
              EnterpriseOps
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
              AI PLATFORM
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '0.75rem 0.75rem', overflowY: 'auto' }}>
        <div style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.1em', padding: '0.25rem 0.5rem 0.5rem', textTransform: 'uppercase' }}>
          Navigation
        </div>
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.6rem 0.875rem',
              borderRadius: 10,
              marginBottom: 2,
              textDecoration: 'none',
              fontSize: '0.875rem',
              fontWeight: 500,
              transition: 'all 0.2s ease',
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
              border: isActive ? '1px solid rgba(99,102,241,0.25)' : '1px solid transparent',
            })}
          >
            {({ isActive }) => (
              <>
                <Icon size={17} color={isActive ? '#6366f1' : undefined} />
                <span style={{ flex: 1 }}>{label}</span>
                {isActive && <ChevronRight size={14} color="#6366f1" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User Profile */}
      <div style={{
        padding: '0.875rem 1rem',
        borderTop: '1px solid var(--border)',
        background: 'rgba(15, 23, 42, 0.5)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.625rem' }}>
          <div style={{
            width: 34, height: 34, borderRadius: '50%',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.875rem', fontWeight: 700, color: 'white', flexShrink: 0,
          }}>
            {user?.name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.name}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.role?.toUpperCase()}
            </div>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="btn btn-secondary btn-sm"
          style={{ width: '100%', justifyContent: 'center' }}
        >
          <LogOut size={14} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
