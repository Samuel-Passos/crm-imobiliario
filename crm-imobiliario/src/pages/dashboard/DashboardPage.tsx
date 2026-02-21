import { useEffect, useState } from 'react'
import { supabase } from '../../lib/supabase'

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
}

interface KanbanStats {
    coluna: string
    id: string
    total: number
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
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        async function fetchAll() {
            // ── Links: COUNT por status via head requests ────────
            const [
                { count: total },
                { count: processado },
                { count: pendente },
                { count: expirado },
            ] = await Promise.all([
                supabase.from('links_anuncios').select('*', { count: 'exact', head: true }),
                supabase.from('links_anuncios').select('*', { count: 'exact', head: true }).eq('status', 'processado'),
                supabase.from('links_anuncios').select('*', { count: 'exact', head: true }).eq('status', 'pendente'),
                supabase.from('links_anuncios').select('*', { count: 'exact', head: true }).eq('status', 'expirado'),
            ])
            setLinkStats({
                total: total || 0,
                processado: processado || 0,
                pendente: pendente || 0,
                expirado: expirado || 0,
            })

            // ── Imóveis: paginação para trazer todos ──────────────
            let imoveisAll: { telefone_existe: boolean; tipo_imovel: string; tipo_negocio: string; aceita_permuta: string }[] = []
            let from = 0
            const PAGE = 1000
            while (true) {
                const { data, error } = await supabase
                    .from('imoveis')
                    .select('telefone_existe, tipo_imovel, tipo_negocio, aceita_permuta')
                    .eq('ativo', true)
                    .range(from, from + PAGE - 1)
                if (error || !data || data.length === 0) break
                imoveisAll = [...imoveisAll, ...data]
                if (data.length < PAGE) break
                from += PAGE
            }

            const porTipoMap: Record<string, { venda: number; aluguel: number }> = {}
            let com_tel = 0, sem_tel = 0, venda = 0, locacao = 0, aceita = 0, nao_aceita = 0

            imoveisAll.forEach(im => {
                if (im.telefone_existe) com_tel++; else sem_tel++
                const neg = im.tipo_negocio || ''
                if (neg === 'venda') venda++
                else if (neg === 'aluguel') locacao++
                if (im.aceita_permuta === 'aceita') aceita++
                else if (im.aceita_permuta === 'nao_aceita') nao_aceita++

                const tipo = im.tipo_imovel || 'Outros'
                if (!porTipoMap[tipo]) porTipoMap[tipo] = { venda: 0, aluguel: 0 }
                if (neg === 'venda') porTipoMap[tipo].venda++
                else if (neg === 'aluguel') porTipoMap[tipo].aluguel++
                else porTipoMap[tipo].venda++
            })

            const por_tipo: TipoItem[] = Object.entries(porTipoMap)
                .map(([tipo, v]) => ({ tipo, venda: v.venda, aluguel: v.aluguel, total: v.venda + v.aluguel }))
                .sort((a, b) => b.total - a.total)
                .slice(0, 7)

            setImovelStats({
                total: imoveisAll.length,
                com_telefone: com_tel,
                sem_telefone: sem_tel,
                por_tipo,
                venda,
                locacao,
                aceita_permuta: aceita,
                nao_aceita_permuta: nao_aceita,
            })

            // ── Kanban ──────────────────────────────────────────
            const { data: colunasComId } = await supabase
                .from('kanban_colunas')
                .select('id, nome, ordem')
                .order('ordem')

            const { data: imoveisKanban } = await supabase
                .from('imoveis')
                .select('kanban_coluna_id')
                .not('kanban_coluna_id', 'is', null)

            if (colunasComId && imoveisKanban) {
                const countById: Record<string, number> = {}
                imoveisKanban.forEach(i => {
                    if (i.kanban_coluna_id) countById[i.kanban_coluna_id] = (countById[i.kanban_coluna_id] || 0) + 1
                })
                setKanbanStats(
                    colunasComId
                        .map(c => ({ id: c.id, coluna: c.nome, total: countById[c.id] || 0 }))
                        .filter(c => c.total > 0)
                )
            }

            setLoading(false)
        }
        fetchAll()
    }, [])

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
                <MetricCard label="Total de Links" value={linkStats?.total || 0} icon="🔗" color="var(--brand-500)" />
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
            <SectionTitle>🏠 Imóveis</SectionTitle>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                <MetricCard label="Total de Imóveis" value={imovelStats?.total || 0} icon="🏠" color="var(--brand-500)" />
                <MetricCard label="Com Telefone" value={imovelStats?.com_telefone || 0} icon="📞" color="var(--success)" sub={`${imovelStats?.sem_telefone || 0} sem telefone`} />
                <MetricCard label="Venda" value={imovelStats?.venda || 0} icon="💰" color="var(--gold-400)" />
                <MetricCard label="Locação" value={imovelStats?.locacao || 0} icon="🔑" color="#a78bfa" />
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
        </div>
    )
}
