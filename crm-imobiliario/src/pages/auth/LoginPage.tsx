import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

export function LoginPage() {
    const { signIn } = useAuth()
    const navigate = useNavigate()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        const { error } = await signIn(email, password)
        setLoading(false)
        if (error) {
            setError('Email ou senha incorretos. Verifique suas credenciais.')
        } else {
            toast.success('Bem-vindo de volta!')
            navigate('/')
        }
    }

    return (
        <div className="auth-layout">
            <div className="auth-card">
                <div className="auth-logo">
                    <div className="auth-logo-icon">🏠</div>
                    <div>
                        <div className="auth-logo-text">CRM Imobiliário</div>
                        <div className="auth-logo-sub">Sistema de Gestão</div>
                    </div>
                </div>

                <h1 className="auth-title">Bem-vindo de volta</h1>
                <p className="auth-subtitle">Entre com suas credenciais para acessar o sistema</p>

                {error && <div className="msg msg-error">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label" htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            className="form-input"
                            placeholder="seu@email.com"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            required
                            autoComplete="email"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="password">Senha</label>
                        <input
                            id="password"
                            type="password"
                            className="form-input"
                            placeholder="••••••••"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            required
                            autoComplete="current-password"
                        />
                    </div>

                    <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: '0.5rem' }}>
                        {loading ? <><span className="spinner" /> Entrando...</> : 'Entrar'}
                    </button>
                </form>

                <div className="auth-links">
                    <Link to="/forgot-password" className="auth-link">Esqueci minha senha</Link>
                    <Link to="/register" className="auth-link">Criar conta</Link>
                </div>
            </div>
        </div>
    )
}
