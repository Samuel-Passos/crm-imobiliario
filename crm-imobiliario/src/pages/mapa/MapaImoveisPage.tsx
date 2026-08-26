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
            <label className="m3-label">{label}</label>
            <div 
                onClick={() => setIsOpen(!isOpen)}
                className={`form-select ${isOpen ? 'open' : ''}`}
                style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    cursor: 'pointer'
                }}
            >
                <span style={{ 
                    fontSize: '0.85rem', 
                    whiteSpace: 'nowrap', 
                    overflow: 'hidden', 
                    textOverflow: 'ellipsis',
                    color: selected.length > 0 ? 'var(--text-primary)' : 'var(--text-secondary)'
                }}>
                    {selected.length === 0 ? placeholder : `${selected.length} selecionado(s)`}
                </span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s', color: 'var(--text-muted)' }}>
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </div>

            {isOpen && (
                <div className="m3-dropdown-menu">
                    <input 
                        autoFocus
                        type="text"
                        className="form-input"
                        placeholder="Pesquisar..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        onClick={e => e.stopPropagation()}
                        style={{ height: '36px', fontSize: '0.85rem' }}
                    />
                    
                    <div className="m3-dropdown-options">
                        {filteredOptions.length === 0 && (
                            <div style={{ padding: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)', textAlign: 'center' }}>Nenhum resultado</div>
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
                        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '8px', display: 'flex', justifyContent: 'flex-end' }}>
                            <button 
                                onClick={(e) => { e.stopPropagation(); onChange([]) }}
                                className="m3-btn-text"
                                style={{ color: 'var(--brand-500)' }}
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

    // Estados para Categorias e Filtros Visuais
    const [colunaNomesMap, setColunaNomesMap] = useState<Record<string, string>>({})
    const [mostrarMercado, setMostrarMercado] = useState(true)
    const [mostrarFunil, setMostrarFunil] = useState(true)
    const [mostrarAutorizados, setMostrarAutorizados] = useState(true)

    useEffect(() => {
        carregarImoveis()
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
        
        // 1. Carrega as colunas para mapear os nomes
        const { data: cols } = await supabase.from('kanban_colunas').select('*')
        if (cols) {
            const map: Record<string, string> = {}
            cols.forEach(c => map[c.id] = c.nome)
            setColunaNomesMap(map)
        }

        // 2. Carrega os imóveis — apenas campos necessários para o mapa e sidebar
        // (fotos[], descricao, outras_caracteristicas etc. são pesados e não são usados aqui)
        const { data, error } = await supabase
            .from('imoveis')
            .select(`
                id, titulo, preco, latitude, longitude,
                tipo_imovel, subtipo, tipo_negocio,
                foto_capa, bairro, cidade, quartos, area_m2,
                autorizado, kanban_coluna_id, anuncio_expirado,
                nome_condominio, vendedor_nome, telefone,
                telefone_mascara, vendedor_whatsapp, url, ad_id,
                rua, numero, complemento, estado, cep,
                vagas, banheiros, suites, aceita_permuta,
                em_condominio, bloco, numero_apartamento
            `)
            .not('latitude', 'is', null)
            .not('longitude', 'is', null)
            .or('anuncio_expirado.is.null,anuncio_expirado.eq.false')
            .limit(3000)

        if (error) {
            toast.error('Erro ao carregar mapa')
        } else if (data) {
            setImoveis(data as ImovelKanban[])
        }
        setLoading(false)
    }

    const getImovelCategory = (im: ImovelKanban): 'autorizados' | 'funil' | 'mercado' => {
        if (im.autorizado) return 'autorizados'
        const colName = im.kanban_coluna_id ? colunaNomesMap[im.kanban_coluna_id] : ''
        if (colName === 'Anúncios de Mercado' || !im.kanban_coluna_id) return 'mercado'
        return 'funil'
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
        // Filtragem por Categoria (Autorizado, Funil, Mercado)
        const cat = getImovelCategory(im)
        if (cat === 'autorizados' && !mostrarAutorizados) return false
        if (cat === 'mercado' && !mostrarMercado) return false
        if (cat === 'funil' && !mostrarFunil) return false

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
        category: getImovelCategory(im),
        onMarkerClick: () => setImovelSelecionado(im)
    })), [filtrados])

    const getCategoryLabel = (cat: 'autorizados' | 'funil' | 'mercado') => {
        if (cat === 'autorizados') return 'Autorizado'
        if (cat === 'funil') return 'Funil'
        return 'Mercado'
    }

    return (
        <div className="map-page-container">
            {/* Header */}
            <header className="map-header">
                <div>
                    <h1>🗺️ Mapa de Imóveis</h1>
                </div>
                <div className="map-header-sub">
                    <p>Visualizando</p>
                    <span className="header-badge">{filtrados.length} imóveis</span>
                </div>
            </header>

            {/* Barra de Filtros Principal */}
            <div className="filter-bar-main">
                <span className="filter-bar-label">Filtros</span>

                <input
                    className="form-input"
                    placeholder="🔍 Buscar título, bairro ou cidade..."
                    value={busca}
                    onChange={e => setBusca(e.target.value)}
                    style={{ width: 230, flex: 'none' }}
                />

                <select
                    className="form-select"
                    value={tipoNegocio}
                    onChange={e => setTipoNegocio(e.target.value as any)}
                    style={{ width: 140, flex: 'none' }}
                >
                    <option value="">Negócio (todos)</option>
                    <option value="venda">💰 Venda</option>
                    <option value="aluguel">🔑 Aluguel</option>
                </select>

                <div className="filter-category-pills">
                    <label className="filter-category-pill">
                        <input type="checkbox" checked={mostrarAutorizados} onChange={e => setMostrarAutorizados(e.target.checked)} style={{ margin: 0 }} />
                        <span style={{ color: '#ef4444' }}>🔴</span> Autorizados
                    </label>
                    <label className="filter-category-pill">
                        <input type="checkbox" checked={mostrarFunil} onChange={e => setMostrarFunil(e.target.checked)} style={{ margin: 0 }} />
                        <span style={{ color: '#f97316' }}>🟠</span> Funil
                    </label>
                    <label className="filter-category-pill">
                        <input type="checkbox" checked={mostrarMercado} onChange={e => setMostrarMercado(e.target.checked)} style={{ margin: 0 }} />
                        <span style={{ color: '#3b82f6' }}>🔵</span> Mercado
                    </label>
                </div>

                <button
                    className={`filter-adv-btn ${mostrarFiltrosAvancados ? 'active' : ''}`}
                    onClick={() => setMostrarFiltrosAvancados(!mostrarFiltrosAvancados)}
                >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                    </svg>
                    Filtros Avançados
                </button>
            </div>

            {/* Filtros Avançados */}
            {mostrarFiltrosAvancados && (
                <div className="advanced-filters-panel">
                    <div className="adv-field">
                        <label>Preço Mín</label>
                        <input className="form-input" type="number" placeholder="R$" value={precoMin} onChange={e => setPrecoMin(e.target.value)} />
                    </div>
                    <div className="adv-field">
                        <label>Preço Máx</label>
                        <input className="form-input" type="number" placeholder="R$" value={precoMax} onChange={e => setPrecoMax(e.target.value)} />
                    </div>

                    <MultiSelectDropdown label="Cidades" options={options.cidades} selected={cidadesSelecionadas} onChange={setCidadesSelecionadas} placeholder="Todas" />
                    <MultiSelectDropdown label="Bairros" options={options.bairros} selected={bairrosSelecionados} onChange={setBairrosSelecionados} placeholder="Todos" />
                    <MultiSelectDropdown label="Condomínios" options={options.condominios} selected={condominiosSelecionados} onChange={setCondominiosSelecionados} placeholder="Todos" />

                    <div className="adv-field">
                        <label>Tipo</label>
                        <select className="form-select" value={tipoImovel} onChange={e => setTipoImovel(e.target.value)}>
                            <option value="">Todos</option>
                            {options.tipos.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                    </div>
                    <div className="adv-field">
                        <label>Subtipo</label>
                        <select className="form-select" value={subtipo} onChange={e => setSubtipo(e.target.value)}>
                            <option value="">Todos</option>
                            {options.subtipos.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                    </div>
                    <div className="adv-field" style={{ flex: 'none', width: 110 }}>
                        <label>Quartos</label>
                        <select className="form-select" value={quartos} onChange={e => setQuartos(e.target.value)}>
                            <option value="">Qualquer</option>
                            <option value="1">1+</option>
                            <option value="2">2+</option>
                            <option value="3">3+</option>
                            <option value="4">4+</option>
                        </select>
                    </div>
                    <div className="adv-field" style={{ flex: 'none', justifyContent: 'flex-end', width: 'auto' }}>
                        <label>&nbsp;</label>
                        <button
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
                            style={{
                                background: 'none', border: 'none', color: 'var(--brand-500)',
                                fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer', padding: '0.45rem 0',
                                whiteSpace: 'nowrap'
                            }}
                        >
                            ✕ Limpar
                        </button>
                    </div>
                </div>
            )}

            {/* Área Principal */}
            <div className="map-main-area">
                {/* Mapa */}
                <div style={{ position: 'absolute', inset: 0 }}>
                    {loading ? (
                        <div className="loading-screen">
                            <div className="spinner" />
                        </div>
                    ) : (
                        <MapView points={mapPoints} height="100%" onBoundsChange={setMapBounds} />
                    )}
                </div>

                {/* Sidebar */}
                <aside className="m3-map-sidebar">
                    <header className="sidebar-header">
                        <h2>📌 Imóveis na visão</h2>
                        <span className="sidebar-count">{imoveisVisiveis.length}</span>
                    </header>

                    <div className="sidebar-scroll">
                        {imoveisVisiveis.length === 0 && (
                            <div className="sidebar-empty">
                                <div className="sidebar-empty-icon">🗺️</div>
                                <p>Nenhum imóvel visível nesta área.<br/>Navegue pelo mapa para explorar.</p>
                            </div>
                        )}

                        {imoveisVisiveis.map(im => {
                            const cat = getImovelCategory(im)
                            return (
                                <div
                                    key={im.id}
                                    className="property-card"
                                    onClick={() => setImovelSelecionado(im)}
                                >
                                    {/* Foto */}
                                    <div className="property-card-img">
                                        {im.foto_capa ? (
                                            <img src={im.foto_capa} alt={im.titulo} loading="lazy" />
                                        ) : (
                                            <div className="property-card-no-img">🏠</div>
                                        )}
                                        <span className={`property-card-category ${cat}`}>
                                            {getCategoryLabel(cat)}
                                        </span>
                                    </div>

                                    {/* Corpo */}
                                    <div className="property-card-body">
                                        <div className="property-card-price">
                                            {im.preco ? `R$ ${im.preco.toLocaleString('pt-BR')}` : <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Preço não informado</span>}
                                        </div>
                                        <div className="property-card-title" title={im.titulo}>
                                            {im.titulo}
                                        </div>
                                        <div className="property-card-location">
                                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, color: 'var(--text-muted)' }}>
                                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                                                <circle cx="12" cy="10" r="3"/>
                                            </svg>
                                            {[im.bairro, im.cidade].filter(Boolean).join(', ') || '—'}
                                        </div>

                                        <div className="property-card-chips">
                                            {im.tipo_imovel && <span className="property-chip">🏡 {im.tipo_imovel}</span>}
                                            {im.quartos != null && <span className="property-chip">🛏 {im.quartos}q</span>}
                                            {im.area_m2 != null && <span className="property-chip">📐 {im.area_m2}m²</span>}
                                            {im.tipo_negocio && <span className="property-chip">{im.tipo_negocio === 'venda' ? '💰' : '🔑'} {im.tipo_negocio}</span>}
                                        </div>
                                    </div>

                                    {/* Footer */}
                                    <div className="property-card-footer">
                                        <span
                                            className="property-card-id"
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                navigator.clipboard.writeText(String(im.id))
                                                toast.success('ID copiado!')
                                            }}
                                            title="Clique para copiar ID"
                                        >
                                            ID #{im.id}
                                        </span>
                                        <span className="property-card-open">
                                            Ver detalhes
                                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                <polyline points="9 18 15 12 9 6"/>
                                            </svg>
                                        </span>
                                    </div>
                                </div>
                            )
                        })}
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
