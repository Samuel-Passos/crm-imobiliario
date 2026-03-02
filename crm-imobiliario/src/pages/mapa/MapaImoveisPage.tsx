import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { MapView } from '../../components/MapView'
import type { ImovelKanban } from '../kanban/types'
import { ImovelModal } from '../kanban/ImovelModal'
import toast from 'react-hot-toast'

export function MapaImoveisPage() {
    const [imoveis, setImoveis] = useState<ImovelKanban[]>([])
    const [loading, setLoading] = useState(true)
    const [busca, setBusca] = useState('')
    const [tipoNegocio, setTipoNegocio] = useState<'' | 'venda' | 'aluguel'>('')
    const [imovelSelecionado, setImovelSelecionado] = useState<ImovelKanban | null>(null)

    useEffect(() => {
        carregarImoveis()
    }, [])

    async function carregarImoveis() {
        setLoading(true)
        const { data, error } = await supabase
            .from('imoveis')
            .select('*')
            .not('latitude', 'is', null)
            .not('longitude', 'is', null)

        if (error) {
            toast.error('Erro ao carregar mapa')
        } else {
            setImoveis(data as ImovelKanban[])
        }
        setLoading(false)
    }

    const filtrados = imoveis.filter(im => {
        if (tipoNegocio && im.tipo_negocio !== tipoNegocio) return false
        if (busca) {
            const q = busca.toLowerCase()
            return (
                (im.titulo || '').toLowerCase().includes(q) ||
                (im.bairro || '').toLowerCase().includes(q) ||
                (im.cidade || '').toLowerCase().includes(q)
            )
        }
        return true
    })

    const mapPoints = filtrados.map(im => ({
        id: im.id,
        lat: im.latitude!,
        lng: im.longitude!,
        popupContent: (
            <div style={{ color: '#333', minWidth: 180 }}>
                {im.foto_capa && (
                    <img src={im.foto_capa} alt="" style={{ width: '100%', height: 80, objectFit: 'cover', borderRadius: 4, marginBottom: 8 }} />
                )}
                <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: 4 }}>{im.titulo}</div>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: im.tipo_negocio === 'venda' ? 'var(--gold-500)' : '#a78bfa', marginBottom: 4 }}>
                    {im.tipo_imovel} · {im.tipo_negocio?.toUpperCase()}
                </div>
                <div style={{ fontWeight: 800, color: 'var(--brand-500)', marginBottom: 8 }}>
                    {im.preco ? `R$ ${im.preco.toLocaleString('pt-BR')}` : 'Preço sob consulta'}
                </div>
                <button
                    onClick={() => setImovelSelecionado(im)}
                    style={{
                        width: '100%', padding: '6px', fontSize: '0.75rem', cursor: 'pointer',
                        background: 'var(--brand-500)', color: '#fff', border: 'none', borderRadius: 4, fontWeight: 600
                    }}
                >
                    Ver Detalhes
                </button>
            </div>
        )
    }))

    return (
        <div style={{ padding: '1.5rem', maxWidth: 1400, margin: '0 auto', width: '100%', height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
            {/* Header / Filtros */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Mapa de Imóveis</h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                        Visualizando {filtrados.length} imóveis com localização
                    </p>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', flex: 1, justifyContent: 'flex-end', minWidth: 300 }}>
                    <input
                        className="form-input"
                        placeholder="🔍 Título, bairro ou cidade..."
                        value={busca}
                        onChange={e => setBusca(e.target.value)}
                        style={{ maxWidth: 300 }}
                    />
                    <select
                        className="form-select"
                        value={tipoNegocio}
                        onChange={e => setTipoNegocio(e.target.value as any)}
                        style={{ width: 'auto' }}
                    >
                        <option value="">Todos os negócios</option>
                        <option value="venda">Venda</option>
                        <option value="aluguel">Aluguel</option>
                    </select>
                </div>
            </div>

            {/* Mapa */}
            <div style={{ flex: 1, position: 'relative' }}>
                {loading ? (
                    <div className="loading-screen" style={{ position: 'absolute', inset: 0, zIndex: 10, background: 'rgba(10,14,26,0.5)' }}>
                        <div className="spinner" />
                    </div>
                ) : (
                    <MapView points={mapPoints} height="100%" />
                )}
            </div>

            {/* Modal */}
            {imovelSelecionado && (
                <ImovelModal
                    imovel={imovelSelecionado}
                    onClose={() => setImovelSelecionado(null)}
                    onUpdate={(u) => {
                        setImoveis(prev => prev.map(im => im.id === imovelSelecionado.id ? { ...im, ...u } : im))
                        setImovelSelecionado(null)
                    }}
                />
            )}
        </div>
    )
}
