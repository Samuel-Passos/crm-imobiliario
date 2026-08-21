import React, { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import './ExtratorCnpjPage.css' // Importando o novo CSS

const ROBO_URL = 'http://localhost:8766'

interface EmpresaCNPJ {
    id: string
    cnpj: string
    identificador_matriz_filial: string
    razao_social: string
    nome_fantasia: string
    cnae: string
    natureza_juridica: string
    whatsapp: string
    email: string
    email_site: string
    score: number
    status: string
    data_inicio_atividade: string
    data_situacao_cadastral: string
    motivo_situacao_cadastral: string
    logradouro: string
    numero: string
    complemento: string
    bairro: string
    municipio: string
    uf: string
    cep: string
    capital_social: number
    socios: string
    qualificacao_do_responsavel: string
    porte: string
    opcao_pelo_simples: string
    data_opcao_pelo_simples: string
    data_exclusao_do_simples: string
    opcao_pelo_mei: string
    situacao_especial: string
    data_situacao_especial: string
    posicao: string
    tel_maps: string
    site: string
    instagram: string
    facebook: string
    telefone_completo_1: string
    tel_opencnpj: string
    email_opencnpj: string
    site_google: string
    qsa_completo: any
    responsavel_qualificacao: string
    notas_investigacao: string
    atualizado_em: string
}

export function ExtratorCnpjPage() {
    const navigate = useNavigate()
    const [empresas, setEmpresas] = useState<EmpresaCNPJ[]>([])
    const [loading, setLoading] = useState(true)
    const [executando, setExecutando] = useState(false)
    const [status, setStatus] = useState<any>(null)
    const [logs, setLogs] = useState<string[]>([])
    const [busca, setBusca] = useState('')
    const [segmento, setSegmento] = useState<'todos' | 'imobiliarias' | 'condominios'>('todos')
    
    const [selectedIdx, setSelectedIdx] = useState<number | null>(null)
    const [enriquecendoIndividual, setEnriquecendoIndividual] = useState(false)
    const [showEditModal, setShowEditModal] = useState(false)
    const [editForm, setEditForm] = useState<Partial<EmpresaCNPJ>>({})

    const [currentPage, setCurrentPage] = useState(1)
        const REGIOES_SJC: any = {
        'Centro': ['CENTRO', 'ADYANA', 'EMA', 'SAO DIMAS', 'MARINGA', 'MONTE CASTELO', 'SANCHES', 'BETANIA', 'BAIRRO DAS ACACIAS', 'VILA MARIA', 'IGUALDADE', 'VILA JACI', 'BAIXA'],
        'Oeste': ['AQUARIUS', 'COLINAS', 'URBANOVA', 'ESPLANADA', 'ALVORADA', 'LIMOEIRO', 'PARATEHY', 'SERIMBURA', 'JAGUARI', 'VIDA NOVA'],
        'Sul': ['SATELITE', 'BOSQUE', 'INDUSTRIAL', 'ORIENTE', 'MORUMBI', 'FLORADAS', 'CIDADE JARDIM', 'GAZZO', 'UNIAO', 'INTERLAGOS', 'DOM PEDRO', '31 DE MARCO', 'RECANTO DOS PINHEIROS', 'CHACARAS REUNIDAS', 'CAMBUI', 'MANTIQUEIRA'],
        'Leste': ['VISTA VERDE', 'EUGENIO DE MELO', 'GALO BRANCO', 'SANTA INES', 'TATETUBA', 'NOVO HORIZONTE', 'TESOURO', 'VENEZIANI', 'CAMPOS DE SAO JOSE', 'SEMINARIO', 'COQUEIRO', 'FREI GALVAO', 'PAIVA', 'PARAISO', 'PRIMAVERA', 'VISTA LINDA'],
        'Norte': ['SANTANA', 'ALTOS DE SANTANA', 'VILA PAIVA', 'BUQUIRA', 'COSTINHA', 'TELESPARK', 'MIRANTE', 'VALE DO SOL'],
        'Sudeste': ['PUTIM', 'SAO JUDAS', 'TERRA NOVA', 'SAO LEOPOLDO', 'RESERVA', 'PLANALTO', 'SAN MARINO', 'SANTA JULIA', 'TORRAO DE OURO']
    }
    const [itemsPerPage, setItemsPerPage] = useState(50)

    const [serverOnline, setServerOnline] = useState(false)
    const [startingServer, setStartingServer] = useState(false)

    // Resetar página ao filtrar
    useEffect(() => {
        setCurrentPage(1)
    }, [segmento])

    const [searchTerm, setSearchTerm] = useState('')
    const [bairroFilter, setBairroFilter] = useState('')
    const [hasZapOnly, setHasZapOnly] = useState(false)
    const [hasSiteOnly, setHasSiteOnly] = useState(false)
    
    // Lista filtrada baseada nos novos estados
    const filtradas = empresas.filter(e => {
        const matchesTerm = !searchTerm || 
            (e.razao_social && e.razao_social.toLowerCase().includes(searchTerm.toLowerCase())) ||
            (e.cnae_descricao && e.cnae_descricao.toLowerCase().includes(searchTerm.toLowerCase())) ||
            (e.cnaes_secundarios && e.cnaes_secundarios.toLowerCase().includes(searchTerm.toLowerCase()));
        
        const bairrosParaFiltrar = bairroFilter.split(',').map(b => b.trim().toLowerCase()).filter(b => b !== '');
        const matchesBairro = bairrosParaFiltrar.length === 0 || 
            bairrosParaFiltrar.some(b => e.bairro && e.bairro.toLowerCase().includes(b));
        
        const matchesZap = !hasZapOnly || !!e.whatsapp;
        const matchesSite = !hasSiteOnly || !!e.site || !!e.site_google;
        
        const matchesSegmento = (() => {
            if (segmento === 'todos') return true
            if (segmento === 'imobiliarias') {
                const imobCnaes = ['6821801', '6821802', '6822600', '6810201', '6810202']
                return imobCnaes.includes(e.cnae)
            }
            if (segmento === 'condominios') {
                const condoCnaes = ['8112500', '9499500']
                return condoCnaes.includes(e.cnae)
            }
            return true
        })()
        
        return matchesTerm && matchesBairro && matchesZap && matchesSite && matchesSegmento
    })

    const totalPages = Math.ceil(filtradas.length / itemsPerPage)
    const paginadas = filtradas.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)

    const empresaAtiva = selectedIdx !== null ? paginadas[selectedIdx] : null

    useEffect(() => {
        carregarDados()
        const iv = setInterval(() => {
            fetchStatus()
            checkServerHealth()
        }, 3000)
        return () => clearInterval(iv)
    }, [])

    async function checkServerHealth() {
        try {
            const res = await fetch(`${ROBO_URL}/status`)
            setServerOnline(res.ok)
        } catch (e) { setServerOnline(false) }
    }

    async function handleLigarServidor() {
        setStartingServer(true)
        const tid = toast.loading('Ligando serviços...')
        try {
            const res = await fetch('http://localhost:8767/start', { method: 'POST' })
            const data = await res.json()
            if (data.ok) toast.success('Robôs acionados!', { id: tid })
            else toast.error(data.mensagem, { id: tid })
        } catch (e) {
            toast.error('Launcher Daemon offline (8767).', { id: tid })
        } finally {
            setTimeout(() => setStartingServer(false), 5000)
        }
    }

    async function carregarDados() {
        setLoading(true)
        const { data, error } = await supabase
            .from('empresas_sjc')
            .select('*')
            .order('score', { ascending: false })

        if (error) toast.error('Erro ao conectar ao Supabase.')
        else setEmpresas(data || [])
        setLoading(false)
    }

    async function handleSaveDatabase() {
        if (!empresaAtiva) return
        const tid = toast.loading('Salvando alterações...')
        try {
            const { error } = await supabase.from('empresas_sjc').update(editForm).eq('id', empresaAtiva.id)
            if (error) throw error
            toast.success('Dados salvos!', { id: tid })
            setShowEditModal(false)
            carregarDados()
        } catch (e) { toast.error('Erro ao salvar.', { id: tid }) }
    }

    async function handleEnriquecerIndividual(cnpj: string) {
        if (!serverOnline) return toast.error('Robô Offline')
        setEnriquecendoIndividual(true)
        const tid = toast.loading('Enriquecendo...')
        try {
            const res = await fetch(`${ROBO_URL}/extrator/enriquecer-individual`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cnpj })
            })
            const data = await res.json()
            if (data.ok) { toast.success('Finalizado!', { id: tid }); carregarDados(); }
            else toast.error(data.mensagem, { id: tid })
        } catch (e) { toast.error('Conexão falhou.', { id: tid }) }
        finally { setEnriquecendoIndividual(false) }
    }

    const [disparandoLote, setDisparandoLote] = useState(false)

    async function handleEnriquecerReceitaWS(cnpj: string) {
        if (!serverOnline) return toast.error('Robô Offline')
        setEnriquecendoIndividual(true)
        const tid = toast.loading('Consultando ReceitaWS...')
        try {
            const res = await fetch(`${ROBO_URL}/extrator/enriquecer-receitaws`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cnpj })
            })
            const data = await res.json()
            if (data.ok) { toast.success('Lead enriquecido!', { id: tid }); carregarDados(); }
            else toast.error(data.mensagem, { id: tid })
        } catch (e) { toast.error('Falha na rede.', { id: tid }) }
        finally { setEnriquecendoIndividual(false) }
    }

    async function handleDispararLoteDireto() {
        if (!serverOnline) return toast.error('Robô Offline')
        const limit = prompt('Quantidade de leads para este lote:', '1000')
        if (!limit) return

        setDisparandoLote(true)
        const tid = toast.loading('Acionando Motor Direto...')
        try {
            const res = await fetch(`${ROBO_URL}/extrator/lote-direto`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ limit: parseInt(limit) })
            })
            const data = await res.json()
            if (data.ok) toast.success(data.mensagem, { id: tid })
            else toast.error(data.mensagem, { id: tid })
        } catch (e) { toast.error('Erro ao conectar ao motor.', { id: tid }) }
        finally { setDisparandoLote(false) }
    }


    async function fetchStatus() {
        try {
            const res = await fetch(`${ROBO_URL}/extrator/status`)
            const data = await res.json()
            if (data.ok) setStatus(data.status)
            
            const resLogs = await fetch(`${ROBO_URL}/extrator/logs`)
            const dataLogs = await resLogs.json()
            if (dataLogs.ok) setLogs(dataLogs.logs)
        } catch (e) { }
    }

    async function iniciarExtracao(testCondo = false, forceAllCnaes = false, stepToRun = 'all') {
        if (!confirm('Deseja iniciar extração de leads? Isso pode levar algum tempo.')) return
        setExecutando(true)
        try {
            const res = await fetch(`${ROBO_URL}/extrator/iniciar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ municipio: 'SAO JOSE DOS CAMPOS', step: stepToRun, test_condo: testCondo, all_cnaes: forceAllCnaes })
            })
            const data = await res.json()
            if (data.ok) toast.success('Pipeline disparado! 🚀')
            else toast.error(data.mensagem)
        } catch (error) { toast.error('Robô não responde.') }
        finally { setExecutando(false) }
    }

    const steps = [
        { id: 0, label: 'Receita', desc: 'Dados Oficiais' },
        { id: 1, label: 'Extração', desc: 'Filtro SJC' },
        { id: 2, label: 'Qualificação', desc: 'Scoring' },
        { id: 3, label: 'Sócios', desc: 'QSA Brasil.io' },
        { id: 4, label: 'Maps', desc: 'Digital & Local' },
        { id: 5, label: 'Whats', desc: 'Validação' },
        { id: 6, label: 'CRM', desc: 'Sincronizar' }
    ]

    const stats = status?.stats || { total: 0, whatsapp: 0, website: 0, email: 0, opencnpj_ok: 0, maps_ok: 0, scraping_ok: 0 }

    return (
        <div className="extractor-container">
            <div className="dashboard-wrapper">
                
                {/* Server Warning Banner */}
                {!serverOnline && (
                    <div className="server-status-banner">
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                            <span style={{ fontSize: '1.5rem' }}>⚠️</span>
                            <div>
                                <div style={{ fontWeight: 850, color: 'var(--m3-error)' }}>Servidor de Extração Offline</div>
                                <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>O robô (8766) não está respondendo. Inicie o sistema para processar leads.</div>
                            </div>
                        </div>
                        <button onClick={handleLigarServidor} disabled={startingServer} className="m3-btn" style={{ background: 'var(--m3-error)', color: 'white' }}>
                            {startingServer ? '⏳ Ligando...' : '⚡ Reativar Sistema'}
                        </button>
                    </div>
                )}

                {/* Header */}
                <header className="extractor-header">
                    <div>
                        <h1 style={{ fontSize: '2.5rem', fontWeight: 900, color: '#1A1C1E', margin: 0 }}>Extração Inteligente</h1>
                        <p style={{ color: '#535F70', fontSize: '1.1rem', marginTop: '4px' }}>Dashboard de Prospecção — São José dos Campos</p>
                    </div>
                    <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', marginRight: '0.5rem' }}>
                            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: serverOnline ? '#1E8E3E' : '#D93025', marginRight: '8px' }} />
                            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: serverOnline ? '#1E8E3E' : '#D93025' }}>{serverOnline ? 'SISTEMA ATIVO' : 'SISTEMA PARADO'}</span>
                        </div>
                        <button onClick={() => iniciarExtracao(false, false, 'resume')} disabled={executando || !serverOnline} className="m3-btn" style={{ background: '#F8FAFD', color: '#1A1C1E', border: '1px solid var(--m3-outline)' }}>▶️ Resumir</button>
                        <button onClick={handleDispararLoteDireto} disabled={disparandoLote || !serverOnline} className="m3-btn" style={{ background: '#0056D2', color: 'white' }}>🚀 Disparar Lote</button>
                        <button onClick={() => iniciarExtracao(true, false, 'all')} disabled={executando || !serverOnline} className="m3-btn m3-btn-secondary">Condomínios</button>

                        <button onClick={() => iniciarExtracao(false, false, 'all')} disabled={executando || !serverOnline} className="m3-btn m3-btn-secondary">Global (Imob)</button>
                        <button onClick={() => iniciarExtracao(false, true, 'all')} disabled={executando || !serverOnline} className="m3-btn m3-btn-primary">Sem Filtro (Todos)</button>
                    </div>
                </header>
                {/* Stats Section */}
                <section className="stats-grid">
                    <StatCard label="Leads Encontrados" value={stats.total} icon="🔍" color="#0056D2" />
                    <StatCard label="Com WhatsApp" value={stats.whatsapp} icon="✅" color="#1E8E3E" />
                    <StatCard label="Sócios & QSA" value={stats.opencnpj_ok} icon="💎" color="#F9AB00" />
                    <StatCard label="Websites" value={stats.website} icon="🌐" color="#4285F4" />
                    <StatCard label="E-mails" value={stats.email} icon="📧" color="#EA4335" />
                    <div className="stat-card-m3" style={{ justifyContent: 'center' }}>
                        <div style={{ 
                            width: '40px', height: '40px', borderRadius: '50%',
                            background: `conic-gradient(#1E8E3E ${stats.total > 0 ? (stats.whatsapp / stats.total) * 100 : 0}%, #E1E2EC 0)`,
                            display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative'
                        }}>
                            <div style={{ width: '30px', height: '30px', background: 'white', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.65rem', fontWeight: 800 }}>
                                {stats.total > 0 ? Math.round((stats.whatsapp / stats.total) * 100) : 0}%
                            </div>
                        </div>
                        <div style={{ marginLeft: '10px' }}>
                            <div style={{ fontSize: '0.9rem', fontWeight: 900 }}>Qualidade</div>
                            <div style={{ fontSize: '0.65rem', color: '#535F70' }}>Base validada</div>
                        </div>
                    </div>
                </section>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '2rem' }}>
                    
                    {/* Left: Leads List */}
                    <div className="leads-table-container">
                        {/* Filtros de Região */}
                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#535F70', marginRight: '8px' }}>FILTRAR POR REGIÃO:</span>
                            {Object.keys(REGIOES_SJC).map(regiao => (
                                <button 
                                    key={regiao}
                                    onClick={() => setBairroFilter(REGIOES_SJC[regiao].join(', '))}
                                    style={{ 
                                        padding: '6px 12px', borderRadius: '20px', border: '1px solid #C4C7C5',
                                        background: 'white', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer',
                                        transition: 'all 0.2s', display: 'flex', alignItems: 'center', gap: '4px'
                                    }}
                                    onMouseOver={(e) => e.currentTarget.style.background = '#F0F4F8'}
                                    onMouseOut={(e) => e.currentTarget.style.background = 'white'}
                                >
                                    📍 {regiao}
                                </button>
                            ))}
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', gap: '1.5rem', flexWrap: 'wrap' }}>
                            

                            <div style={{ display: 'flex', gap: '1rem', flex: 1, minWidth: '400px' }}>
                                <div style={{ position: 'relative', flex: 2 }}>
                                    <span style={{ position: 'absolute', left: '12px', top: '10px', fontSize: '1.2rem' }}>🔍</span>
                                    <input 
                                        type="text" 
                                        placeholder="Buscar por nome ou atividade (CNAE)..." 
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        style={{ width: '100%', padding: '10px 10px 10px 40px', borderRadius: '12px', border: '1px solid #C4C7C5', fontSize: '0.9rem' }}
                                    />
                                </div>
                                <div style={{ position: 'relative', flex: 1 }}>
                                    <span style={{ position: 'absolute', left: '12px', top: '10px', fontSize: '1.2rem' }}>🏘️</span>
                                    <input 
                                        type="text" 
                                        placeholder="Bairros (use vírgula)..." 
                                        value={bairroFilter}
                                        onChange={(e) => setBairroFilter(e.target.value)}
                                        style={{ width: '100%', padding: '10px 10px 10px 40px', borderRadius: '12px', border: '1px solid #C4C7C5', fontSize: '0.9rem' }}
                                    />
                                </div>
                            </div>

                            <div style={{ display: 'flex', gap: '0.75rem' }}>
                                <button 
                                    onClick={() => setHasZapOnly(!hasZapOnly)}
                                    className={`m3-btn ${hasZapOnly ? 'm3-btn-primary' : 'm3-btn-secondary'}`}
                                    style={{ padding: '8px 16px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <span>{hasZapOnly ? '✅' : '📱'}</span> WhatsApp
                                </button>
                                <button 
                                    onClick={() => setHasSiteOnly(!hasSiteOnly)}
                                    className={`m3-btn ${hasSiteOnly ? 'm3-btn-primary' : 'm3-btn-secondary'}`}
                                    style={{ padding: '8px 16px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <span>{hasSiteOnly ? '✅' : '🌐'}</span> Website
                                </button>
                                { (searchTerm || bairroFilter || hasZapOnly || hasSiteOnly) && (
                                    <button 
                                        onClick={() => { setSearchTerm(''); setBairroFilter(''); setHasZapOnly(false); setHasSiteOnly(false); }}
                                        style={{ background: 'none', border: 'none', color: '#BA1A1A', fontWeight: 700, cursor: 'pointer', fontSize: '0.8rem' }}
                                    >
                                        Limpar
                                    </button>
                                )}
                            </div>
                        </div>

                        <table className="m3-table">
                            <thead>
                                <tr>
                                    <th>Identificação</th>
                                    <th>Contatos</th>
                                    <th>Score</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan={4} style={{ textAlign: 'center', padding: '4rem' }}>Processando base de inteligência...</td></tr>
                                ) : (
                                    paginadas.map((e, idx) => (
                                        <tr 
                                            key={e.id} 
                                            className={`lead-row ${selectedIdx === idx ? 'selected' : ''}`}
                                            onClick={() => setSelectedIdx(idx)}
                                        >
                                            <td>
                                                <div style={{ fontWeight: 800, color: '#1A1C1E' }}>{e.razao_social}</div>
                                                <div style={{ fontSize: '0.7rem', color: '#535F70' }}>{e.cnpj} • {e.bairro}</div>
                                            </td>
                                            <td>
                                                {e.whatsapp ? <span style={{ color: '#1E8E3E', fontWeight: 700, fontSize: '0.8rem' }}>🟢 {e.whatsapp}</span> : 
                                                 e.tel_maps ? <span style={{ color: '#535F70', fontSize: '0.8rem' }}>📍 {e.tel_maps}</span> : '—'}
                                            </td>
                                            <td>
                                                <div style={{ 
                                                    background: e.score >= 4 ? '#E6F4EA' : e.score >= 2 ? '#FEF7E0' : '#FCE8E6',
                                                    color: e.score >= 4 ? '#1E8E3E' : e.score >= 2 ? '#B06000' : '#D93025',
                                                    padding: '4px 8px', borderRadius: '6px', fontWeight: 900, fontSize: '0.8rem', width: 'fit-content'
                                                }}>
                                                    {e.score}/5
                                                </div>
                                            </td>
                                            <td>
                                                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#535F70' }}>{e.porte || 'N/I'}</div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>

                        {/* Pagination Controls */}
                        {!loading && totalPages > 1 && (
                            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '2rem', paddingBottom: '2rem' }}>
                                <button 
                                    disabled={currentPage === 1}
                                    onClick={() => setCurrentPage(prev => prev - 1)}
                                    className="m3-btn m3-btn-secondary"
                                    style={{ padding: '8px 16px' }}
                                >
                                    Anterior
                                </button>
                                
                                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#535F70' }}>
                                    Página <span style={{ color: 'var(--m3-primary)' }}>{currentPage}</span> de {totalPages}
                                    <span style={{ marginLeft: '8px', color: '#8E9199', fontWeight: 500 }}>
                                        ({filtradas.length} total)
                                    </span>
                                </div>

                                <button 
                                    disabled={currentPage === totalPages}
                                    onClick={() => setCurrentPage(prev => prev + 1)}
                                    className="m3-btn m3-btn-secondary"
                                    style={{ padding: '8px 16px' }}
                                >
                                    Próxima
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Right: Pipeline & Quick Info */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        
                        {/* Selected Lead Quick Info */}
                        {empresaAtiva && (
                            <div className="quick-dossier" style={{ position: 'relative', top: 0 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 950 }}>Quick Lead</h3>
                                    <button onClick={() => setSelectedIdx(null)} style={{ border: 'none', background: 'transparent', cursor: 'pointer' }}>✕</button>
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <div style={{ fontWeight: 800, color: '#1A1C1E', fontSize: '1rem' }}>{empresaAtiva.razao_social}</div>
                                    <div style={{ fontSize: '0.75rem', color: '#535F70' }}>SJC — {empresaAtiva.bairro}</div>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    <button onClick={() => navigate(`/extrator-cnpj/lead/${empresaAtiva.id}`)} className="m3-btn m3-btn-primary" style={{ fontSize: '0.75rem' }}>📑 Abrir Dossiê Analítico</button>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                        <button onClick={() => handleEnriquecerReceitaWS(empresaAtiva.cnpj)} className="m3-btn m3-btn-secondary" style={{ fontSize: '0.7rem', padding: '8px' }}>🚀 Receita</button>
                                        <button onClick={() => handleEnriquecerIndividual(empresaAtiva.cnpj)} className="m3-btn m3-btn-secondary" style={{ fontSize: '0.7rem', padding: '8px' }}>🔍 OpenCNPJ</button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Pipeline Stepper */}
                        <div className="pipeline-card">
                            <h3 style={{ margin: '0 0 1.5rem 0', fontSize: '1rem', fontWeight: 900 }}>Pipeline Ativo</h3>
                            <div className="stepper-row">
                                {steps.map((s) => {
                                    const active = status?.last_step === s.id
                                    const completed = status?.last_step > s.id
                                    return (
                                        <div key={s.id} className="step-item">
                                            <div className="step-line" style={{ background: completed ? '#1E8E3E' : 'var(--m3-outline-variant)' }} />
                                            <div className="step-circle" style={{ 
                                                background: completed ? '#1E8E3E' : active ? 'var(--m3-primary)' : 'var(--m3-outline-variant)',
                                                color: 'white'
                                            }}>
                                                {completed ? '✓' : s.id + 1}
                                            </div>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: active ? 'var(--m3-primary)' : '#1A1C1E' }}>{s.label}</div>
                                                <div style={{ fontSize: '0.7rem', color: '#535F70' }}>{active ? status.message : s.desc}</div>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>

                        {/* Logs Console */}
                        <div className="console-card">
                            <div className="console-header">
                                <span style={{ fontSize: '0.65rem', fontWeight: 900, letterSpacing: '0.1em', color: '#E1E2EC' }}>SYSTEM_REPORTS.LOG</span>
                                <div style={{ display: 'flex', gap: '4px' }}>
                                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#D93025' }} />
                                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#F9AB00' }} />
                                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#1E8E3E' }} />
                                </div>
                            </div>
                            <div className="console-body" id="extrator-logs">
                                {logs.map((l, i) => (
                                    <div key={i} style={{ marginBottom: '2px', opacity: 0.9 }}>
                                        <span style={{ color: l.includes('ERROR') ? '#D93025' : l.includes('INFO') ? '#4285F4' : '#1E8E3E', marginRight: '6px' }}>
                                            {l.includes('INFO') ? '>>' : l.includes('ERROR') ? '!!' : '>'}
                                        </span>
                                        {l.split('] ').slice(1).join('] ') || l}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Modal de Edição */}
            {showEditModal && (
                <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(8px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
                    <div className="pipeline-card" style={{ maxWidth: '700px', width: '100%', maxHeight: '90vh', overflowY: 'auto' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem' }}>
                            <h2 style={{ margin: 0 }}>Editar Lead</h2>
                            <button onClick={() => setShowEditModal(false)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', fontSize: '1.2rem' }}>✕</button>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                            <EditField label="Razão Social" value={editForm.razao_social} onChange={v => setEditForm({...editForm, razao_social: v})} />
                            <EditField label="WhatsApp" value={editForm.whatsapp} onChange={v => setEditForm({...editForm, whatsapp: v})} />
                            <EditField label="E-mail" value={editForm.email} onChange={v => setEditForm({...editForm, email: v})} />
                            <EditField label="Telefone Maps" value={editForm.tel_maps} onChange={v => setEditForm({...editForm, tel_maps: v})} />
                        </div>
                        <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem' }}>
                            <button onClick={() => setShowEditModal(false)} className="m3-btn m3-btn-secondary" style={{ flex: 1 }}>Cancelar</button>
                            <button onClick={handleSaveDatabase} className="m3-btn m3-btn-primary" style={{ flex: 2 }}>Salvar Alterações</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

function StatCard({ label, value, icon, color }: any) {
    return (
        <div className="stat-card-m3">
            <div className="stat-icon-box" style={{ background: `${color}15`, color }}>{icon}</div>
            <div>
                <div style={{ fontSize: '1.5rem', fontWeight: 900, color: '#1A1C1E' }}>{value}</div>
                <div style={{ fontSize: '0.8rem', color: '#535F70', fontWeight: 600 }}>{label}</div>
            </div>
        </div>
    )
}

function FilterTab({ active, onClick, label }: any) {
    return <button onClick={onClick} className={`filter-tab ${active ? 'active' : ''}`}>{label}</button>
}

function EditField({ label, value, onChange }: any) {
    return (
        <div>
            <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 800, color: '#535F70', textTransform: 'uppercase', marginBottom: '6px' }}>{label}</label>
            <input 
                type="text" 
                value={value || ''} 
                onChange={e => onChange(e.target.value)}
                style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--m3-outline)', background: '#F8FAFD' }} 
            />
        </div>
    )
}
