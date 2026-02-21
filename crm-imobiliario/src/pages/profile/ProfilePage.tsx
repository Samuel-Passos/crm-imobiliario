import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

interface ViaCEPResponse {
    logradouro: string; bairro: string; localidade: string; uf: string; erro?: boolean
}

export function ProfilePage() {
    const { profile, updateProfile } = useAuth()
    const [loading, setLoading] = useState(false)
    const [loadingCep, setLoadingCep] = useState(false)

    const [form, setForm] = useState({
        nome_completo: '', telefone: '', whatsapp: '', email: '',
        cep: '', logradouro: '', numero: '', complemento: '',
        bairro: '', cidade: '', estado: ''
    })

    useEffect(() => {
        if (profile) {
            setForm({
                nome_completo: profile.nome_completo || '',
                telefone: profile.telefone || '',
                whatsapp: profile.whatsapp || '',
                email: profile.email || '',
                cep: profile.cep || '',
                logradouro: profile.logradouro || '',
                numero: profile.numero || '',
                complemento: profile.complemento || '',
                bairro: profile.bairro || '',
                cidade: profile.cidade || '',
                estado: profile.estado || ''
            })
        }
    }, [profile])

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
                setForm(f => ({ ...f, logradouro: data.logradouro, bairro: data.bairro, cidade: data.localidade, estado: data.uf }))
            }
        } catch (_) { toast.error('Erro ao buscar CEP') }
        setLoadingCep(false)
    }

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        const { error } = await updateProfile(form)
        setLoading(false)
        if (error) toast.error('Erro ao salvar perfil.')
        else toast.success('Perfil atualizado com sucesso!')
    }

    return (
        <div style={{ maxWidth: 600 }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Meu Perfil</h1>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.9rem' }}>
                Gerencie seus dados pessoais e de contato
            </p>

            <div className="card">
                {/* Badge de role */}
                {profile && (
                    <div style={{ marginBottom: '1.5rem' }}>
                        <span className={`badge badge-${profile.role}`}>
                            {profile.role === 'admin' ? '👑 Admin'
                                : profile.role === 'corretor' ? '🏠 Corretor'
                                    : profile.role === 'secretario' ? '📋 Secretário'
                                        : '👤 Cliente'}
                        </span>
                    </div>
                )}

                <form onSubmit={handleSave}>
                    <div className="form-group">
                        <label className="form-label">Nome completo</label>
                        <input className="form-input" value={form.nome_completo} onChange={set('nome_completo')} required />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Email</label>
                        <input className="form-input" type="email" value={form.email} onChange={set('email')} />
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

                    <div style={{ borderTop: '1px solid var(--border)', margin: '1.25rem 0', paddingTop: '1rem' }}>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem' }}>Endereço</p>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">CEP {loadingCep && <span style={{ color: 'var(--brand-500)' }}>buscando...</span>}</label>
                            <input className="form-input" placeholder="00000-000" value={form.cep} onChange={set('cep')} onBlur={handleCepBlur} maxLength={9} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Número</label>
                            <input className="form-input" placeholder="123" value={form.numero} onChange={set('numero')} />
                        </div>
                    </div>
                    <div className="form-group">
                        <label className="form-label">Logradouro</label>
                        <input className="form-input" value={form.logradouro} onChange={set('logradouro')} />
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
                            <label className="form-label">Estado (UF)</label>
                            <input className="form-input" maxLength={2} value={form.estado} onChange={set('estado')} />
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                        <button type="submit" className="btn btn-primary" disabled={loading} style={{ flex: 1 }}>
                            {loading ? <><span className="spinner" /> Salvando...</> : 'Salvar alterações'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
