import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import type { Role } from '../contexts/AuthContext'

interface PrivateRouteProps {
    children: React.ReactNode
    allowedRoles?: Role[]
}

export function PrivateRoute({ children, allowedRoles }: PrivateRouteProps) {
    const { user, profile, loading } = useAuth()

    if (loading) {
        return (
            <div className="loading-screen">
                <div className="spinner" />
                <p>Carregando...</p>
            </div>
        )
    }

    if (!user) return <Navigate to="/login" replace />

    if (allowedRoles && profile && !allowedRoles.includes(profile.role)) {
        return <Navigate to="/" replace />
    }

    return <>{children}</>
}
