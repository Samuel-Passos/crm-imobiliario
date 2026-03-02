import React, { useEffect, useState } from 'react'
import { supabase } from '../../lib/supabase'
import toast from 'react-hot-toast'

interface LinkStats {
    total: number
    pendente: number
    processado: number
    expirado: number
}

interface TipoItem {
    tipo: string
    venda: number
    aluguel: number
    total: number
}

interface ImovelStats {
    total: number
    com_telefone: number
    sem_telefone: number
    por_tipo: TipoItem[]
    venda: number
    locacao: number
    aceita_permuta: number
    nao_aceita_permuta: number
    expirados: number
    total_absoluto: number
}

interface KanbanStats {
    coluna: string
    id: string
    total: number
}

interface ScraperRun {
    id: number
    data_inicio: string
    data_fim: string | null
    leads_processados: number
    leads_expirados: number
    leads_sem_telefone: number
    leads_com_telefone: number
    encontrados_via_botao: number
    encontrados_via_descricao: number
    erros: number
}

interface ScraperLog {
    id: number
    data_hora: string
    imovel_id: number
    url: string
    com_telefone: boolean
    origem_telefone: string | null
    expirado: boolean
    erro: string | null
    duracao_segundos: number
}

function MetricCard({
    label, value, icon, color = 'var(--brand-500)', sub
}: {
    label: string; value: number | string; icon: string; color?: string; sub?: string
}) {
    return (
        <div className="card" style={{
            display: 'flex', alignItems: 'flex-start', gap: '1rem',
            borderLeft: `3px solid ${color}`,
            animation: 'fadeSlideUp 0.4s ease'
        }}>
            <div style={{
                width: 44, height: 44, borderRadius: 'var(--radius-md)',
                background: `${color}20`, display: 'flex', alignItems: 'center',
                justifyContent: 'center', fontSize: '1.3rem', flexShrink: 0
            }}>{icon}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500, marginBottom: '0.25rem' }}>
                    {label}
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>
                    {typeof value === 'number' ? value.toLocaleString('pt-BR') : value}
                </div>
                {sub && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>{sub}</div>}
            </div>
        </div>
    )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
    return (
        <h2 style={{
            fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)',
            textTransform: 'uppercase', letterSpacing: '0.08em',
            marginBottom: '1rem', marginTop: '2rem'
        }}>{children}</h2>
    )
}

export function DashboardPage() {
    const [linkStats, setLinkStats] = useState<LinkStats | null>(null)
    const [imovelStats, setImovelStats] = useState<ImovelStats | null>(null)
    const [kanbanStats, setKanbanStats] = useState<KanbanStats[]>([])
    const [scraperRuns, setScraperRuns] = useState<ScraperRun[]>([])
    const [scraperLogs, setScraperLogs] = useState<ScraperLog[]>([])
    const [loading, setLoading] = useState(true)
    const [executing, setExecuting] = useState(false)
    const [isPaused, setIsPaused] = useState(false)
    const [expandedCycles, setExpandedCycles] = useState<Record<number, boolean>>({})

    const toggleCycle = (id: number) => {
        setExpandedCycles(prev => ({ ...prev, [id]: !prev[id] }))
    }

    const fetchScraperHistory = async () => {
        // ── Scraper Stats ──────────────────────────────────
        const { data: runs } = await supabase
            .from('estatisticas_scraper')
            .select('*')
            .order('data_inicio', { ascending: false })
            .limit(50)

        if (runs) setScraperRuns(runs as ScraperRun[])

        // ── Scraper Detailed Logs ─────────────────────────
        const { data: logs } = await supabase
            .from('logs_detalhados_scraper')
            .select('*')
            .order('data_hora', { ascending: false })
            .limit(100)

        if (logs) setScraperLogs(logs as ScraperLog[])
    }

    const fetchAll = async () => {
        // ── Links: COUNT por status via head requests ────────
        const [
            { count: total },
            { count: processado },
            { count: pendente },
            { count: expirado },
            { count: expiradosImoveis },
            { count: totalImoveisAbsoluto }
        ] = await Promise.all([
            supabase.from('links_anuncios').select('*', { count: 'exact', head: true }),
            supabase.from('links_anuncios').select('*', { count: 'exact', head: true }).eq('status', 'processado'),
            supabase.from('links_anuncios').select('*', { count: 'exact', head: true }).eq('status', 'pendente'),
            supabase.from('links_anuncios').select('*', { count: 'exact', head: true }).eq('status', 'expirado'),
            supabase.from('imoveis').select('*', { count: 'exact', head: true }).eq('ativo', true).eq('anuncio_expirado', true),
            supabase.from('imoveis').select('*', { count: 'exact', head: true }) // O TOTAL DE LINHAS
        ])
        setLinkStats({
            total: total || 0,
            processado: processado || 0,
            pendente: pendente || 0,
            expirado: expirado || 0,
        })

        // ── Busca de Imóveis (para métricas e distribuição) ────────
        let imoveisAll: any[] = []
        let from = 0
        const PAGE = 1000

        while (true) {
            const { data, error } = await supabase
                .from('imoveis')
                .select('telefone_existe, tipo_imovel, tipo_negocio, aceita_permuta')
                .eq('ativo', true)
                .neq('anuncio_expirado', true)
                .range(from, from + PAGE - 1)

            if (error) {
                console.error('Erro ao buscar imóveis para stats:', error)
                break
            }
            if (!data || data.length === 0) break

            imoveisAll = imoveisAll.concat(data)
            if (data.length < PAGE) break
            from += PAGE
        }

        // ── Status Scraper (Initial Check) ───────────────
        try {
            const response = await fetch('http://localhost:8765/status-execution')
            if (response.ok) {
                const data = await response.json()
                setExecuting(data.executing)
                setIsPaused(data.isPaused)
            }
        } catch (e) {
            console.warn('Scraper offline ou inacessível.')
        }

        const porTipoMap: Record<string, { venda: number; aluguel: number }> = {}
        let com_tel = 0, sem_tel = 0, venda = 0, locacao = 0, aceita = 0, nao_aceita = 0

        imoveisAll.forEach(im => {
            if (im.telefone_existe) com_tel++; else sem_tel++
            const neg = typeof im.tipo_negocio === 'string' ? im.tipo_negocio.trim().toLowerCase() : ''
            const isVenda = neg === 'venda'
            const isLocacao = neg === 'locação' || neg === 'locacao' || neg === 'aluguel'
            if (isVenda) venda++
            else if (isLocacao) locacao++
            const isPermuta = !!im.aceita_permuta && im.aceita_permuta !== 'nao_aceita' && im.aceita_permuta !== 'Não' && im.aceita_permuta !== 'false'
            if (isPermuta) aceita++
            else nao_aceita++
            const tipo = im.tipo_imovel || 'Outros'
            if (!porTipoMap[tipo]) porTipoMap[tipo] = { venda: 0, aluguel: 0 }
            if (isVenda) porTipoMap[tipo].venda++
            else if (isLocacao) porTipoMap[tipo].aluguel++
            else porTipoMap[tipo].venda++
        })

        const por_tipo: TipoItem[] = Object.entries(porTipoMap)
            .map(([tipo, v]) => ({ tipo, venda: v.venda, aluguel: v.aluguel, total: v.venda + v.aluguel }))
            .sort((a, b) => b.total - a.total)
            .slice(0, 15)

        setImovelStats({
            total: imoveisAll.length,
            com_telefone: com_tel,
            sem_telefone: sem_tel,
            por_tipo,
            venda,
            locacao,
            aceita_permuta: aceita,
            nao_aceita_permuta: nao_aceita,
            expirados: expiradosImoveis || 0,
            total_absoluto: totalImoveisAbsoluto || 0
        })

        // ── Kanban ──────────────────────────────────────────
        const { data: colunasComId } = await supabase.from('kanban_colunas').select('id, nome, ordem').order('ordem')
        const { data: imoveisKanban } = await supabase.from('imoveis').select('kanban_coluna_id').not('kanban_coluna_id', 'is', null)

        if (colunasComId && imoveisKanban) {
            const countById: Record<string, number> = {}
            imoveisKanban.forEach(i => {
                if (i.kanban_coluna_id) countById[i.kanban_coluna_id] = (countById[i.kanban_coluna_id] || 0) + 1
            })
            setKanbanStats(colunasComId.map(c => ({ id: c.id, coluna: c.nome, total: countById[c.id] || 0 })).filter(c => c.total > 0))
        }

        await fetchScraperHistory()
        setLoading(false)
    }

    useEffect(() => {
        fetchAll()
    }, [])

    const handleRunExtractor = async () => {
        if (!confirm('Deseja iniciar o ciclo completo de extração de telefones e prospecção? (Lote de 200)')) return

        setExecuting(true)
        setIsPaused(false)
        try {
            const response = await fetch('http://localhost:8765/run', {
                method: 'POST',
            })
            const data = await response.json()
            if (response.ok) {
                toast.success('Extrator iniciado com sucesso!')
            } else {
                toast.error(`Erro ao iniciar: ${data.message || 'Erro desconhecido'}`)
                setExecuting(false)
            }
        } catch (error) {
            toast.error('Não foi possível conectar ao servidor do extrator (Porta 8765).')
            setExecuting(false)
        }
    }

    const handleStop = async () => {
        try {
            const response = await fetch('http://localhost:8765/stop', { method: 'POST' })
            if (response.ok) {
                toast.success('Sinal de parada enviado!')
                setExecuting(false)
                setIsPaused(false)
            }
        } catch (error) {
            toast.error('Erro ao conectar ao servidor para parar.')
        }
    }

    const handlePauseToggle = async () => {
        const endpoint = isPaused ? 'resume' : 'pause'
        try {
            const response = await fetch(`http://localhost:8765/${endpoint}`, { method: 'POST' })
            if (response.ok) {
                setIsPaused(!isPaused)
                toast.success(isPaused ? 'Extração retomada!' : 'Extração pausada!')
            }
        } catch (error) {
            toast.error('Erro ao conectar ao servidor para pausar/retomar.')
        }
    }

    // Polling para sincronizar status e dados do scraper em tempo real
    useEffect(() => {
        let interval: any;

        // Polling constante enquanto o scraper estiver ativo
        const runPolling = async () => {
            try {
                const response = await fetch('http://localhost:8765/status-execution')
                if (response.ok) {
                    const data = await response.json()

                    // Se parou de executar agora: limpa, atualiza tudo uma última vez
                    if (!data.executing && executing) {
                        setExecuting(false)
                        setIsPaused(false)
                        fetchAll() // Atualiza dashboards gerais
                        return
                    }

                    if (data.executing) {
                        setExecuting(true)
                        setIsPaused(data.isPaused)
                        // Atualiza logs e estatísticas parciais sem recarregar a página
                        fetchScraperHistory()
                    }
                }
            } catch (error) {
                console.error('Erro no polling:', error)
            }
        }

        // Se estiver executando, polling a cada 2 segundos para sensação de "tempo real"
        // Se não estiver, polling a cada 10 segundos apenas para detectar início externo
        const delay = executing ? 2000 : 10000;

        interval = setInterval(runPolling, delay)

        // Execução imediata ao mudar estado
        if (executing) runPolling()

        return () => clearInterval(interval)
    }, [executing])

    if (loading) {
        return (
            <div className="loading-screen" style={{ minHeight: 'auto', height: '60vh' }}>
                <div className="spinner" />
                <p>Carregando métricas...</p>
            </div>
        )
    }

    const maxKanban = Math.max(...kanbanStats.map(k => k.total), 1)

    return (
        <div>
            <div style={{ marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.25rem' }}>Dashboard</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Visão geral do CRM Imobiliário</p>
            </div>

            {/* ── Links de Anúncios ── */}
            <SectionTitle>🔗 Links de Anúncios</SectionTitle>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                <MetricCard label="Total de Links (Tabela)" value={linkStats?.total || 0} icon="🔗" color="var(--brand-500)" />
                <MetricCard label="Pendente" value={linkStats?.pendente || 0} icon="⏳" color="var(--warning)" sub="aguardando scraping" />
                <MetricCard label="Processado" value={linkStats?.processado || 0} icon="✅" color="var(--success)" sub="já coletados" />
                <MetricCard label="Expirado" value={linkStats?.expirado || 0} icon="❌" color="var(--error)" sub="anúncios removidos" />
            </div>

            {/* Barra de progresso status */}
            {linkStats && linkStats.total > 0 && (
                <div className="card" style={{ marginTop: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                        <span>✅ {Math.round((linkStats.processado / linkStats.total) * 100)}% processados</span>
                        <span>⏳ {Math.round((linkStats.pendente / linkStats.total) * 100)}% pendentes</span>
                        <span>❌ {Math.round((linkStats.expirado / linkStats.total) * 100)}% expirados</span>
                    </div>
                    <div style={{ height: 10, background: 'var(--border)', borderRadius: 99, overflow: 'hidden', display: 'flex' }}>
                        <div style={{ height: '100%', background: 'var(--success)', width: `${(linkStats.processado / linkStats.total) * 100}%`, transition: 'width 0.6s ease' }} />
                        <div style={{ height: '100%', background: 'var(--warning)', width: `${(linkStats.pendente / linkStats.total) * 100}%`, transition: 'width 0.6s ease' }} />
                        <div style={{ height: '100%', background: 'var(--error)', width: `${(linkStats.expirado / linkStats.total) * 100}%`, transition: 'width 0.6s ease' }} />
                    </div>
                </div>
            )}

            {/* ── Imóveis ── */}
            <SectionTitle>🏠 Imóveis (Base do CRM)</SectionTitle>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                <MetricCard label="Total de Imóveis Ativos" value={imovelStats?.total || 0} icon="🏠" color="var(--brand-500)" />
                <MetricCard label="Total Absoluto (Tabela)" value={imovelStats?.total_absoluto || 0} icon="🗄️" color="var(--border-strong)" sub="total de linhas registradas" />
                <MetricCard label="Com Telefone" value={imovelStats?.com_telefone || 0} icon="📞" color="var(--success)" sub={`${imovelStats?.sem_telefone || 0} sem telefone`} />
                <MetricCard label="Venda" value={imovelStats?.venda || 0} icon="💰" color="var(--gold-400)" />
                <MetricCard label="Locação" value={imovelStats?.locacao || 0} icon="🔑" color="#a78bfa" />
                <MetricCard label="Expirados" value={imovelStats?.expirados || 0} icon="⚠️" color="var(--warning)" sub="removidos da contagem" />
                <MetricCard label="Aceita Permuta" value={imovelStats?.aceita_permuta || 0} icon="🔄" color="var(--success)" />
                <MetricCard label="Não Aceita Permuta" value={imovelStats?.nao_aceita_permuta || 0} icon="🚫" color="var(--error)" />
            </div>

            {/* ── Distribuição por tipo: 2 blocos separados ── */}
            {(imovelStats?.por_tipo?.length || 0) > 0 && (
                <>
                    <SectionTitle>📊 Distribuição por Tipo</SectionTitle>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>

                        {/* ESQUERDA — Aluguel */}
                        <div className="card">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                                <div style={{ width: 10, height: 10, borderRadius: 2, background: '#a78bfa' }} />
                                <span style={{ fontWeight: 700, color: '#a78bfa', fontSize: '0.9rem' }}>🔑 Aluguel</span>
                                <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                                    {imovelStats?.locacao.toLocaleString('pt-BR')} imóveis
                                </span>
                            </div>
                            {(() => {
                                const items = (imovelStats?.por_tipo || []).filter(t => t.aluguel > 0).sort((a, b) => b.aluguel - a.aluguel)
                                const maxVal = Math.max(...items.map(t => t.aluguel), 1)
                                return items.map(({ tipo, aluguel }) => (
                                    <div key={tipo} style={{ marginBottom: '0.85rem' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem', fontSize: '0.82rem' }}>
                                            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{tipo}</span>
                                            <span style={{ color: 'var(--text-muted)' }}>{aluguel}</span>
                                        </div>
                                        <div style={{ height: 6, background: 'var(--border)', borderRadius: 99, overflow: 'hidden' }}>
                                            <div style={{ height: '100%', background: '#a78bfa', width: `${(aluguel / maxVal) * 100}%`, borderRadius: 99, transition: 'width 0.6s ease' }} />
                                        </div>
                                    </div>
                                ))
                            })()}
                        </div>

                        {/* DIREITA — Venda */}
                        <div className="card">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                                <div style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--brand-500)' }} />
                                <span style={{ fontWeight: 700, color: 'var(--brand-500)', fontSize: '0.9rem' }}>💰 Venda</span>
                                <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                                    {imovelStats?.venda.toLocaleString('pt-BR')} imóveis
                                </span>
                            </div>
                            {(() => {
                                const items = (imovelStats?.por_tipo || []).filter(t => t.venda > 0).sort((a, b) => b.venda - a.venda)
                                const maxVal = Math.max(...items.map(t => t.venda), 1)
                                return items.map(({ tipo, venda }) => (
                                    <div key={tipo} style={{ marginBottom: '0.85rem' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem', fontSize: '0.82rem' }}>
                                            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{tipo}</span>
                                            <span style={{ color: 'var(--text-muted)' }}>{venda}</span>
                                        </div>
                                        <div style={{ height: 6, background: 'var(--border)', borderRadius: 99, overflow: 'hidden' }}>
                                            <div style={{ height: '100%', background: 'var(--brand-500)', width: `${(venda / maxVal) * 100}%`, borderRadius: 99, transition: 'width 0.6s ease' }} />
                                        </div>
                                    </div>
                                ))
                            })()}
                        </div>

                    </div>
                </>
            )}

            {/* ── Kanban ── */}
            {kanbanStats.length > 0 && (
                <>
                    <SectionTitle>🗂️ CRM Kanban</SectionTitle>
                    <div className="card">
                        <div style={{ display: 'flex', gap: '1rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
                            {kanbanStats.map(k => (
                                <div key={k.id} style={{
                                    flexShrink: 0, minWidth: 100, textAlign: 'center',
                                    background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)',
                                    padding: '0.75rem 0.5rem', border: '1px solid var(--border)'
                                }}>
                                    <div style={{
                                        height: Math.max(4, Math.round((k.total / maxKanban) * 80)),
                                        background: 'linear-gradient(180deg, var(--brand-500), var(--brand-700))',
                                        borderRadius: 4, marginBottom: '0.5rem', transition: 'height 0.4s ease'
                                    }} />
                                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{k.total}</div>
                                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '0.2rem', wordBreak: 'break-word' }}>
                                        {k.coluna}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}

            {/* ── Funil CRM ── */}
            {kanbanStats.length > 0 && (() => {
                const funil = ['Caixa de Entrada', 'Script 1', 'Script 2', 'Script 3', 'Aceitou', 'Qualificação do Cadastro']
                const funilData = funil.map(nome => ({
                    nome, total: kanbanStats.find(k => k.coluna === nome)?.total || 0
                })).filter(f => f.total > 0)
                if (!funilData.length) return null
                const maxF = Math.max(...funilData.map(f => f.total), 1)
                const colors = ['var(--brand-500)', '#6366f1', '#8b5cf6', '#a78bfa', 'var(--success)', '#34d399']
                return (
                    <>
                        <SectionTitle>🎯 Funil CRM</SectionTitle>
                        <div className="card">
                            {funilData.map((f, i) => (
                                <div key={f.nome} style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                    <div style={{ width: 24, height: 24, borderRadius: '50%', background: colors[i], display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.72rem', fontWeight: 700, flexShrink: 0 }}>
                                        {i + 1}
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.85rem' }}>
                                            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{f.nome}</span>
                                            <span style={{ color: 'var(--text-muted)' }}>{f.total}</span>
                                        </div>
                                        <div style={{ height: 6, background: 'var(--border)', borderRadius: 99, overflow: 'hidden' }}>
                                            <div style={{ height: '100%', borderRadius: 99, background: colors[i], width: `${(f.total / maxF) * 100}%`, transition: 'width 0.6s ease' }} />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )
            })()}
            {/* ── Performance do Scraper ── */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '2.5rem', marginBottom: '1rem' }}>
                <div style={{ marginTop: '-1.5rem' }}>
                    <SectionTitle>🤖 Performance do Scraper</SectionTitle>
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    {!executing ? (
                        <button
                            onClick={handleRunExtractor}
                            style={{
                                padding: '0.4rem 1rem',
                                background: 'var(--brand-500)',
                                color: 'white',
                                border: 'none',
                                borderRadius: 'var(--radius-md)',
                                fontSize: '0.8rem',
                                fontWeight: 700,
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                boxShadow: '0 4px 6px -1px rgba(59,130,246,0.2)',
                                transition: 'all 0.2s',
                            }}
                        >
                            <span>🚀</span>
                            Executar Extração (200 IDs)
                        </button>
                    ) : (
                        <>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginRight: '0.5rem' }}>
                                <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--brand-500)' }}>
                                    {isPaused ? 'Pausado' : 'Em execução...'}
                                </span>
                            </div>

                            <button
                                onClick={handlePauseToggle}
                                style={{
                                    padding: '0.4rem 1rem',
                                    background: isPaused ? 'var(--brand-500)' : '#f59e0b',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: 'var(--radius-md)',
                                    fontSize: '0.8rem',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.4rem',
                                }}
                            >
                                <span>{isPaused ? '▶️' : '⏸️'}</span>
                                {isPaused ? 'Retomar' : 'Pausar'}
                            </button>

                            <button
                                onClick={handleStop}
                                style={{
                                    padding: '0.4rem 1rem',
                                    background: '#ef4444',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: 'var(--radius-md)',
                                    fontSize: '0.8rem',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.4rem',
                                }}
                            >
                                <span>⏹️</span>
                                Parar
                            </button>
                        </>
                    )}
                </div>
            </div>
            {(() => {
                const hojeStr = new Date().toLocaleDateString('pt-BR')
                // @ts-ignore
                const runsHoje = scraperRuns.filter(r => new Date(r.data_inicio).toLocaleDateString('pt-BR') === hojeStr)

                const totalProcessado = runsHoje.reduce((acc: number, r: any) => acc + (r.leads_processados || 0), 0)
                const totalComTel = runsHoje.reduce((acc: number, r: any) => acc + (r.leads_com_telefone || 0), 0)
                const totalExp = runsHoje.reduce((acc: number, r: any) => acc + (r.leads_expirados || 0), 0)
                const totalErros = runsHoje.reduce((acc: number, r: any) => acc + (r.erros || 0), 0)
                const totalBotao = runsHoje.reduce((acc: number, r: any) => acc + (r.encontrados_via_botao || 0), 0)
                const totalDesc = runsHoje.reduce((acc: number, r: any) => acc + (r.encontrados_via_descricao || 0), 0)

                return (
                    <>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                            <MetricCard label="Ciclos Hoje" value={runsHoje.length} icon="🔄" color="var(--brand-500)" />
                            <MetricCard label="Páginas Abertas Hoje" value={totalProcessado} icon="📄" color="#6366f1" />
                            <MetricCard label="Novos Telefones Hoje" value={totalComTel} icon="📱" color="var(--success)" sub={`${totalBotao} botão / ${totalDesc} desc.`} />
                            <MetricCard label="Expirados Hoje" value={totalExp} icon="⚠️" color="var(--warning)" />
                            <MetricCard label="Erros Hoje" value={totalErros} icon="❌" color="var(--error)" />
                        </div>

                        <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: '3rem' }}>
                            <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                    <h3 style={{ fontSize: '0.9rem', fontWeight: 700 }}>Histórico de Ciclos</h3>
                                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: 'var(--bg-app)', padding: '2px 8px', borderRadius: 12, border: '1px solid var(--border)' }}>
                                        Clique na linha para expandir detalhes
                                    </span>
                                </div>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Últimos 50 ciclos</span>
                            </div>
                            <div style={{ overflowX: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                                    <thead>
                                        <tr style={{ background: 'var(--bg-surface)', textAlign: 'left', color: 'var(--text-muted)' }}>
                                            <th style={{ padding: '0.75rem 1rem', width: 40 }}></th>
                                            <th style={{ padding: '0.75rem 1rem' }}>Data/Hora</th>
                                            <th style={{ padding: '0.75rem 1rem' }}>Resumo</th>
                                            <th style={{ padding: '0.75rem 1rem' }}>Com Tel</th>
                                            <th style={{ padding: '0.75rem 1rem' }}>Erros</th>
                                            <th style={{ padding: '0.75rem 1rem' }}>Duração</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {scraperRuns.map(run => {
                                            const inicio = new Date(run.data_inicio)
                                            const fim = run.data_fim ? new Date(run.data_fim) : null
                                            const duracao = fim ? Math.round((fim.getTime() - inicio.getTime()) / 1000) : '-'
                                            const isExpanded = !!expandedCycles[run.id]
                                            const logsDoCiclo = scraperLogs.filter(l => (l as any).estatistica_id === run.id)

                                            return (
                                                <React.Fragment key={run.id}>
                                                    <tr
                                                        onClick={() => toggleCycle(run.id)}
                                                        style={{
                                                            borderTop: '1px solid var(--border)',
                                                            cursor: 'pointer',
                                                            background: isExpanded ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
                                                            transition: 'background 0.2s',
                                                            userSelect: 'none'
                                                        }}
                                                    >
                                                        <td style={{ padding: '0.75rem 1rem', textAlign: 'center', color: isExpanded ? 'var(--brand-500)' : 'var(--text-muted)' }}>
                                                            {isExpanded ? '▼' : '▶'}
                                                        </td>
                                                        <td style={{ padding: '0.75rem 1rem' }}>
                                                            {inicio.toLocaleDateString('pt-BR')} <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{inicio.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</span>
                                                        </td>
                                                        <td style={{ padding: '0.75rem 1rem' }}>
                                                            <strong>Processados: {run.leads_processados}</strong> <span style={{ color: 'var(--text-muted)' }}>(#{run.id})</span>
                                                        </td>
                                                        <td style={{ padding: '0.75rem 1rem', color: 'var(--success)', fontWeight: 700 }}>{run.leads_com_telefone} ✅</td>
                                                        <td style={{ padding: '0.75rem 1rem', color: run.erros > 0 ? 'var(--error)' : 'inherit' }}>{run.erros} ❌</td>
                                                        <td style={{ padding: '0.75rem 1rem' }}>{duracao}s</td>
                                                    </tr>
                                                    {isExpanded && (
                                                        <tr>
                                                            <td colSpan={6} style={{ padding: '0 1rem 1rem 1rem', background: 'rgba(59, 130, 246, 0.02)' }}>
                                                                <div style={{ padding: '1rem', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)' }}>
                                                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                                                                        <thead>
                                                                            <tr style={{ textAlign: 'left', color: 'var(--text-muted)', borderBottom: '1px solid var(--border)' }}>
                                                                                <th style={{ padding: '0.5rem' }}>ID Imóvel</th>
                                                                                <th style={{ padding: '0.5rem' }}>Link</th>
                                                                                <th style={{ padding: '0.5rem' }}>Resultado</th>
                                                                                <th style={{ padding: '0.5rem' }}>Fonte</th>
                                                                                <th style={{ padding: '0.5rem' }}>Duração</th>
                                                                            </tr>
                                                                        </thead>
                                                                        <tbody>
                                                                            {logsDoCiclo.map(log => (
                                                                                <tr key={log.id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                                                                                    <td style={{ padding: '0.5rem' }}>#{log.imovel_id}</td>
                                                                                    <td style={{ padding: '0.5rem' }}>
                                                                                        <a href={log.url} target="_blank" rel="noreferrer" style={{ color: 'var(--brand-500)', textDecoration: 'none' }}>Ver Anúncio 🔗</a>
                                                                                    </td>
                                                                                    <td style={{ padding: '0.5rem' }}>
                                                                                        {log.com_telefone ? <span style={{ color: 'var(--success)', fontWeight: 700 }}>✅ SIM</span> :
                                                                                            log.expirado ? <span style={{ color: 'var(--warning)' }}>⚠️ Expirado</span> :
                                                                                                log.erro ? <span style={{ color: 'var(--error)' }}>❌ Erro</span> :
                                                                                                    <span style={{ color: 'var(--text-muted)' }}>Não encontrado</span>}
                                                                                    </td>
                                                                                    <td style={{ padding: '0.5rem', textTransform: 'capitalize' }}>{log.origem_telefone || '-'}</td>
                                                                                    <td style={{ padding: '0.5rem' }}>{log.duracao_segundos}s</td>
                                                                                </tr>
                                                                            ))}
                                                                            {logsDoCiclo.length === 0 && (
                                                                                <tr>
                                                                                    <td colSpan={5} style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)' }}>Sem detalhes registrados.</td>
                                                                                </tr>
                                                                            )}
                                                                        </tbody>
                                                                    </table>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    )}
                                                </React.Fragment>
                                            )
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                )
            })()}
        </div>
    )
}
