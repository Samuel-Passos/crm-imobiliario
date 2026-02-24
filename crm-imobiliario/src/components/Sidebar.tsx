import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useDeviceType } from '../hooks/useDeviceType'
import toast from 'react-hot-toast'

const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/kanban', label: 'CRM Kanban', icon: '🗂️' },
    { path: '/pesquisa', label: 'Pesquisar Imóvel', icon: '🔍' },
    { path: '/contatos', label: 'Contatos', icon: '👥' },
    { path: '/mapa', label: 'Mapa de Imóveis', icon: '🗺️' },
    { path: '/automacoes', label: 'Automações', icon: '⚙️' },
]

export function Sidebar() {
    const { profile, signOut } = useAuth()
    const navigate = useNavigate()
    const location = useLocation()
    const device = useDeviceType()
    const [collapsed, setCollapsed] = useState(false)

    // Mobile: não renderiza sidebar (usa bottom nav)
    if (device === 'mobile') return null

    const isTablet = device === 'tablet'
    const sidebarWidth = isTablet && collapsed ? 64 : 260

    const handleSignOut = async () => {
        await signOut()
        toast.success('Até logo!')
        navigate('/login')
    }

    return (
        <aside className="sidebar" style={{ width: sidebarWidth, minWidth: sidebarWidth, transition: 'width 250ms ease' }}>
            {/* Toggle (tablet) */}
            {isTablet && (
                <button
                    onClick={() => setCollapsed(c => !c)}
                    style={{
                        background: 'none', border: 'none', color: 'var(--text-muted)',
                        cursor: 'pointer', fontSize: '1.1rem', padding: '0.5rem',
                        alignSelf: 'flex-end', marginBottom: '0.5rem'
                    }}
                    title={collapsed ? 'Expandir' : 'Recolher'}
                >
                    {collapsed ? '▶' : '◀'}
                </button>
            )}

            {/* Logo */}
            {!collapsed && (
                <div className="auth-logo" style={{ marginBottom: '2rem' }}>
                    <div className="auth-logo-icon">🏠</div>
                    <div>
                        <div className="auth-logo-text">CRM Imobiliário</div>
                        <div className="auth-logo-sub">Sistema de Gestão</div>
                    </div>
                </div>
            )}
            {collapsed && <div style={{ marginBottom: '2rem', textAlign: 'center', fontSize: '1.5rem' }}>🏠</div>}

            {/* Nav */}
            <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {navItems.map(item => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
                        title={collapsed ? item.label : undefined}
                        style={collapsed ? { justifyContent: 'center', padding: '0.75rem' } : {}}
                    >
                        <span style={{ fontSize: '1.1rem' }}>{item.icon}</span>
                        {!collapsed && item.label}
                    </Link>
                ))}

                {profile?.role === 'admin' && (
                    <>
                        <div style={{ borderTop: '1px solid var(--border)', margin: '0.75rem 0' }} />
                        <Link to="/admin/users" className={`nav-item ${location.pathname === '/admin/users' ? 'active' : ''}`}
                            title={collapsed ? 'Usuários' : undefined}
                            style={collapsed ? { justifyContent: 'center', padding: '0.75rem' } : {}}>
                            <span>⚙️</span>
                            {!collapsed && 'Usuários'}
                        </Link>
                    </>
                )}
            </nav>

            {/* User info + logout */}
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
                <Link to="/profile" className="nav-item"
                    style={collapsed ? { justifyContent: 'center', padding: '0.75rem' } : { marginBottom: '0.5rem' }}>
                    <span>👤</span>
                    {!collapsed && (
                        <div style={{ flex: 1, overflow: 'hidden' }}>
                            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {profile?.nome_completo || 'Meu Perfil'}
                            </div>
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{profile?.role}</div>
                        </div>
                    )}
                </Link>
                <button
                    className="nav-item"
                    onClick={handleSignOut}
                    style={{
                        width: '100%', background: 'none', border: 'none',
                        color: 'var(--error)', cursor: 'pointer',
                        ...(collapsed ? { justifyContent: 'center', padding: '0.75rem' } : {})
                    }}
                    title={collapsed ? 'Sair' : undefined}
                >
                    <span>🚪</span>
                    {!collapsed && 'Sair'}
                </button>
            </div>
        </aside>
    )
}
