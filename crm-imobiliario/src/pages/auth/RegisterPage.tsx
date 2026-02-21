import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

interface ViaCEPResponse {
    logradouro: string; bairro: string; localidade: string; uf: string; erro?: boolean
}

export function RegisterPage() {
    const { signUp, updateProfile } = useAuth()
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)
    const [loadingCep, setLoadingCep] = useState(false)
    const [error, setError] = useState('')

    const [form, setForm] = useState({
        nome_completo: '', email: '', password: '', confirm_password: '',
        telefone: '', whatsapp: '',
        cep: '', logradouro: '', numero: '', complemento: '',
        bairro: '', cidade: '', estado: ''
    })

    const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
        setForm(f => ({ ...f, [field]: e.target.value }))

    const handleCepBlur = async () => {
        const cep = form.cep.replace(/\D/g, '')
        if (cep.length !== 8) return
        setLoadingCep(true)
        try {
            const res = await fetch(`https://viacep.com.br/ws/${cep}/json/`)
            const data: ViaCEPResponse = await res.json()
            if (!data.erro) {
                setForm(f => ({
                    ...f,
                    logradouro: data.logradouro,
                    bairro: data.bairro,
                    cidade: data.localidade,
                    estado: data.uf
                }))
            }
        } catch (_) {
            toast.error('Erro ao buscar CEP')
        }
        setLoadingCep(false)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        if (form.password !== form.confirm_password) {
            setError('As senhas não coincidem.')
            return
        }
        if (form.password.length < 6) {
            setError('A senha deve ter pelo menos 6 caracteres.')
            return
        }
        setLoading(true)
        const { error } = await signUp(form.email, form.password, form.nome_completo)
        if (error) {
            setError(error.message === 'User already registered'
                ? 'Este email já está cadastrado.'
                : 'Erro ao criar conta. Tente novamente.')
            setLoading(false)
            return
        }
        await updateProfile({
            nome_completo: form.nome_completo, telefone: form.telefone,
            whatsapp: form.whatsapp, email: form.email,
            cep: form.cep, logradouro: form.logradouro, numero: form.numero,
            complemento: form.complemento, bairro: form.bairro,
            cidade: form.cidade, estado: form.estado
        })
        setLoading(false)
        toast.success('Conta criada! Verifique seu email para confirmar.')
        navigate('/login')
    }

    return (
        <div className="auth-layout">
            <div className="auth-card" style={{ maxWidth: 560 }}>
                <div className="auth-logo">
                    <div className="auth-logo-icon">🏠</div>
                    <div>
                        <div className="auth-logo-text">CRM Imobiliário</div>
                        <div className="auth-logo-sub">Criar Conta</div>
                    </div>
                </div>

                <h1 className="auth-title">Crie sua conta</h1>
                <p className="auth-subtitle">Preencha os dados para acessar o sistema</p>

                {error && <div className="msg msg-error">{error}</div>}

                <form onSubmit={handleSubmit}>
                    {/* Dados pessoais */}
                    <div className="form-group">
                        <label className="form-label">Nome completo</label>
                        <input className="form-input" placeholder="João da Silva" value={form.nome_completo} onChange={set('nome_completo')} required />
                    </div>
                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Telefone</label>
                            <input className="form-input" placeholder="(11) 99999-9999" value={form.telefone} onChange={set('telefone')} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">WhatsApp</label>
                            <input className="form-input" placeholder="(11) 99999-9999" value={form.whatsapp} onChange={set('whatsapp')} />
                        </div>
                    </div>
                    <div className="form-group">
                        <label className="form-label">Email</label>
                        <input className="form-input" type="email" placeholder="seu@email.com" value={form.email} onChange={set('email')} required />
                    </div>
                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Senha</label>
                            <input className="form-input" type="password" placeholder="mín. 6 caracteres" value={form.password} onChange={set('password')} required />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Confirmar senha</label>
                            <input className="form-input" type="password" placeholder="••••••••" value={form.confirm_password} onChange={set('confirm_password')} required />
                        </div>
                    </div>

                    <div className="auth-divider">Endereço</div>

                    {/* Endereço com ViaCEP */}
                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">CEP {loadingCep && <span style={{ color: 'var(--brand-500)' }}>buscando...</span>}</label>
                            <input className="form-input" placeholder="00000-000" value={form.cep}
                                onChange={set('cep')} onBlur={handleCepBlur} maxLength={9} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Número</label>
                            <input className="form-input" placeholder="123" value={form.numero} onChange={set('numero')} />
                        </div>
                    </div>
                    <div className="form-group">
                        <label className="form-label">Logradouro</label>
                        <input className="form-input" placeholder="Preenchido automaticamente" value={form.logradouro} onChange={set('logradouro')} />
                    </div>
                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Bairro</label>
                            <input className="form-input" value={form.bairro} onChange={set('bairro')} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Complemento</label>
                            <input className="form-input" placeholder="Apto, sala..." value={form.complemento} onChange={set('complemento')} />
                        </div>
                    </div>
                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Cidade</label>
                            <input className="form-input" value={form.cidade} onChange={set('cidade')} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Estado</label>
                            <input className="form-input" maxLength={2} value={form.estado} onChange={set('estado')} />
                        </div>
                    </div>

                    <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: '0.5rem' }}>
                        {loading ? <><span className="spinner" /> Criando conta...</> : 'Criar conta'}
                    </button>
                </form>

                <div className="auth-links" style={{ justifyContent: 'center', marginTop: '1rem' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Já tem uma conta? </span>
                    <Link to="/login" className="auth-link" style={{ marginLeft: '0.3rem' }}>Entrar</Link>
                </div>
            </div>
        </div>
    )
}
