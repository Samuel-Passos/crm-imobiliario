import { useState } from 'react'
import { Link } from 'react-router-dom'
import { supabase } from '../../lib/supabase'
import toast from 'react-hot-toast'

export function ForgotPasswordPage() {
    const [email, setEmail] = useState('')
    const [loading, setLoading] = useState(false)
    const [sent, setSent] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/reset-password`
        })
        setLoading(false)
        if (error) {
            toast.error('Erro ao enviar email. Tente novamente.')
        } else {
            setSent(true)
        }
    }

    return (
        <div className="auth-layout">
            <div className="auth-card">
                <div className="auth-logo">
                    <div className="auth-logo-icon">🏠</div>
                    <div>
                        <div className="auth-logo-text">CRM Imobiliário</div>
                        <div className="auth-logo-sub">Recuperar Senha</div>
                    </div>
                </div>

                {sent ? (
                    <>
                        <div className="msg msg-success" style={{ marginTop: '1rem' }}>
                            ✅ Email enviado! Verifique sua caixa de entrada e clique no link para redefinir sua senha.
                        </div>
                        <Link to="/login" className="btn btn-primary" style={{ display: 'flex', marginTop: '1.5rem' }}>
                            Voltar ao login
                        </Link>
                    </>
                ) : (
                    <>
                        <h1 className="auth-title">Esqueceu a senha?</h1>
                        <p className="auth-subtitle">Informe seu email e enviaremos um link de recuperação</p>

                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label className="form-label" htmlFor="email">Email cadastrado</label>
                                <input
                                    id="email"
                                    type="email"
                                    className="form-input"
                                    placeholder="seu@email.com"
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    required
                                />
                            </div>
                            <button type="submit" className="btn btn-primary" disabled={loading}>
                                {loading ? <><span className="spinner" /> Enviando...</> : 'Enviar link de recuperação'}
                            </button>
                        </form>

                        <div className="auth-links" style={{ justifyContent: 'center', marginTop: '1rem' }}>
                            <Link to="/login" className="auth-link">← Voltar ao login</Link>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}
