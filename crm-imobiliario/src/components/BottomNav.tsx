import { Link, useLocation } from 'react-router-dom'

const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/kanban', label: 'Kanban', icon: '🗂️' },
    { path: '/pesquisa', label: 'Pesquisa', icon: '🔍' },
    { path: '/disponibilidade', label: 'Robô', icon: '🤖' },
    { path: '/profile', label: 'Perfil', icon: '👤' },
]

export function BottomNav() {
    const location = useLocation()

    return (
        <nav className="bottom-nav">
            {navItems.map(item => (
                <Link
                    key={item.path}
                    to={item.path}
                    className={`bottom-nav-item ${location.pathname === item.path ? 'active' : ''}`}
                >
                    <span className="bottom-nav-icon">{item.icon}</span>
                    <span className="bottom-nav-label">{item.label}</span>
                </Link>
            ))}
        </nav>
    )
}
