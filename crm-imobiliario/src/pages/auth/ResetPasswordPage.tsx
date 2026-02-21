import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../../lib/supabase'
import toast from 'react-hot-toast'

export function ResetPasswordPage() {
    const navigate = useNavigate()
    const [password, setPassword] = useState('')
    const [confirm, setConfirm] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        if (password !== confirm) { setError('As senhas não coincidem.'); return }
        if (password.length < 6) { setError('A senha deve ter pelo menos 6 caracteres.'); return }
        setLoading(true)
        const { error } = await supabase.auth.updateUser({ password })
        setLoading(false)
        if (error) {
            setError('Erro ao redefinir senha. O link pode ter expirado.')
        } else {
            toast.success('Senha redefinida com sucesso!')
            navigate('/login')
        }
    }

    return (
        <div className="auth-layout">
            <div className="auth-card">
                <div className="auth-logo">
                    <div className="auth-logo-icon">🏠</div>
                    <div>
                        <div className="auth-logo-text">CRM Imobiliário</div>
                        <div className="auth-logo-sub">Nova Senha</div>
                    </div>
                </div>

                <h1 className="auth-title">Redefinir senha</h1>
                <p className="auth-subtitle">Escolha uma nova senha segura para sua conta</p>

                {error && <div className="msg msg-error">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Nova senha</label>
                        <input
                            type="password" className="form-input"
                            placeholder="mín. 6 caracteres"
                            value={password} onChange={e => setPassword(e.target.value)} required
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Confirmar nova senha</label>
                        <input
                            type="password" className="form-input"
                            placeholder="••••••••"
                            value={confirm} onChange={e => setConfirm(e.target.value)} required
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? <><span className="spinner" /> Salvando...</> : 'Redefinir senha'}
                    </button>
                </form>
            </div>
        </div>
    )
}
