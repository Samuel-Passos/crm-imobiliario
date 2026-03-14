import { useState, useEffect, useMemo } from 'react'
import { supabase } from '../../lib/supabase'
import L from 'leaflet'
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
    
    // Novos filtros
    const [precoMin, setPrecoMin] = useState('')
    const [precoMax, setPrecoMax] = useState('')
    const [buscaBairro, setBuscaBairro] = useState('')
    const [buscaCondominio, setBuscaCondominio] = useState('')
    const [quartos, setQuartos] = useState('')
    const [mostrarFiltrosAvancados, setMostrarFiltrosAvancados] = useState(false)
    const [loadingGeocode, setLoadingGeocode] = useState(false)
    const [loadingReprocess, setLoadingReprocess] = useState(false)
    const [loadingGoogle, setLoadingGoogle] = useState(false)
    const [loadingGoogleReprocess, setLoadingGoogleReprocess] = useState(false)
    const [isGeocodingRunning, setIsGeocodingRunning] = useState(false)
    
    // Novo Estado: Área visível do mapa
    const [mapBounds, setMapBounds] = useState<L.LatLngBounds | null>(null)

    useEffect(() => {
        carregarImoveis()
        
        // Polling para verificar se geocodificador está rodando
        const interval = setInterval(async () => {
            try {
                const res = await fetch('http://localhost:8765/geocode/status')
                const data = await res.json()
                setIsGeocodingRunning(data.running)
            } catch (err) {
                // Silencie erro de polling se o servidor estiver offline
            }
        }, 3000)
        
        return () => clearInterval(interval)
    }, [])

    async function carregarImoveis() {
        setLoading(true)
        const { data, error } = await supabase
            .from('imoveis')
            .select('*')
            .not('latitude', 'is', null)
            .not('longitude', 'is', null)
            .limit(50000)

        if (error) {
            toast.error('Erro ao carregar mapa')
        } else {
            setImoveis(data as ImovelKanban[])
        }
        setLoading(false)
    }

    const handleRunGeocoder = async () => {
        setLoadingGeocode(true)
        try {
            const response = await fetch('http://localhost:8765/geocode', { method: 'POST' })
            const data = await response.json()
            if (response.ok) {
                toast.success('Buscando coordenadas em background!', { duration: 5000 })
                setIsGeocodingRunning(true)
            } else {
                toast.error(`Falha ao iniciar geocoder: ${data.message}`)
            }
        } catch (error) {
            toast.error('Falha de conexão. O servidor do scraper (FastAPI) está rodando?')
        }
        setTimeout(() => setLoadingGeocode(false), 2000)
    }

    const handleRunReprocess = async () => {
        setLoadingReprocess(true)
        try {
            const response = await fetch('http://localhost:8765/geocode/reprocess', { method: 'POST' })
            const data = await response.json()
            if (response.ok) {
                toast.success('Reprocessando coordenadas imprecisas em background!', { duration: 5000 })
                setIsGeocodingRunning(true)
            } else {
                toast.error(`Falha ao reprocessar: ${data.message}`)
            }
        } catch (error) {
            toast.error('Falha de conexão. O servidor do scraper está rodando?')
        }
        setTimeout(() => setLoadingReprocess(false), 2000)
    }

    const handleRunGoogleGeocoder = async () => {
        setLoadingGoogle(true)
        try {
            const response = await fetch('http://localhost:8765/geocode/google', { method: 'POST' })
            const data = await response.json()
            if (response.ok) {
                toast.success('🗺️ Google Maps: buscando coordenadas em background!', { duration: 5000 })
                setIsGeocodingRunning(true)
            } else {
                toast.error(`Falha ao iniciar Google Geocoder: ${data.message}`)
            }
        } catch (error) {
            toast.error('Falha de conexão. O servidor do scraper (FastAPI) está rodando?')
        }
        setTimeout(() => setLoadingGoogle(false), 2000)
    }

    const handleRunGoogleReprocess = async () => {
        setLoadingGoogleReprocess(true)
        try {
            const response = await fetch('http://localhost:8765/geocode/google/reprocess', { method: 'POST' })
            const data = await response.json()
            if (response.ok) {
                toast.success('🗺️ Google Maps: reprocessando imóveis imprecisos em background!', { duration: 5000 })
                setIsGeocodingRunning(true)
            } else {
                toast.error(`Falha: ${data.message}`)
            }
        } catch (error) {
            toast.error('Falha de conexão. O servidor do scraper está rodando?')
        }
        setTimeout(() => setLoadingGoogleReprocess(false), 2000)
    }

    const handleStopGeocode = async () => {
        try {
            const response = await fetch('http://localhost:8765/geocode/stop', { method: 'POST' })
            if (response.ok) {
                toast.success('Sinal de parada enviado. O robô parará após o item atual.')
            }
        } catch (error) {
            toast.error('Erro ao tentar parar geocodificador.')
        }
    }

    const filtrados = imoveis.filter(im => {
        if (tipoNegocio && im.tipo_negocio !== tipoNegocio) return false
        
        if (precoMin) {
            const min = parseFloat(precoMin.replace(/\D/g, ''))
            if (!isNaN(min) && (im.preco || 0) < min) return false
        }
        if (precoMax) {
            const max = parseFloat(precoMax.replace(/\D/g, ''))
            if (!isNaN(max) && (im.preco || 0) > max) return false
        }
        if (buscaBairro) {
            const q = buscaBairro.toLowerCase()
            if (!(im.bairro || '').toLowerCase().includes(q)) return false
        }
        if (buscaCondominio) {
            const q = buscaCondominio.toLowerCase()
            if (!(im.nome_condominio || '').toLowerCase().includes(q)) return false
        }
        if (quartos) {
            const qts = parseInt(quartos, 10)
            if (!isNaN(qts) && (im.quartos || 0) < qts) return false
        }

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

    // Imóveis que vão para a lista lateral (limitados aos que estão dentro da tela atual)
    const imoveisVisiveis = useMemo(() => {
        if (!mapBounds) return filtrados.slice(0, 50) // Fallback inicial caso não tenha bound ainda

        const visiveis = filtrados.filter(im => {
            if (im.latitude == null || im.longitude == null) return false
            const pt = L.latLng(im.latitude, im.longitude)
            return mapBounds.contains(pt)
        })

        return visiveis.slice(0, 50) // Limita a 50 na lista por performance
    }, [filtrados, mapBounds])

    const mapPoints = filtrados.map(im => ({
        id: im.id,
        lat: im.latitude!,
        lng: im.longitude!,
        onMarkerClick: () => setImovelSelecionado(im),
        tooltipContent: (
            <div style={{ minWidth: 200, maxWidth: 240 }}>
                {im.foto_capa && (
                    <img
                        src={im.foto_capa}
                        alt=""
                        style={{ width: '100%', height: 100, objectFit: 'cover', borderRadius: '6px 6px 0 0', display: 'block', margin: '-8px -10px 8px -10px', width: 'calc(100% + 20px)' }}
                    />
                )}
                <div style={{ fontWeight: 700, fontSize: '0.82rem', lineHeight: 1.3, marginBottom: 3, color: '#1a1a2e' }}>
                    {im.titulo}
                </div>
                <div style={{ fontSize: '0.72rem', color: '#666', marginBottom: 4 }}>
                    📍 {im.bairro || im.cidade || '—'}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 }}>
                    <div style={{ fontWeight: 800, color: '#6366f1', fontSize: '0.85rem' }}>
                        {im.preco ? `R$ ${im.preco.toLocaleString('pt-BR')}` : 'Preço sob consulta'}
                    </div>
                    {im.quartos && (
                        <div style={{ fontSize: '0.68rem', background: '#f0f0f5', padding: '2px 7px', borderRadius: 4, color: '#555' }}>
                            🛏 {im.quartos} qto{im.quartos > 1 ? 's' : ''}
                        </div>
                    )}
                </div>
                <div style={{ marginTop: 8, fontSize: '0.68rem', color: '#888', textAlign: 'center' }}>
                    Clique para ver detalhes →
                </div>
            </div>
        )
    }))

    return (
        <div style={{ padding: '1.5rem', maxWidth: 1400, margin: '0 auto', width: '100%', height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
            {/* Header / Filtros */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: mostrarFiltrosAvancados ? '0.5rem' : '1rem', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Mapa de Imóveis</h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                        Visualizando {filtrados.length} imóveis com localização
                    </p>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', flex: 1, justifyContent: 'flex-end', alignItems: 'center', minWidth: 300, flexWrap: 'wrap' }}>
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
                    
                    <button 
                        className="btn"
                        onClick={() => setMostrarFiltrosAvancados(!mostrarFiltrosAvancados)}
                        style={{ 
                            background: mostrarFiltrosAvancados ? 'var(--brand-500)' : 'var(--bg-surface)', 
                            color: mostrarFiltrosAvancados ? '#fff' : 'var(--text-primary)',
                            border: '1px solid',
                            borderColor: mostrarFiltrosAvancados ? 'var(--brand-500)' : 'var(--border)',
                            padding: '0.5rem 1rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                        </svg>
                        Filtros
                    </button>

                    <button
                        className="btn"
                        onClick={handleRunGeocoder}
                        disabled={loadingGeocode}
                        style={{
                            background: 'var(--bg-surface)',
                            color: 'var(--brand-500)',
                            border: '1px solid var(--brand-500)',
                            padding: '0.5rem 1rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            transition: 'all 0.2s',
                        }}
                        onMouseOver={(e) => { e.currentTarget.style.background = 'var(--brand-500)'; e.currentTarget.style.color = '#fff' }}
                        onMouseOut={(e) => { e.currentTarget.style.background = 'var(--bg-surface)'; e.currentTarget.style.color = 'var(--brand-500)' }}
                    >
                        {loadingGeocode ? <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> : <span>📍</span>}
                        Buscar Coordenadas
                    </button>

                    <button
                        className="btn"
                        onClick={handleRunReprocess}
                        disabled={loadingReprocess}
                        title="Melhora pinos que estão no centro do bairro para nível de rua"
                        style={{
                            background: 'var(--bg-surface)',
                            color: 'var(--warning, #f59e0b)',
                            border: '1px solid var(--warning, #f59e0b)',
                            padding: '0.5rem 1rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            transition: 'all 0.2s',
                        }}
                        onMouseOver={(e) => { e.currentTarget.style.background = 'var(--warning, #f59e0b)'; e.currentTarget.style.color = '#fff' }}
                        onMouseOut={(e) => { e.currentTarget.style.background = 'var(--bg-surface)'; e.currentTarget.style.color = 'var(--warning, #f59e0b)' }}
                    >
                        {loadingReprocess ? <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> : <span>♻️</span>}
                        Reprocessar Coords
                    </button>

                    <button
                        className="btn"
                        onClick={handleRunGoogleGeocoder}
                        disabled={loadingGoogle}
                        title="Google Maps: geocodificar imóveis sem coordenadas"
                        style={{
                            background: 'var(--bg-surface)',
                            color: '#10b981',
                            border: '1px solid #10b981',
                            padding: '0.5rem 1rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            transition: 'all 0.2s',
                        }}
                        onMouseOver={(e) => { e.currentTarget.style.background = '#10b981'; e.currentTarget.style.color = '#fff' }}
                        onMouseOut={(e) => { e.currentTarget.style.background = 'var(--bg-surface)'; e.currentTarget.style.color = '#10b981' }}
                    >
                        {loadingGoogle ? <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> : <span>🗺️</span>}
                        Google (novos)
                    </button>

                    <button
                        className="btn"
                        onClick={handleRunGoogleReprocess}
                        disabled={loadingGoogleReprocess}
                        title="Google Maps: reprocessar imóveis com geocode_needs_review=true"
                        style={{
                            background: 'var(--bg-surface)',
                            color: '#06b6d4',
                            border: '1px solid #06b6d4',
                            padding: '0.5rem 1rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            transition: 'all 0.2s',
                        }}
                        onMouseOver={(e) => { e.currentTarget.style.background = '#06b6d4'; e.currentTarget.style.color = '#fff' }}
                        onMouseOut={(e) => { e.currentTarget.style.background = 'var(--bg-surface)'; e.currentTarget.style.color = '#06b6d4' }}
                    >
                        {loadingGoogleReprocess ? <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> : <span>🔄</span>}
                        Google (revisão)
                    </button>

                    {isGeocodingRunning && (
                        <button
                            className="btn"
                            onClick={handleStopGeocode}
                            style={{
                                background: '#fee2e2',
                                color: '#b91c1c',
                                border: '1px solid #f87171',
                                padding: '0.5rem 1rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                fontWeight: 600
                            }}
                        >
                            <span style={{ fontSize: '1.1rem' }}>🛑</span>
                            Cancelar
                        </button>
                    )}
                </div>
            </div>

            {/* Filtros Avançados (Expansível) */}
            {mostrarFiltrosAvancados && (
                <div style={{ 
                    display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap', 
                    background: 'var(--bg-surface)', padding: '1rem', borderRadius: 'var(--radius-md)', 
                    border: '1px solid var(--border)',
                    animation: 'fadeIn 0.2s ease-out'
                }}>
                    <div style={{ flex: 1, minWidth: 150 }}>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Preço Mín (R$)</label>
                        <input
                            className="form-input"
                            type="number"
                            placeholder="Ex: 100000"
                            value={precoMin}
                            onChange={e => setPrecoMin(e.target.value)}
                            style={{ width: '100%' }}
                        />
                    </div>
                    <div style={{ flex: 1, minWidth: 150 }}>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Preço Máx (R$)</label>
                        <input
                            className="form-input"
                            type="number"
                            placeholder="Ex: 500000"
                            value={precoMax}
                            onChange={e => setPrecoMax(e.target.value)}
                            style={{ width: '100%' }}
                        />
                    </div>
                    <div style={{ flex: 2, minWidth: 200 }}>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Bairro</label>
                        <input
                            className="form-input"
                            placeholder="Ex: Centro"
                            value={buscaBairro}
                            onChange={e => setBuscaBairro(e.target.value)}
                            style={{ width: '100%' }}
                        />
                    </div>
                    <div style={{ flex: 2, minWidth: 200 }}>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Condomínio</label>
                        <input
                            className="form-input"
                            placeholder="Nome do condomínio"
                            value={buscaCondominio}
                            onChange={e => setBuscaCondominio(e.target.value)}
                            style={{ width: '100%' }}
                        />
                    </div>
                    <div style={{ flex: 1, minWidth: 120 }}>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Dormitórios</label>
                        <select
                            className="form-select"
                            value={quartos}
                            onChange={e => setQuartos(e.target.value)}
                            style={{ width: '100%' }}
                        >
                            <option value="">Qualquer</option>
                            <option value="1">1+ quarto</option>
                            <option value="2">2+ quartos</option>
                            <option value="3">3+ quartos</option>
                            <option value="4">4+ quartos</option>
                            <option value="5">5+ quartos</option>
                        </select>
                    </div>
                    {(precoMin || precoMax || buscaBairro || buscaCondominio || quartos) && (
                        <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: '2px' }}>
                            <button 
                                onClick={() => {
                                    setPrecoMin('')
                                    setPrecoMax('')
                                    setBuscaBairro('')
                                    setBuscaCondominio('')
                                    setQuartos('')
                                }}
                                style={{ 
                                    background: 'transparent', color: 'var(--text-muted)', 
                                    border: 'none', cursor: 'pointer', fontSize: '0.85rem',
                                    textDecoration: 'underline'
                                }}
                            >
                                Limpar
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Main Area: Mapa + Lista Lateral */}
            <div style={{ flex: 1, display: 'flex', gap: '1rem', overflow: 'hidden', minHeight: 0 }}>
                {/* Mapa */}
                <div style={{ flex: 3, position: 'relative', minWidth: 0 }}>
                    {loading ? (
                        <div className="loading-screen" style={{ position: 'absolute', inset: 0, zIndex: 10, background: 'rgba(10,14,26,0.5)' }}>
                            <div className="spinner" />
                        </div>
                    ) : (
                        <MapView points={mapPoints} height="100%" onBoundsChange={setMapBounds} />
                    )}
                </div>

                {/* Lista Lateral (Sidebar) */}
                <div style={{
                    width: '340px',
                    minWidth: '300px',
                    maxWidth: '380px',
                    display: 'flex',
                    flexDirection: 'column',
                    background: 'var(--bg-surface)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border)',
                    overflow: 'hidden',
                    height: '100%',
                }}>
                    {/* Header fixo */}
                    <div style={{
                        padding: '0.85rem 1rem',
                        borderBottom: '1px solid var(--border)',
                        background: 'var(--bg-card)',
                        flexShrink: 0,
                    }}>
                        <h2 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0 }}>
                            Imóveis na Tela ({imoveisVisiveis.length})
                        </h2>
                        <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: 0, marginTop: '2px' }}>
                            {imoveisVisiveis.length > 50 ? 'Mostrando os 50 principais deste recorte' : 'Role para ver todos os imóveis'}
                        </p>
                    </div>

                    {/* Lista com scroll */}
                    <div style={{
                        flex: 1,
                        overflowY: 'auto',
                        overflowX: 'hidden',
                        padding: '0.6rem',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.5rem',
                    }}>
                        {imoveisVisiveis.length === 0 && (
                            <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', padding: '3rem 1rem' }}>
                                Nenhum imóvel encontrado nesta área ou filtro.
                            </div>
                        )}
                        {imoveisVisiveis.map(im => (
                            <div
                                key={im.id}
                                onClick={() => setImovelSelecionado(im)}
                                style={{
                                    border: '1px solid var(--border)',
                                    borderRadius: 'var(--radius-md)',
                                    cursor: 'pointer',
                                    background: 'var(--bg-card)',
                                    transition: 'border-color 0.18s, box-shadow 0.18s',
                                    overflow: 'hidden',
                                    display: 'flex',
                                    height: '88px',         // altura fixa — evita compressão
                                    minHeight: '88px',
                                    flexShrink: 0,          // nunca encolher
                                }}
                                onMouseOver={(e) => {
                                    e.currentTarget.style.borderColor = 'var(--brand-500)'
                                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(99,102,241,0.12)'
                                }}
                                onMouseOut={(e) => {
                                    e.currentTarget.style.borderColor = 'var(--border)'
                                    e.currentTarget.style.boxShadow = 'none'
                                }}
                            >
                                {/* Foto */}
                                <div style={{
                                    width: '88px',
                                    minWidth: '88px',
                                    height: '88px',
                                    background: 'var(--bg-surface)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    overflow: 'hidden',
                                    flexShrink: 0,
                                }}>
                                    {im.foto_capa ? (
                                        <img
                                            src={im.foto_capa}
                                            alt=""
                                            style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                                        />
                                    ) : (
                                        <span style={{ fontSize: '1.6rem', opacity: 0.4 }}>🏠</span>
                                    )}
                                </div>

                                {/* Info */}
                                <div style={{
                                    padding: '0.5rem 0.6rem',
                                    flex: 1,
                                    minWidth: 0,
                                    display: 'flex',
                                    flexDirection: 'column',
                                    justifyContent: 'space-between',
                                }}>
                                    {/* Título */}
                                    <div style={{
                                        fontWeight: 600,
                                        fontSize: '0.8rem',
                                        lineHeight: 1.3,
                                        overflow: 'hidden',
                                        display: '-webkit-box',
                                        WebkitLineClamp: 2,
                                        WebkitBoxOrient: 'vertical',
                                        color: 'var(--text-primary)',
                                    }}>
                                        {im.titulo}
                                    </div>

                                    {/* Bairro */}
                                    <div style={{
                                        fontSize: '0.7rem',
                                        color: 'var(--text-muted)',
                                        whiteSpace: 'nowrap',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                    }}>
                                        📍 {im.bairro || im.cidade || '—'}
                                    </div>

                                    {/* Preço + quartos */}
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ fontWeight: 700, color: 'var(--brand-500)', fontSize: '0.82rem' }}>
                                            {im.preco ? `R$ ${im.preco.toLocaleString('pt-BR')}` : 'S/ Preço'}
                                        </div>
                                        {im.quartos && (
                                            <div style={{
                                                fontSize: '0.65rem',
                                                background: 'var(--bg-surface)',
                                                padding: '1px 6px',
                                                borderRadius: '4px',
                                                border: '1px solid var(--border)',
                                                color: 'var(--text-muted)',
                                                whiteSpace: 'nowrap',
                                            }}>
                                                🛏 {im.quartos} qto{im.quartos > 1 ? 's' : ''}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
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
