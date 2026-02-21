import { useEffect, useState, useCallback } from 'react'
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
function SortableCard({ imovel, onUpdate }: {
    imovel: ImovelKanban
    onUpdate: (u: Partial<ImovelKanban>) => void
}) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
        id: imovel.id,
        data: { type: 'card', coluna: imovel.kanban_coluna_id }
    })
    return (
        <div
            ref={setNodeRef}
            style={{ transform: CSS.Transform.toString(transform), transition, zIndex: isDragging ? 999 : undefined }}
            {...attributes}
            {...listeners}
        >
            <KanbanCard imovel={imovel} onUpdate={onUpdate} isDragging={isDragging} />
        </div>
    )
}

// ── Droppable column ──────────────────────────────────────
function DroppableColuna({ coluna, cards, onUpdate }: {
    coluna: KanbanColuna
    cards: ImovelKanban[]
    onUpdate: (id: number, u: Partial<ImovelKanban>) => void
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
                <SortableContext items={cards.map(c => c.id)} strategy={verticalListSortingStrategy}>
                    {cards.map(card => (
                        <SortableCard key={card.id} imovel={card} onUpdate={u => onUpdate(card.id, u)} />
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
            </div>
        </div>
    )
}

// ── Página principal ──────────────────────────────────────
export function KanbanPage() {
    const [colunas, setColunas] = useState<KanbanColuna[]>([])
    const [imoveis, setImoveis] = useState<ImovelKanban[]>([])
    const [loading, setLoading] = useState(true)
    const [activeCard, setActiveCard] = useState<ImovelKanban | null>(null)
    const [filtros, setFiltros] = useState<FiltrosKanban>({
        tipo_negocio: '', tipo_imovel: '', cidade: '', aceita_permuta: ''
    })

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
            vendedor_nome, telefone, telefone_mascara, vendedor_whatsapp,
            ad_id, foto_capa, fotos,
            vendedor_chat_ativo, vendedor_email, autorizado, comissao_pct,
            area_construida_m2, area_terreno_m2, salas, tem_cozinha,
            outras_caracteristicas, descricao,
            condominio, condominio_str, iptu, iptu_str,
            aceita_permuta, notas_corretor, historico_kanban,
            kanban_coluna_id, kanban_ordem
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

        // Move visualmente sem persistir ainda
        updateImovel(activeId, { kanban_coluna_id: targetColunaId })
    }

    // Ao soltar — persiste no Supabase
    const handleDragEnd = async (e: DragEndEvent) => {
        const card = activeCard
        setActiveCard(null)
        if (!card) return

        const { active } = e
        const imovelAtual = imoveis.find(im => im.id === active.id)
        if (!imovelAtual) return

        const targetColunaId = imovelAtual.kanban_coluna_id
        if (!targetColunaId || targetColunaId === card.kanban_coluna_id) return

        const colunaDestino = colunas.find(c => c.id === targetColunaId)
        if (!colunaDestino) return

        const cardsNaColuna = imoveis.filter(im => im.kanban_coluna_id === targetColunaId && im.id !== card.id)
        const novaOrdem = cardsNaColuna.length + 1
        const historico = [...(card.historico_kanban || []), { coluna: colunaDestino.nome, data: new Date().toISOString() }]

        updateImovel(card.id, { kanban_ordem: novaOrdem, historico_kanban: historico })

        const { error } = await supabase.from('imoveis').update({
            kanban_coluna_id: targetColunaId,
            kanban_ordem: novaOrdem,
            historico_kanban: historico,
        }).eq('id', card.id)

        if (error) {
            toast.error('Erro ao mover card')
            // Reverte para coluna original
            updateImovel(card.id, { kanban_coluna_id: card.kanban_coluna_id, kanban_ordem: card.kanban_ordem })
        } else {
            toast.success(`→ ${colunaDestino.nome}`, { duration: 1500 })
        }
    }

    // ── Filtros ───────────────────────────────────────────────
    const imovelFiltrado = imoveis.filter(im => {
        if (filtros.tipo_negocio && im.tipo_negocio !== filtros.tipo_negocio) return false
        if (filtros.tipo_imovel && im.tipo_imovel !== filtros.tipo_imovel) return false
        if (filtros.cidade && im.cidade !== filtros.cidade) return false
        if (filtros.aceita_permuta && im.aceita_permuta !== filtros.aceita_permuta) return false
        return true
    })

    const cidades = [...new Set(imoveis.map(im => im.cidade).filter(Boolean) as string[])].sort()
    const tipos = [...new Set(imoveis.map(im => im.tipo_imovel).filter(Boolean) as string[])].sort()

    if (loading) return <div className="loading-screen"><div className="spinner" /></div>

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', margin: '-2rem', overflow: 'hidden' }}>
            {/* Header */}
            <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
                <h1 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '0.1rem' }}>CRM Kanban</h1>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                    {imovelFiltrado.length} imóveis · {colunas.length} colunas
                </p>
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
                        const cards = imovelFiltrado
                            .filter(im => im.kanban_coluna_id === col.id)
                            .sort((a, b) => a.kanban_ordem - b.kanban_ordem)
                        return (
                            <DroppableColuna
                                key={col.id}
                                coluna={col}
                                cards={cards}
                                onUpdate={(id, u) => updateImovel(id, u)}
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
