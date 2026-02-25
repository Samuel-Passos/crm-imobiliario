import { useEffect, useState, useCallback, useMemo, memo } from 'react'
import {
    DndContext,
    DragOverlay,
    closestCenter,
    PointerSensor,
    useSensor,
    useSensors,
    useDroppable,
} from '@dnd-kit/core'
import type { DragStartEvent, DragEndEvent, DragOverEvent } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { supabase } from '../../lib/supabase'
import type { ImovelKanban, KanbanColuna, FiltrosKanban } from './types'
import { KanbanCard } from './KanbanCard'
import { KanbanFilters } from './KanbanFilters'
import toast from 'react-hot-toast'

// ── Sortable card wrapper ─────────────────────────────────
const SortableCard = memo(function SortableCard({ imovel, onUpdate }: {
    imovel: ImovelKanban
    onUpdate: (id: number, u: Partial<ImovelKanban>) => void
}) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
        id: imovel.id,
        data: { type: 'card', coluna: imovel.kanban_coluna_id }
    })

    const handleClick = useCallback(() => {
        const urlParams = new URLSearchParams(window.location.search)
        urlParams.set('modal', imovel.id.toString())
        window.history.replaceState({}, '', `${window.location.pathname}?${urlParams.toString()}`)
        // Trigger custom event to open modal
        window.dispatchEvent(new CustomEvent('openModal', { detail: imovel.id.toString() }))
    }, [imovel.id])

    const handleUpdate = useCallback((u: Partial<ImovelKanban>) => {
        onUpdate(imovel.id, u)
    }, [imovel.id, onUpdate])

    return (
        <div
            ref={setNodeRef}
            style={{ transform: CSS.Transform.toString(transform), transition, zIndex: isDragging ? 999 : undefined }}
            {...attributes}
            {...listeners}
        >
            <KanbanCard imovel={imovel} onUpdate={handleUpdate} isDragging={isDragging} onClick={handleClick} />
        </div>
    )
}, (prev, next) => {
    return prev.imovel === next.imovel && prev.onUpdate === next.onUpdate;
})

// ── Droppable column ──────────────────────────────────────
const DroppableColuna = memo(function DroppableColuna({ coluna, cards, allCards, totalCount, onUpdate, onLoadMore }: {
    coluna: KanbanColuna
    cards: ImovelKanban[]
    allCards: ImovelKanban[]
    totalCount: number
    onUpdate: (id: number, u: Partial<ImovelKanban>) => void
    onLoadMore: () => void
}) {
    // A própria coluna é droppable (para cards vindos de outras colunas)
    const { setNodeRef, isOver } = useDroppable({
        id: coluna.id,
        data: { type: 'coluna', colunaId: coluna.id }
    })

    return (
        <div className="kanban-col" style={{ borderRight: '1px solid var(--border)' }}>
            {/* Header */}
            <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '0.75rem 1rem', borderBottom: '1px solid var(--border)',
                position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 1
            }}>
                <span style={{ fontWeight: 700, fontSize: '0.87rem', color: 'var(--text-primary)' }}>
                    {coluna.nome}
                </span>
                <span style={{
                    background: 'rgba(59,130,246,0.15)', color: 'var(--brand-500)',
                    borderRadius: 99, padding: '0.1rem 0.5rem', fontSize: '0.72rem', fontWeight: 700
                }}>
                    {cards.length}
                </span>
            </div>

            {/* Área droppable com lista sortable */}
            <div
                ref={setNodeRef}
                style={{
                    padding: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem',
                    flex: 1, minHeight: 80,
                    background: isOver ? 'rgba(59,130,246,0.05)' : undefined,
                    transition: 'background 150ms'
                }}
            >
                <SortableContext items={allCards.map(c => c.id)} strategy={verticalListSortingStrategy}>
                    {cards.map(card => (
                        <SortableCard key={card.id} imovel={card} onUpdate={onUpdate} />
                    ))}
                </SortableContext>

                {cards.length === 0 && (
                    <div style={{
                        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: 'var(--text-muted)', fontSize: '0.8rem', minHeight: 60, opacity: 0.5
                    }}>
                        Vazio
                    </div>
                )}

                {cards.length > 0 && totalCount > cards.length && (
                    <button
                        onClick={onLoadMore}
                        style={{
                            width: '100%',
                            padding: '0.6rem',
                            marginTop: '0.5rem',
                            background: 'var(--bg-surface)',
                            border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-sm)',
                            color: 'var(--brand-500)',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            gap: '0.5rem',
                            transition: 'all 0.2s',
                        }}
                        onMouseOver={(e) => {
                            e.currentTarget.style.background = 'rgba(59,130,246,0.05)'
                            e.currentTarget.style.borderColor = 'rgba(59,130,246,0.2)'
                        }}
                        onMouseOut={(e) => {
                            e.currentTarget.style.background = 'var(--bg-surface)'
                            e.currentTarget.style.borderColor = 'var(--border)'
                        }}
                    >
                        Carregar mais {totalCount - cards.length} cards ⬇️
                    </button>
                )}
            </div>
        </div>
    )
}, (prev, next) => {
    return prev.coluna === next.coluna &&
        prev.cards === next.cards &&
        prev.totalCount === next.totalCount &&
        prev.onUpdate === next.onUpdate &&
        prev.onLoadMore === next.onLoadMore;
})

// ── Página principal ──────────────────────────────────────
export function KanbanPage() {
    const [colunas, setColunas] = useState<KanbanColuna[]>([])
    const [imoveis, setImoveis] = useState<ImovelKanban[]>([])
    const [loading, setLoading] = useState(true)
    const [executing, setExecuting] = useState(false)
    const [isPaused, setIsPaused] = useState(false)
    const [activeCard, setActiveCard] = useState<ImovelKanban | null>(null)
    const initParams = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '')
    const [filtros, setFiltrosState] = useState<FiltrosKanban>({
        tipo_negocio: (initParams.get('tipo_negocio') || '') as FiltrosKanban['tipo_negocio'],
        tipo_imovel: initParams.get('tipo_imovel') || '',
        cidade: initParams.get('cidade') || '',
        aceita_permuta: (initParams.get('aceita_permuta') || '') as FiltrosKanban['aceita_permuta'],
        telefone_status: (initParams.get('telefone_status') || '') as FiltrosKanban['telefone_status'],
        ordenacao: (initParams.get('ordenacao') || '') as FiltrosKanban['ordenacao'],
        busca: initParams.get('busca') || ''
    })

    // Limits the amount of items shown per column initially to 50
    const [limitesPorColuna, setLimitesPorColuna] = useState<Record<string, number>>({})

    const handleLoadMore = useCallback((colunaId: string) => {
        setLimitesPorColuna(prev => ({
            ...prev,
            [colunaId]: (prev[colunaId] || 50) + 50
        }))
    }, [])

    const setFiltros = (f: FiltrosKanban) => {
        setFiltrosState(f)
        const newParams = new URLSearchParams()
        Object.entries(f).forEach(([key, val]) => {
            if (val) newParams.set(key, val as string)
        })
        const newUrl = `${window.location.pathname}${newParams.toString() ? ('?' + newParams.toString()) : ''}`
        window.history.replaceState({}, '', newUrl)
    }

    const setUrlModalInfo = (id: number | null) => {
        const urlParams = new URLSearchParams(window.location.search)
        if (id !== null) {
            urlParams.set('modal', id.toString())
        } else {
            urlParams.delete('modal')
        }
        const newStr = urlParams.toString()
        window.history.replaceState({}, '', `${window.location.pathname}${newStr ? '?' + newStr : ''}`)
    }

    const handleRunExtractor = async () => {
        if (!confirm('Deseja iniciar o ciclo completo de extração de telefones e prospecção? (Isso rodará em background)')) return

        setExecuting(true)
        setIsPaused(false)
        try {
            const response = await fetch('http://localhost:8765/run', {
                method: 'POST',
            })
            const data = await response.json()
            if (response.ok) {
                toast.success('Extrator iniciado com sucesso em background!')
            } else {
                toast.error(`Erro ao iniciar: ${data.message || 'Erro desconhecido'}`)
                setExecuting(false)
            }
        } catch (error) {
            console.error('Erro ao chamar o scraper:', error)
            toast.error('Não foi possível conectar ao servidor do extrator (FastAPI). Verifique se ele está rodando na porta 8765.')
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

    // Polling para sincronizar status com o backend
    useEffect(() => {
        let interval: any;
        if (executing) {
            interval = setInterval(async () => {
                try {
                    const response = await fetch('http://localhost:8765/status-execution')
                    if (response.ok) {
                        const data = await response.json()
                        // Se o backend diz que NÃO está executando, mas o front acha que está
                        if (!data.executing && executing) {
                            setExecuting(false)
                            setIsPaused(false)
                            clearInterval(interval)
                        } else if (data.isPaused !== isPaused) {
                            setIsPaused(data.isPaused)
                        }
                    }
                } catch (error) {
                    console.error('Erro no polling de status:', error)
                }
            }, 3000)
        }
        return () => clearInterval(interval)
    }, [executing, isPaused])

    // Escutar eventos locais na janela com useCallback pra prevenir deps infinitas
    useEffect(() => {
        const handleOpenModalEvent = (e: CustomEvent<string>) => {
            setUrlModalInfo(Number(e.detail))
        }
        const handleCloseModalEvent = () => {
            setUrlModalInfo(null)
        }
        window.addEventListener('openModal' as any, handleOpenModalEvent)
        window.addEventListener('closeModal' as any, handleCloseModalEvent)

        return () => {
            window.removeEventListener('openModal' as any, handleOpenModalEvent)
            window.removeEventListener('closeModal' as any, handleCloseModalEvent)
        }
    }, [])

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
    )

    // ── Fetch inicial ────────────────────────────────────────
    useEffect(() => {
        async function load() {
            const { data: cols } = await supabase.from('kanban_colunas').select('*').order('ordem')
            if (cols) setColunas(cols)

            let all: ImovelKanban[] = []
            let from = 0
            while (true) {
                const { data } = await supabase
                    .from('imoveis')
                    .select(`
            id, list_id, titulo, url, preco, preco_str,
            tipo_imovel, subtipo, tipo_negocio, area_m2,
            quartos, banheiros, vagas, suites,
            rua, numero, complemento, bairro, cidade, estado, cep,
            em_condominio, nome_condominio, bloco, numero_apartamento,
            latitude, longitude,
            vendedor_nome, telefone_existe, telefone, telefone_mascara, telefones_extraidos, vendedor_whatsapp,
            ad_id, foto_capa, fotos,
            vendedor_chat_ativo, vendedor_email, autorizado, comissao_pct,
            area_construida_m2, area_terreno_m2, salas, tem_cozinha,
            outras_caracteristicas, descricao,
            condominio, condominio_str, iptu, iptu_str,
            origem, aceita_permuta, notas_corretor, historico_kanban,
            kanban_coluna_id, kanban_ordem, telefone_pesquisado, anuncio_expirado
          `)
                    .not('kanban_coluna_id', 'is', null)
                    .eq('ativo', true)
                    .order('kanban_ordem', { ascending: true })
                    .range(from, from + 999)
                if (!data || data.length === 0) break
                all = [...all, ...data as ImovelKanban[]]
                if (data.length < 1000) break
                from += 1000
            }
            setImoveis(all)
            setLoading(false)
        }
        load()

        // Inscreve no Supabase Realtime para ouvir atualizações no banco (ex: scraper em background)
        const channel = supabase.channel('schema-db-changes')
            .on(
                'postgres_changes',
                {
                    event: 'UPDATE',
                    schema: 'public',
                    table: 'imoveis'
                },
                (payload) => {
                    const newImovel = payload.new as Partial<ImovelKanban>
                    if (newImovel.id) {
                        setImoveis(prev => prev.map(im => im.id === newImovel.id ? { ...im, ...newImovel } : im))
                    }
                }
            )
            .subscribe()

        return () => {
            supabase.removeChannel(channel)
        }
    }, [])

    const updateImovel = useCallback((id: number, fields: Partial<ImovelKanban>) => {
        setImoveis(prev => prev.map(im => im.id === id ? { ...im, ...fields } : im))
    }, [])

    // ── DnD handlers ─────────────────────────────────────────
    const handleDragStart = (e: DragStartEvent) => {
        const card = imoveis.find(im => im.id === e.active.id)
        setActiveCard(card || null)
    }

    // Atualiza coluna visualmente enquanto arrasta (drag over)
    const handleDragOver = (e: DragOverEvent) => {
        const { active, over } = e
        if (!over) return

        const activeId = active.id as number
        const overType = over.data.current?.type

        let targetColunaId: string | null = null

        if (overType === 'coluna') {
            targetColunaId = over.data.current?.colunaId as string
        } else if (overType === 'card' || over.data.current?.coluna) {
            targetColunaId = over.data.current?.coluna as string
            // fallback: achar pelo imovel
            if (!targetColunaId) {
                targetColunaId = imoveis.find(im => im.id === over.id)?.kanban_coluna_id || null
            }
        } else {
            // over.id pode ser UUID da coluna
            const isColuna = colunas.some(c => c.id === over.id)
            if (isColuna) targetColunaId = over.id as string
            else targetColunaId = imoveis.find(im => im.id === over.id)?.kanban_coluna_id || null
        }

        const imovel = imoveis.find(im => im.id === activeId)
        if (!imovel || !targetColunaId || imovel.kanban_coluna_id === targetColunaId) return

        // Guardamos de onde ele veio na variável estática em tela caso precise reverter
        if (!activeCard) {
            setActiveCard(imovel)
        }
    }

    // Ao soltar — persiste no Supabase
    const handleDragEnd = async (e: DragEndEvent) => {
        const cardOriginal = activeCard
        setActiveCard(null)
        if (!cardOriginal) return

        const { over } = e
        if (!over) {
            updateImovel(cardOriginal.id, { kanban_coluna_id: cardOriginal.kanban_coluna_id, kanban_ordem: cardOriginal.kanban_ordem })
            return
        }

        const overType = over.data.current?.type
        let targetColunaId: string | null = null

        if (overType === 'coluna') {
            targetColunaId = over.data.current?.colunaId as string
        } else if (overType === 'card' || over.data.current?.coluna) {
            targetColunaId = over.data.current?.coluna as string
            if (!targetColunaId) {
                targetColunaId = imoveis.find(im => im.id === over.id)?.kanban_coluna_id || null
            }
        } else {
            const isColuna = colunas.some(c => c.id === over.id)
            if (isColuna) targetColunaId = over.id as string
            else targetColunaId = imoveis.find(im => im.id === over.id)?.kanban_coluna_id || null
        }

        if (!targetColunaId || targetColunaId === cardOriginal.kanban_coluna_id) {
            // Reverte visual se soltou fora ou na mesma coluna
            updateImovel(cardOriginal.id, { kanban_coluna_id: cardOriginal.kanban_coluna_id, kanban_ordem: cardOriginal.kanban_ordem })
            return
        }

        const colunaDestino = colunas.find(c => c.id === targetColunaId)
        if (!colunaDestino) {
            updateImovel(cardOriginal.id, { kanban_coluna_id: cardOriginal.kanban_coluna_id, kanban_ordem: cardOriginal.kanban_ordem })
            return
        }

        const cardsNaColuna = imoveis.filter(im => im.kanban_coluna_id === targetColunaId && im.id !== cardOriginal.id)
        const novaOrdem = cardsNaColuna.length + 1
        const historico = [...(cardOriginal.historico_kanban || []), { coluna: colunaDestino.nome, data: new Date().toISOString() }]

        // Commit state
        updateImovel(cardOriginal.id, { kanban_coluna_id: targetColunaId, kanban_ordem: novaOrdem, historico_kanban: historico })

        const { error } = await supabase.from('imoveis').update({
            kanban_coluna_id: targetColunaId,
            kanban_ordem: novaOrdem,
            historico_kanban: historico,
        }).eq('id', cardOriginal.id)

        if (error) {
            toast.error('Erro ao mover card')
            // Reverte para coluna original
            updateImovel(cardOriginal.id, { kanban_coluna_id: cardOriginal.kanban_coluna_id, kanban_ordem: cardOriginal.kanban_ordem })
        } else {
            toast.success(`→ ${colunaDestino.nome}`, { duration: 1500 })
        }
    }

    // ── Filtros e Ordenação ───────────────────────────────────────────────
    const imovelFiltrado = useMemo(() => {
        return imoveis.filter(im => {
            if (filtros.tipo_negocio && im.tipo_negocio !== filtros.tipo_negocio) return false
            if (filtros.tipo_imovel && im.tipo_imovel !== filtros.tipo_imovel) return false
            if (filtros.cidade && im.cidade !== filtros.cidade) return false
            if (filtros.aceita_permuta && im.aceita_permuta !== filtros.aceita_permuta) return false

            if (filtros.telefone_status === 'com_telefone' && !im.telefone_existe) return false
            if (filtros.telefone_status === 'sem_telefone' && im.telefone_existe) return false

            if (filtros.busca) {
                const termo = filtros.busca.toLowerCase()
                const matchesId = im.id.toString() === termo
                const matchesAdId = im.ad_id?.toString() === termo
                const matchesListId = im.list_id?.toString() === termo
                const matchesTitulo = im.titulo.toLowerCase().includes(termo)

                if (!matchesId && !matchesAdId && !matchesListId && !matchesTitulo) return false
            }

            return true
        })
    }, [imoveis, filtros])

    const cardsPorColuna = useMemo(() => {
        const map = new Map<string, ImovelKanban[]>()
        colunas.forEach(col => map.set(col.id, []))

        imovelFiltrado.forEach(im => {
            if (im.kanban_coluna_id && map.has(im.kanban_coluna_id)) {
                map.get(im.kanban_coluna_id)!.push(im)
            }
        })

        map.forEach(cards => {
            cards.sort((a, b) => {
                if (filtros.ordenacao === 'recente_antigo') return b.id - a.id // ID maior é mais recente no auto_increment
                if (filtros.ordenacao === 'antigo_recente') return a.id - b.id
                if (filtros.ordenacao === 'preco_maior') return (b.preco || 0) - (a.preco || 0)
                if (filtros.ordenacao === 'preco_menor') return (a.preco || 999999999) - (b.preco || 999999999)
                // Default: Ordem do Quadro Kanban
                return a.kanban_ordem - b.kanban_ordem
            })
        })
        return map
    }, [imovelFiltrado, colunas, filtros.ordenacao])

    const cidades = useMemo(() => [...new Set(imoveis.map(im => im.cidade).filter(Boolean) as string[])].sort(), [imoveis])
    const tipos = useMemo(() => [...new Set(imoveis.map(im => im.tipo_imovel).filter(Boolean) as string[])].sort(), [imoveis])

    if (loading) return <div className="loading-screen"><div className="spinner" /></div>

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', margin: '-2rem', overflow: 'hidden' }}>
            {/* Header */}
            <div style={{
                padding: '1rem 1.5rem',
                borderBottom: '1px solid var(--border)',
                background: 'var(--bg-surface)',
                display: 'flex',
                alignItems: 'center',
                gap: '2rem'
            }}>
                <div>
                    <h1 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '0.1rem' }}>CRM Kanban</h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                        {imovelFiltrado.length} imóveis · {colunas.length} colunas
                    </p>
                </div>

                <div style={{ display: 'flex', gap: '0.75rem' }}>
                    {!executing ? (
                        <button
                            onClick={handleRunExtractor}
                            style={{
                                padding: '0.6rem 1.2rem',
                                background: 'var(--brand-500)',
                                color: 'white',
                                border: 'none',
                                borderRadius: 'var(--radius-md)',
                                fontSize: '0.87rem',
                                fontWeight: 700,
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                boxShadow: '0 4px 6px -1px rgba(59,130,246,0.2)',
                                transition: 'all 0.2s',
                                zIndex: 100,
                            }}
                        >
                            <span>🚀</span>
                            Executar Extrator em Lote
                        </button>
                    ) : (
                        <>
                            <button
                                onClick={handlePauseToggle}
                                style={{
                                    padding: '0.6rem 1.2rem',
                                    background: isPaused ? 'var(--brand-500)' : '#f59e0b',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: 'var(--radius-md)',
                                    fontSize: '0.87rem',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    transition: 'all 0.2s',
                                }}
                            >
                                <span>{isPaused ? '▶️' : '⏸️'}</span>
                                {isPaused ? 'Retomar' : 'Pausar'}
                            </button>

                            <button
                                onClick={handleStop}
                                style={{
                                    padding: '0.6rem 1.2rem',
                                    background: '#ef4444',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: 'var(--radius-md)',
                                    fontSize: '0.87rem',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    transition: 'all 0.2s',
                                }}
                            >
                                <span>⏹️</span>
                                Parar Extração
                            </button>
                        </>
                    )}
                </div>
            </div>

            <KanbanFilters filtros={filtros} onChange={setFiltros} cidades={cidades} tipos={tipos} />

            {/* Board */}
            <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragStart={handleDragStart}
                onDragOver={handleDragOver}
                onDragEnd={handleDragEnd}
            >
                <div className="kanban-board">
                    {colunas.map(col => {
                        const allCards = cardsPorColuna.get(col.id) || []
                        const maxLimit = limitesPorColuna[col.id] || 50
                        const visibleCards = allCards.slice(0, maxLimit)

                        return (
                            <DroppableColuna
                                key={col.id}
                                coluna={col}
                                cards={visibleCards}
                                allCards={allCards}
                                totalCount={allCards.length}
                                onUpdate={updateImovel}
                                onLoadMore={() => handleLoadMore(col.id)}
                            />
                        )
                    })}
                </div>

                <DragOverlay>
                    {activeCard && <KanbanCard imovel={activeCard} onUpdate={() => { }} />}
                </DragOverlay>
            </DndContext>
        </div>
    )
}
