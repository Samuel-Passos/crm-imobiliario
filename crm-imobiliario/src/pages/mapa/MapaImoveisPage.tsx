import { useState, useEffect, useMemo, useRef } from 'react'
import { supabase } from '../../lib/supabase'
import L from 'leaflet'
import { MapView } from '../../components/MapView'
import type { ImovelKanban } from '../kanban/types'
import { ImovelModal } from '../kanban/ImovelModal'
import toast from 'react-hot-toast'
import './MapaImoveisPage.css'

function MultiSelectDropdown({ 
    label, 
    options, 
    selected, 
    onChange, 
    placeholder = "Selecionar..." 
}: { 
    label: string, 
    options: string[], 
    selected: string[], 
    onChange: (values: string[]) => void,
    placeholder?: string
}) {
    const [isOpen, setIsOpen] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const containerRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const filteredOptions = useMemo(() => {
        return options.filter(opt => opt.toLowerCase().includes(searchTerm.toLowerCase()))
    }, [options, searchTerm])

    const toggleOption = (opt: string) => {
        if (selected.includes(opt)) {
            onChange(selected.filter(i => i !== opt))
        } else {
            onChange([...selected, opt])
        }
    }

    return (
        <div ref={containerRef} className="m3-dropdown-container">
            <label className="m3-label" style={{ marginBottom: '0.5rem', display: 'block' }}>{label}</label>
            <div 
                onClick={() => setIsOpen(!isOpen)}
                className={`m3-dropdown-trigger ${isOpen ? 'open' : ''}`}
            >
                <span style={{ 
                    fontSize: '0.9rem', 
                    whiteSpace: 'nowrap', 
                    overflow: 'hidden', 
                    textOverflow: 'ellipsis',
                    color: selected.length > 0 ? 'var(--m3-on-surface)' : 'var(--m3-on-surface-variant)'
                }}>
                    {selected.length === 0 ? placeholder : `${selected.length} selecionado(s)`}
                </span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </div>

            {isOpen && (
                <div className="m3-dropdown-menu">
                    <input 
                        autoFocus
                        type="text"
                        className="m3-input"
                        placeholder="Pesquisar..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        onClick={e => e.stopPropagation()}
                        style={{ height: '36px', fontSize: '0.85rem' }}
                    />
                    
                    <div className="m3-dropdown-options">
                        {filteredOptions.length === 0 && (
                            <div style={{ padding: '8px', fontSize: '0.85rem', color: 'var(--m3-on-surface-variant)', textAlign: 'center' }}>Nenhum resultado</div>
                        )}
                        {filteredOptions.map(opt => (
                            <div 
                                key={opt}
                                className={`m3-dropdown-opt ${selected.includes(opt) ? 'selected' : ''}`}
                                onClick={(e) => { e.stopPropagation(); toggleOption(opt) }}
                            >
                                <input 
                                    type="checkbox" 
                                    checked={selected.includes(opt)} 
                                    readOnly 
                                    className="m3-checkbox"
                                    style={{ margin: 0 }} 
                                />
                                <span style={{ flex: 1 }}>{opt}</span>
                            </div>
                        ))}
                    </div>

                    {selected.length > 0 && (
                        <div style={{ borderTop: '1px solid var(--m3-outline-variant)', paddingTop: '8px', display: 'flex', justifyContent: 'flex-end' }}>
                            <button 
                                onClick={(e) => { e.stopPropagation(); onChange([]) }}
                                className="m3-btn-text"
                                style={{ color: 'var(--m3-primary)' }}
                            >
                                Limpar
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}


export function MapaImoveisPage() {
    const [imoveis, setImoveis] = useState<ImovelKanban[]>([])
    const [loading, setLoading] = useState(true)
    const [busca, setBusca] = useState('')
    const [tipoNegocio, setTipoNegocio] = useState<'' | 'venda' | 'aluguel'>('')
    const [imovelSelecionado, setImovelSelecionado] = useState<ImovelKanban | null>(null)
    
    // Novos filtros
    const [precoMin, setPrecoMin] = useState('')
    const [precoMax, setPrecoMax] = useState('')
    const [quartos, setQuartos] = useState('')
    const [tipoImovel, setTipoImovel] = useState('')
    const [subtipo, setSubtipo] = useState('')
    const [condominiosSelecionados, setCondominiosSelecionados] = useState<string[]>([])
    const [bairrosSelecionados, setBairrosSelecionados] = useState<string[]>([])
    const [cidadesSelecionadas, setCidadesSelecionadas] = useState<string[]>([])
    
    const [mostrarFiltrosAvancados, setMostrarFiltrosAvancados] = useState(false)
    const [loadingGoogle, setLoadingGoogle] = useState(false)
    const [isGeocodingRunning, setIsGeocodingRunning] = useState(false)
    
    // Novo Estado: Área visível do mapa
    const [mapBounds, setMapBounds] = useState<L.LatLngBounds | null>(null)

    useEffect(() => {
        carregarImoveis()
        
        // Polling para verificar se geocodificador está rodando
        const interval = setInterval(async () => {
            try {
                const res = await fetch('http://127.0.0.1:8765/geocode/status')
                const data = await res.json()
                setIsGeocodingRunning(data.running)
            } catch (err) {
                // Silencie erro de polling se o servidor estiver offline
            }
        }, 3000)
        
        return () => clearInterval(interval)
    }, [])

    async function handleRevisarGoogleSingle(imovelId: number) {
        setLoadingGoogle(true)
        const loadingToast = toast.loading('Consultando Google Maps...')
        try {
            const res = await fetch('http://127.0.0.1:8765/geocode/google/single', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ imovel_id: imovelId })
            })
            if (!res.ok) throw new Error('Servidor offline')
            const data = await res.json()
            if (data.sucesso) {
                toast.success('Localização corrigida via Google!', { id: loadingToast })
                setImoveis(prev => prev.map(im => 
                    im.id === imovelId ? { ...im, latitude: data.coords.lat, longitude: data.coords.lng } : im
                ))
            } else {
                toast.error(data.erro || 'Não foi possível localizar', { id: loadingToast })
            }
        } catch (err) {
            toast.error('Erro de conexão com o robô.', { id: loadingToast })
        } finally {
            setLoadingGoogle(false)
        }
    }

    async function carregarImoveis() {
        setLoading(true)
        const { data, error } = await supabase
            .from('imoveis')
            .select('*')
            .not('latitude', 'is', null)
            .not('longitude', 'is', null)
            .or('anuncio_expirado.is.null,anuncio_expirado.eq.false')
            .limit(50000) // Voltando ao limite original estável

        if (error) {
            toast.error('Erro ao carregar mapa')
        } else if (data) {
            setImoveis(data as ImovelKanban[])
        }
        setLoading(false)
    }

    const handleRunGoogleGeocoder = async () => {
        setLoadingGoogle(true)
        try {
            const response = await fetch('http://127.0.0.1:8765/geocode/google', { method: 'POST' })
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


    const handleStopGeocoder = async () => {
        try {
            await fetch('http://127.0.0.1:8765/geocode/stop', { method: 'POST' })
            toast.success('Sinal de parada enviado!')
        } catch (err) {
            toast.error('Erro ao parar geocodificador.')
        }
    }

    const options = useMemo(() => {
        const bairros = new Set<string>()
        const condominios = new Set<string>()
        const tipos = new Set<string>()
        const subtipos = new Set<string>()
        const cidades = new Set<string>()

        imoveis.forEach(im => {
            if (im.bairro) bairros.add(im.bairro)
            if (im.nome_condominio) condominios.add(im.nome_condominio)
            if (im.tipo_imovel) tipos.add(im.tipo_imovel)
            if (im.subtipo) subtipos.add(im.subtipo)
            if (im.cidade) cidades.add(im.cidade)
        })

        return {
            bairros: Array.from(bairros).sort(),
            condominios: Array.from(condominios).sort(),
            tipos: Array.from(tipos).sort(),
            subtipos: Array.from(subtipos).sort(),
            cidades: Array.from(cidades).sort()
        }
    }, [imoveis])

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
        if (bairrosSelecionados.length > 0) {
            if (!im.bairro || !bairrosSelecionados.includes(im.bairro)) return false
        }
        
        if (cidadesSelecionadas.length > 0) {
            if (!im.cidade || !cidadesSelecionadas.includes(im.cidade)) return false
        }
        
        if (condominiosSelecionados.length > 0) {
            if (!im.nome_condominio || !condominiosSelecionados.includes(im.nome_condominio)) return false
        }

        if (tipoImovel && im.tipo_imovel !== tipoImovel) return false
        if (subtipo && im.subtipo !== subtipo) return false

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
        if (!mapBounds) return filtrados.slice(0, 50)

        const visiveis = filtrados.filter(im => {
            if (im.latitude == null || im.longitude == null) return false
            const pt = L.latLng(im.latitude, im.longitude)
            return mapBounds.contains(pt)
        })

        return visiveis.slice(0, 50)
    }, [filtrados, mapBounds])

    const mapPoints = useMemo(() => filtrados.map(im => ({
        id: im.id,
        lat: Number(im.latitude),
        lng: Number(im.longitude),
        onMarkerClick: () => setImovelSelecionado(im),
        tooltipContent: (
            <div style={{ minWidth: 200, maxWidth: 240, overflow: 'hidden' }}>
                {im.foto_capa && (
                    <img
                        src={im.foto_capa}
                        alt=""
                        style={{ height: 110, width: '100%', objectFit: 'cover', display: 'block' }}
                    />
                )}
                <div style={{ padding: '10px' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.85rem', lineHeight: 1.3, marginBottom: 4, color: '#1A1C1E' }}>
                        {im.titulo}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--m3-on-surface-variant)', marginBottom: 6 }}>
                        📍 {im.bairro || im.cidade || '—'}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                        <div style={{ fontWeight: 800, color: 'var(--m3-primary)', fontSize: '0.95rem' }}>
                            {im.preco ? `R$ ${im.preco.toLocaleString('pt-BR')}` : 'S/P'}
                        </div>
                        {im.quartos && (
                            <div style={{ fontSize: '0.7rem', background: 'var(--m3-surface)', padding: '2px 8px', borderRadius: 4, color: 'var(--m3-on-surface-variant)', border: '1px solid var(--m3-outline-variant)' }}>
                                🛏 {im.quartos}q
                            </div>
                        )}
                    </div>
                </div>
            </div>
        )
    })), [filtrados])

    return (
        <div className="map-page-container">
            {/* Header */}
            <header className="map-header">
                <div>
                    <h1>🗺️ Mapa de Imóveis</h1>
                    <p>Visualizando {filtrados.length} imóveis com coordenadas.</p>
                </div>

                <div className="filter-bar-main">
                    <input
                        className="m3-input"
                        placeholder="🔍 Título, bairro ou cidade..."
                        value={busca}
                        onChange={e => setBusca(e.target.value)}
                        style={{ maxWidth: 280 }}
                    />
                    <select
                        className="m3-select"
                        value={tipoNegocio}
                        onChange={e => setTipoNegocio(e.target.value as any)}
                        style={{ width: 'auto' }}
                    >
                        <option value="">Tipo Negócio</option>
                        <option value="venda">Venda</option>
                        <option value="aluguel">Aluguel</option>
                    </select>
                    
                    <button 
                        className={`m3-btn ${mostrarFiltrosAvancados ? 'm3-btn-active' : 'm3-btn-secondary'}`}
                        onClick={() => setMostrarFiltrosAvancados(!mostrarFiltrosAvancados)}
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                        </svg>
                        Filtros
                    </button>

                    <button
                        className="m3-btn m3-btn-success"
                        onClick={handleRunGoogleGeocoder}
                        disabled={loadingGoogle}
                        title="Google Maps: geocodificar imóveis sem coordenadas"
                    >
                        {loadingGoogle ? <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> : <span>🗺️</span>}
                        Google (novos)
                    </button>

                    {isGeocodingRunning && (
                        <button
                            className="m3-btn"
                            onClick={handleStopGeocoder}
                            style={{ background: '#FCE8E6', color: 'var(--m3-error)', border: '1px solid var(--m3-error)' }}
                        >
                            🛑 Cancelar
                        </button>
                    )}
                </div>
            </header>

            {/* Filtros Avançados */}
            {mostrarFiltrosAvancados && (
                <div className="advanced-filters-panel">
                    <div className="m3-field-group">
                        <label className="m3-label">Preço Mín</label>
                        <input
                            className="m3-input"
                            type="number"
                            placeholder="R$"
                            value={precoMin}
                            onChange={e => setPrecoMin(e.target.value)}
                        />
                    </div>
                    <div className="m3-field-group">
                        <label className="m3-label">Preço Máx</label>
                        <input
                            className="m3-input"
                            type="number"
                            placeholder="R$"
                            value={precoMax}
                            onChange={e => setPrecoMax(e.target.value)}
                        />
                    </div>
                    
                    <MultiSelectDropdown 
                        label="Cidades" 
                        options={options.cidades} 
                        selected={cidadesSelecionadas} 
                        onChange={setCidadesSelecionadas}
                        placeholder="Todas"
                    />
                    
                    <MultiSelectDropdown 
                        label="Bairros" 
                        options={options.bairros} 
                        selected={bairrosSelecionados} 
                        onChange={setBairrosSelecionados}
                        placeholder="Todos"
                    />
                    
                    <MultiSelectDropdown 
                        label="Condomínios" 
                        options={options.condominios} 
                        selected={condominiosSelecionados} 
                        onChange={setCondominiosSelecionados}
                        placeholder="Todos"
                    />

                    <div className="m3-field-group">
                        <label className="m3-label">Tipo</label>
                        <select
                            className="m3-select"
                            value={tipoImovel}
                            onChange={e => setTipoImovel(e.target.value)}
                        >
                            <option value="">Todos</option>
                            {options.tipos.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                    </div>

                    <div className="m3-field-group">
                        <label className="m3-label">Subtipo</label>
                        <select
                            className="m3-select"
                            value={subtipo}
                            onChange={e => setSubtipo(e.target.value)}
                        >
                            <option value="">Todos</option>
                            {options.subtipos.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                    </div>

                    <div className="m3-field-group">
                        <label className="m3-label">Quartos</label>
                        <select
                            className="m3-select"
                            value={quartos}
                            onChange={e => setQuartos(e.target.value)}
                        >
                            <option value="">Qualquer</option>
                            <option value="1">1+</option>
                            <option value="2">2+</option>
                            <option value="3">3+</option>
                            <option value="4">4+</option>
                        </select>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', paddingBottom: '1.5rem' }}>
                         <button 
                            className="m3-btn-text"
                            onClick={() => {
                                setPrecoMin('')
                                setPrecoMax('')
                                setBairrosSelecionados([])
                                setCidadesSelecionadas([])
                                setCondominiosSelecionados([])
                                setQuartos('')
                                setTipoImovel('')
                                setSubtipo('')
                            }}
                            style={{ color: 'var(--m3-primary)' }}
                        >
                            Limpar Filtros
                        </button>
                    </div>
                </div>
            )}

            {/* Área Principal */}
            <div className="map-main-area">
                {/* Mapa */}
                <div style={{ position: 'absolute', inset: 0 }}>
                    {loading ? (
                        <div className="loading-screen" style={{ background: 'var(--m3-surface)' }}>
                            <div className="spinner" />
                        </div>
                    ) : (
                        <MapView points={mapPoints} height="100%" onBoundsChange={setMapBounds} />
                    )}
                </div>

                {/* Sidebar M3 */}
                <aside className="m3-map-sidebar">
                    <header className="sidebar-header">
                        <h2>📌 Imóveis na visão</h2>
                        <span className="sidebar-count">{imoveisVisiveis.length}</span>
                    </header>

                    <div className="sidebar-scroll">
                        {imoveisVisiveis.length === 0 && (
                            <div style={{ textAlign: 'center', color: 'var(--m3-on-surface-variant)', fontSize: '0.85rem', padding: '3rem 1rem' }}>
                                Nenhum imóvel visível nesta área.
                            </div>
                        )}
                        {imoveisVisiveis.map(im => (
                            <div
                                key={im.id}
                                className="m3-property-card"
                                onClick={() => setImovelSelecionado(im)}
                            >
                                <div className="card-img-box">
                                    {im.foto_capa ? (
                                        <img src={im.foto_capa} alt="" />
                                    ) : (
                                        <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', opacity: 0.3 }}>🏠</div>
                                    )}
                                </div>

                                <div className="card-info-box">
                                    <div className="card-title">{im.titulo}</div>
                                    <div className="card-price">
                                        {im.preco ? `R$ ${im.preco.toLocaleString('pt-BR')}` : 'S/P'}
                                    </div>
                                    <div className="card-meta">
                                        <span title={im.bairro}>📍 {im.bairro || '—'}</span>
                                        {im.quartos && <span>• 🛏 {im.quartos}q</span>}
                                    </div>
                                    <div 
                                        title="Clique para copiar ID"
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            navigator.clipboard.writeText(String(im.id))
                                            toast.success('ID copiado!')
                                        }}
                                        style={{ fontSize: '0.7rem', opacity: 0.5, cursor: 'pointer', marginTop: '4px' }}
                                    >
                                        ID: {im.id}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </aside>
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
