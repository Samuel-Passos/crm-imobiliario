import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import type { Contato, TipoContato } from './types'
import { TIPO_CONTATO_LABELS, TIPO_CONTATO_CORES } from './types'
import { ContatoModal } from './ContatoModal'
import toast from 'react-hot-toast'

const TIPOS_FILTRO: Array<{ value: '' | TipoContato; label: string }> = [
    { value: '', label: 'Todos os tipos' },
    { value: 'proprietario', label: '🏠 Proprietário' },
    { value: 'comprador', label: '💰 Comprador' },
    { value: 'inquilino', label: '🔑 Inquilino' },
    { value: 'parceiro', label: '🤝 Parceiro' },
    { value: 'outro', label: '👤 Outro' },
]

export function ContatosPage() {
    const [contatos, setContatos] = useState<Contato[]>([])
    const [loading, setLoading] = useState(true)
    const [busca, setBusca] = useState('')
    const [tipoFiltro, setTipoFiltro] = useState<'' | TipoContato>('')
    const [modalAberto, setModalAberto] = useState(false)
    const [contatoSelecionado, setContatoSelecionado] = useState<Contato | null>(null)
    const [deletando, setDeletando] = useState<string | null>(null)

    useEffect(() => {
        carregarContatos()
    }, [])

    async function carregarContatos() {
        setLoading(true)
        const { data, error } = await supabase
            .from('contatos')
            .select('*')
            .order('nome_completo', { ascending: true })

        if (error) {
            toast.error('Erro ao carregar contatos')
        } else {
            setContatos(data as Contato[])
        }
        setLoading(false)
    }

    function handleNovo() {
        setContatoSelecionado(null)
        setModalAberto(true)
    }

    function handleEditar(c: Contato) {
        setContatoSelecionado(c)
        setModalAberto(true)
    }

    function handleSaved(c: Contato) {
        setContatos(prev => {
            const existe = prev.find(x => x.id === c.id)
            if (existe) return prev.map(x => x.id === c.id ? c : x)
            return [c, ...prev].sort((a, b) => a.nome_completo.localeCompare(b.nome_completo))
        })
    }

    async function handleDeletar(c: Contato) {
        if (!confirm(`Remover o contato "${c.nome_completo}"?`)) return
        setDeletando(c.id)
        const { error } = await supabase.from('contatos').delete().eq('id', c.id)
        if (error) {
            toast.error('Erro ao remover')
        } else {
            setContatos(prev => prev.filter(x => x.id !== c.id))
            toast.success('Contato removido')
        }
        setDeletando(null)
    }

    // Filtros locais (rápido, sem nova query)
    const filtrado = contatos.filter(c => {
        if (tipoFiltro && c.tipo_contato !== tipoFiltro) return false
        if (busca) {
            const q = busca.toLowerCase()
            return (
                c.nome_completo.toLowerCase().includes(q) ||
                (c.cidade || '').toLowerCase().includes(q) ||
                (c.telefone || '').includes(q) ||
                (c.email || '').toLowerCase().includes(q)
            )
        }
        return true
    })

    function waLink(c: Contato) {
        const numero = (c.whatsapp || c.telefone || '').replace(/\D/g, '')
        return numero ? `https://wa.me/55${numero}` : null
    }

    return (
        <div style={{ padding: '1.5rem', maxWidth: 1100, margin: '0 auto', width: '100%' }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '0.1rem' }}>Contatos</h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                        {filtrado.length} de {contatos.length} contato{contatos.length !== 1 ? 's' : ''}
                    </p>
                </div>
                <button className="btn btn-primary" onClick={handleNovo} style={{ width: 'auto', padding: '0.75rem 1.25rem' }}>
                    + Novo Contato
                </button>
            </div>

            {/* Filtros */}
            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
                <input
                    className="form-input"
                    value={busca}
                    onChange={e => setBusca(e.target.value)}
                    placeholder="🔍 Buscar por nome, cidade, telefone ou e-mail..."
                    style={{ flex: 1, minWidth: 220 }}
                />
                <select className="form-select" value={tipoFiltro} onChange={e => setTipoFiltro(e.target.value as typeof tipoFiltro)}
                    style={{ width: 'auto', minWidth: 180 }}>
                    {TIPOS_FILTRO.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
                {(busca || tipoFiltro) && (
                    <button onClick={() => { setBusca(''); setTipoFiltro('') }}
                        style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-muted)', cursor: 'pointer', padding: '0 0.75rem', fontSize: '0.85rem' }}>
                        Limpar
                    </button>
                )}
            </div>

            {/* Lista */}
            {loading ? (
                <div className="loading-screen"><div className="spinner" /></div>
            ) : filtrado.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '4rem 1rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border)' }}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>👥</div>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                        {contatos.length === 0 ? 'Nenhum contato cadastrado' : 'Nenhum resultado encontrado'}
                    </h3>
                    {contatos.length === 0 && (
                        <button className="btn btn-primary" onClick={handleNovo} style={{ width: 'auto', marginTop: '1rem' }}>
                            + Adicionar primeiro contato
                        </button>
                    )}
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
                    {filtrado.map(c => (
                        <div key={c.id} style={{
                            background: 'var(--bg-card)', border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-md)', padding: '1.25rem',
                            transition: 'border-color 200ms, transform 150ms',
                        }}
                            onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(59,130,246,0.4)')}
                            onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
                        >
                            {/* Topo do card */}
                            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                                <div>
                                    <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                                        {c.nome_completo}
                                    </div>
                                    <span style={{
                                        fontSize: '0.7rem', fontWeight: 600,
                                        color: TIPO_CONTATO_CORES[c.tipo_contato],
                                        background: `${TIPO_CONTATO_CORES[c.tipo_contato]}18`,
                                        padding: '0.15rem 0.5rem', borderRadius: 99
                                    }}>
                                        {TIPO_CONTATO_LABELS[c.tipo_contato]}
                                    </span>
                                </div>
                                {/* Acções */}
                                <div style={{ display: 'flex', gap: '0.3rem' }}>
                                    <button onClick={() => handleEditar(c)}
                                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '0.9rem', padding: '0.2rem 0.4rem' }}
                                        title="Editar">✏️</button>
                                    <button onClick={() => handleDeletar(c)} disabled={deletando === c.id}
                                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--error)', fontSize: '0.9rem', padding: '0.2rem 0.4rem' }}
                                        title="Remover">🗑️</button>
                                </div>
                            </div>

                            {/* Localização */}
                            {(c.cidade || c.logradouro) && (
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                                    📍 {[c.logradouro, c.numero, c.bairro, c.cidade, c.estado].filter(Boolean).join(', ')}
                                </div>
                            )}

                            {/* Contatos */}
                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
                                {c.telefone && (
                                    <a href={`tel:${c.telefone.replace(/\D/g, '')}`}
                                        style={{ fontSize: '0.78rem', color: 'var(--brand-500)', textDecoration: 'none', background: 'rgba(59,130,246,0.1)', padding: '0.25rem 0.6rem', borderRadius: 99 }}>
                                        📞 {c.telefone}
                                    </a>
                                )}
                                {waLink(c) && (
                                    <a href={waLink(c)!} target="_blank" rel="noopener noreferrer"
                                        style={{ fontSize: '0.78rem', color: '#4ade80', textDecoration: 'none', background: 'rgba(74,222,128,0.1)', padding: '0.25rem 0.6rem', borderRadius: 99 }}>
                                        💬 WhatsApp
                                    </a>
                                )}
                                {c.email && (
                                    <a href={`mailto:${c.email}`}
                                        style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textDecoration: 'none', background: 'rgba(255,255,255,0.05)', padding: '0.25rem 0.6rem', borderRadius: 99 }}>
                                        ✉️ {c.email}
                                    </a>
                                )}
                            </div>

                            {/* Notas preview */}
                            {c.notas && (
                                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                                    📝 {c.notas}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Modal */}
            {modalAberto && (
                <ContatoModal
                    contato={contatoSelecionado}
                    onClose={() => setModalAberto(false)}
                    onSaved={handleSaved}
                />
            )}
        </div>
    )
}
