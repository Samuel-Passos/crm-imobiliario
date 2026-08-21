import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useDeviceType } from '../hooks/useDeviceType'
import toast from 'react-hot-toast'

const ROBO_URL = 'http://localhost:8766'
const LAUNCHER_URL = 'http://localhost:8767'

const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/kanban', label: 'CRM Kanban', icon: '🗂️' },
    { path: '/pesquisa', label: 'Pesquisar Imóvel', icon: '🔍' },
    { path: '/contatos', label: 'Contatos', icon: '👥' },
    { path: '/mapa', label: 'Mapa de Imóveis', icon: '🗺️' },
    { path: '/automacoes', label: 'Automações', icon: '⚙️' },
    { path: '/disponibilidade', label: 'Robô Disponibilidade', icon: '🤖' },
    { path: '/extrator-cnpj', label: 'Extrator de CNPJ', icon: '🏢' },
    { path: '/captador', label: 'Captador OLX', icon: '🕸️' },
    { path: '/campanhas', label: 'Motor de Campanhas', icon: '📞' },
    { path: '/templates', label: 'Templates de Mensagem', icon: '📝' },
    { path: '/designer', label: 'Designer IA', icon: '🎨' },
    { path: '/configuracoes', label: 'Configurações', icon: '⚙️' },

]

export function Sidebar() {
    const { profile, signOut } = useAuth()
    const navigate = useNavigate()
    const location = useLocation()
    const device = useDeviceType()
    const [collapsed, setCollapsed] = useState(false)
    const [subindo, setSubindo] = useState(false)
    const [roboOnline, setRoboOnline] = useState<boolean | null>(null)
    const [daemonOnline, setDaemonOnline] = useState<boolean | null>(null)

    // Polling de status do robô e do daemon a cada 8s
    useEffect(() => {
        const check = async () => {
            // Checa robô principal
            try {
                const res = await fetch(`${ROBO_URL}/status`, { signal: AbortSignal.timeout(2500) })
                setRoboOnline(res.ok)
            } catch {
                setRoboOnline(false)
            }
            // Checa launcher daemon
            try {
                const res = await fetch(`${LAUNCHER_URL}/ping`, { signal: AbortSignal.timeout(2500) })
                setDaemonOnline(res.ok)
            } catch {
                setDaemonOnline(false)
            }
        }
        check()
        const iv = setInterval(check, 8000)
        return () => clearInterval(iv)
    }, [])

    const handleSubirTudo = async () => {
        setSubindo(true)
        try {
            // Tenta primeiro o servidor principal (já está no ar)
            if (roboOnline) {
                const res = await fetch(`${ROBO_URL}/system/start`, { method: 'POST', signal: AbortSignal.timeout(8000) })
                if (res.ok) {
                    toast.success('🚀 Serviços sendo reiniciados!')
                    return
                }
            }
            // Fallback: daemon sempre ligado (porta 8767)
            if (daemonOnline) {
                const res = await fetch(`${LAUNCHER_URL}/start`, { method: 'POST', signal: AbortSignal.timeout(8000) })
                if (res.ok) {
                    toast.success('🚀 Iniciando todos os serviços... aguarde ~10s e recarregue.')
                    return
                }
            }
            toast.error('Daemon offline. Rode: python3 launcher_daemon.py', { duration: 6000 })
        } catch {
            toast.error('Não foi possível contatar o launcher.', { duration: 5000 })
        } finally {
            setSubindo(false)
        }
    }

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
                    <div style={{ flex: 1 }}>
                        <div className="auth-logo-text">CRM Imobiliário</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.15rem' }}>
                            <span style={{
                                width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
                                background: roboOnline === null ? '#94a3b8' : roboOnline ? '#10b981' : '#ef4444',
                                boxShadow: roboOnline ? '0 0 5px #10b981' : 'none',
                                transition: 'background 0.4s ease'
                            }} />
                            <div className="auth-logo-sub" style={{ fontSize: '0.68rem' }}>
                                {roboOnline === null ? 'verificando...' : roboOnline ? 'robô online' : 'robô offline'}
                            </div>
                        </div>
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

                {/* Botão Subir Tudo */}
                <button
                    onClick={handleSubirTudo}
                    disabled={subindo}
                    title={collapsed ? 'Subir Tudo' : undefined}
                    style={{
                        width: '100%', marginBottom: '0.5rem',
                        display: 'flex', alignItems: 'center', gap: '0.6rem',
                        padding: collapsed ? '0.75rem' : '0.65rem 1rem',
                        justifyContent: collapsed ? 'center' : 'flex-start',
                        borderRadius: '10px', border: '1px solid rgba(16,185,129,0.35)',
                        background: subindo ? 'rgba(16,185,129,0.06)' : 'rgba(16,185,129,0.1)',
                        color: '#10b981', cursor: subindo ? 'not-allowed' : 'pointer',
                        fontWeight: 700, fontSize: '0.88rem',
                        transition: 'all 0.2s ease',
                        opacity: subindo ? 0.7 : 1,
                    }}
                >
                    <span style={{ fontSize: '1rem' }}>{subindo ? '⏳' : '🚀'}</span>
                    {!collapsed && (subindo ? 'Subindo...' : 'Subir Tudo')}
                </button>

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
