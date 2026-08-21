import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import type { Contato, TipoContato } from './types'
import { TIPO_CONTATO_LABELS, TIPO_CONTATO_CORES } from './types'
import { ContatoModal } from './ContatoModal'
import { ContatosMapa } from './ContatosMapa'
import toast from 'react-hot-toast'

const TIPOS_FILTRO: Array<{ value: '' | TipoContato; label: string }> = [
    { value: '', label: 'Todos os tipos' },
    { value: 'proprietario', label: '🏠 Proprietário' },
    { value: 'comprador', label: '💰 Comprador' },
    { value: 'inquilino', label: '🔑 Inquilino' },
    { value: 'parceiro', label: '🤝 Parceiro' },
    { value: 'porteiro', label: '🏢 Porteiro' },
    { value: 'sindico', label: '👔 Síndico' },
    { value: 'servicos_gerais', label: '🧹 Serviços Gerais' },
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
    const [viewMode, setViewMode] = useState<'list' | 'map'>('list')

    useEffect(() => {
        carregarContatos()
    }, [])

    async function carregarContatos() {
        setLoading(true)
        const { data, error } = await supabase
            .from('contatos')
            .select('*')
            .order('created_at', { ascending: false })

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
            return [c, ...prev]
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

    const filtrado = contatos.filter(c => {
        if (tipoFiltro && c.tipo_contato !== tipoFiltro) return false
        if (busca) {
            const q = busca.toLowerCase()
            return (
                c.nome_completo.toLowerCase().includes(q) ||
                (c.cidade || '').toLowerCase().includes(q) ||
                (c.telefone || '').includes(q)
            )
        }
        return true
    })

    function waLink(c: Contato) {
        const numero = (c.whatsapp || c.telefone || '').replace(/\D/g, '')
        if (!numero) return null
        const telFormatado = numero.startsWith('55') ? numero : `55${numero}`
        return `https://wa.me/${telFormatado}`
    }

    return (
        <div style={{ padding: '2rem', maxWidth: 1200, margin: '0 auto' }}>
            {/* Header com Estilo Premium */}
            <header style={{ 
                marginBottom: '2rem', display: 'flex', alignItems: 'flex-end', 
                justifyContent: 'space-between', flexWrap: 'wrap', gap: '1.5rem' 
            }}>
                <div>
                    <h1 style={{ fontSize: '2.5rem', fontWeight: 900, letterSpacing: '-0.02em', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                        Lista Fria
                    </h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '1rem', fontWeight: 500 }}>
                        Gerencie e prospecte novos leads na sua base de dados
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <div style={{ display: 'flex', background: 'var(--bg-card)', padding: '4px', borderRadius: '12px', border: '1px solid var(--border)' }}>
                        <button onClick={() => setViewMode('list')} style={{ 
                            padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                            background: viewMode === 'list' ? 'var(--brand-500)' : 'transparent',
                            color: viewMode === 'list' ? 'white' : 'var(--text-muted)',
                            fontWeight: 700, transition: 'all 0.2s'
                        }}>Lista</button>
                        <button onClick={() => setViewMode('map')} style={{ 
                            padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                            background: viewMode === 'map' ? 'var(--brand-500)' : 'transparent',
                            color: viewMode === 'map' ? 'white' : 'var(--text-muted)',
                            fontWeight: 700, transition: 'all 0.2s'
                        }}>Mapa</button>
                    </div>
                    <button onClick={handleNovo} className="btn btn-primary" style={{ padding: '0 1.5rem', height: 44, borderRadius: 12 }}>
                        + Novo Lead
                    </button>
                </div>
            </header>

            {/* Filtros Modernos */}
            <div style={{ 
                display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) auto auto', 
                gap: '1rem', marginBottom: '2.5rem', alignItems: 'center' 
            }}>
                <div style={{ position: 'relative' }}>
                    <input 
                        className="form-input" 
                        value={busca} 
                        onChange={e => setBusca(e.target.value)}
                        placeholder="Pesquisar por nome, cidade ou telefone..."
                        style={{ paddingLeft: '2.5rem', height: 48, borderRadius: 14 }}
                    />
                    <span style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', opacity: 0.5 }}>🔍</span>
                </div>
                <select 
                    className="form-select" 
                    value={tipoFiltro} 
                    onChange={e => setTipoFiltro(e.target.value as any)}
                    style={{ height: 48, borderRadius: 14, minWidth: 200 }}
                >
                    {TIPOS_FILTRO.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                    {filtrado.length} contatos encontrados
                </div>
            </div>

            {loading ? (
                <div style={{ padding: '5rem', textAlign: 'center' }}><div className="spinner" /></div>
            ) : viewMode === 'map' ? (
                <ContatosMapa contatos={filtrado} onEditar={handleEditar} />
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
                    {filtrado.map((c, idx) => (
                        <div key={c.id} style={{ 
                            background: 'var(--bg-card)', borderRadius: '20px', border: '1px solid var(--border)',
                            padding: '1.5rem', position: 'relative', overflow: 'hidden',
                            animation: `fadeSlideUp 0.4s ease forwards ${idx * 0.05}s`, opacity: 0,
                            boxShadow: '0 4px 12px rgba(0,0,0,0.03)'
                        }}>
                            {/* Accent line */}
                            <div style={{ 
                                position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', 
                                background: TIPO_CONTATO_CORES[c.tipo_contato] || 'var(--brand-500)'
                            }} />

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                                <div>
                                    <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                                        {c.nome_completo}
                                    </h3>
                                    <span style={{ 
                                        fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase',
                                        color: TIPO_CONTATO_CORES[c.tipo_contato], background: `${TIPO_CONTATO_CORES[c.tipo_contato]}15`,
                                        padding: '4px 10px', borderRadius: '8px'
                                    }}>
                                        {TIPO_CONTATO_LABELS[c.tipo_contato]}
                                    </span>
                                </div>
                                <div style={{ display: 'flex', gap: '0.25rem' }}>
                                    <button onClick={() => handleEditar(c)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '6px' }}>✏️</button>
                                    <button onClick={() => handleDeletar(c)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '6px' }}>🗑️</button>
                                </div>
                            </div>

                            <div style={{ spaceY: '0.75rem', marginBottom: '1.5rem' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                                    <span style={{ opacity: 0.6 }}>📞</span> {c.telefone || 'Sem telefone'}
                                </div>
                                {c.email && (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.9rem', color: 'var(--text-primary)', marginTop: '0.5rem' }}>
                                        <span style={{ opacity: 0.6 }}>📧</span> {c.email}
                                    </div>
                                )}
                                {c.cidade && (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                                        <span style={{ opacity: 0.6 }}>📍</span> {c.cidade}
                                    </div>
                                )}
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                                <a 
                                    href={waLink(c) || '#'} 
                                    target="_blank" 
                                    rel="noreferrer" 
                                    style={{ 
                                        padding: '10px', borderRadius: '12px', background: '#25D366', 
                                        color: 'white', textDecoration: 'none', textAlign: 'center',
                                        fontSize: '0.85rem', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem'
                                    }}
                                >
                                    💬 WhatsApp
                                </a>
                                <a 
                                    href={`tel:${c.telefone?.replace(/\D/g, '')}`}
                                    style={{ 
                                        padding: '10px', borderRadius: '12px', background: 'var(--brand-500)', 
                                        color: 'white', textDecoration: 'none', textAlign: 'center',
                                        fontSize: '0.85rem', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem'
                                    }}
                                >
                                    📞 Ligar
                                </a>
                            </div>

                            {c.notas && (
                                <div style={{ 
                                    marginTop: '1.25rem', padding: '10px', borderRadius: '12px', 
                                    background: 'var(--bg-app)', fontSize: '0.8rem', color: 'var(--text-muted)',
                                    fontStyle: 'italic', border: '1px solid var(--border)'
                                }}>
                                    "{c.notas}"
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {modalAberto && (
                <ContatoModal 
                    contato={contatoSelecionado} 
                    onClose={() => setModalAberto(false)} 
                    onSaved={handleSaved} 
                />
            )}

            {/* Estilos Globais para Estar Página */}
            <style>{`
                @keyframes fadeSlideUp {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    )
}
