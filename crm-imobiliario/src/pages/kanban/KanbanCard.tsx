import { useState, useEffect, memo } from 'react'
import type { ImovelKanban } from './types'
import { getChatUrl } from './types'
import { ImovelModal } from './ImovelModal'

interface KanbanCardProps {
    imovel: ImovelKanban
    onUpdate: (updated: Partial<ImovelKanban>) => void
    isDragging?: boolean
    onClick?: () => void
}

function formatPreco(preco: number | null, precoStr: string | null): string {
    if (precoStr && precoStr !== 'Preço') return precoStr
    if (preco) return `R$ ${preco.toLocaleString('pt-BR')}`
    return 'Sob consulta'
}

export const KanbanCard = memo(function KanbanCard({ imovel, onUpdate, isDragging, onClick }: KanbanCardProps) {
    const [modalOpen, setModalOpen] = useState(false)

    useEffect(() => {
        const modalIdUrl = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '').get('modal')
        if (modalIdUrl === String(imovel.id)) {
            setModalOpen(true)
        }
    }, [imovel.id])

    // vendedor_whatsapp é boolean — o número de WA é o mesmo de telefone
    const waLink = imovel.vendedor_whatsapp && imovel.telefone
        ? `https://wa.me/55${imovel.telefone.replace(/\D/g, '')}`
        : null
    const chatUrl = getChatUrl(imovel)

    return (
        <>
            <div
                className={`kanban-card ${isDragging ? 'dragging' : ''}`}
                style={{
                    opacity: isDragging ? 0.4 : 1,
                    borderLeft: `3px solid ${imovel.autorizado ? 'var(--success)' : 'transparent'}`,
                    borderTop: `3px solid ${imovel.telefone_pesquisado && !imovel.telefone && !imovel.telefone_mascara && !imovel.anuncio_expirado ? 'var(--error)' : 'transparent'}`,
                }}
                onClick={() => {
                    if (!isDragging) {
                        setModalOpen(true)
                        if (onClick) onClick()
                    }
                }}
            >
                {/* Foto */}
                {imovel.foto_capa && (
                    <div style={{
                        height: 100, borderRadius: 'var(--radius-sm)', overflow: 'hidden',
                        marginBottom: '0.75rem', background: 'var(--bg-base)'
                    }}>
                        <img src={imovel.foto_capa} alt={imovel.titulo} loading="lazy"
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
                    </div>
                )}

                {/* Tipo + permuta */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                    <span style={{
                        fontSize: '0.68rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em',
                        color: imovel.tipo_negocio === 'venda' ? 'var(--gold-400)' : '#a78bfa'
                    }}>
                        {imovel.tipo_imovel || 'Imóvel'} · {imovel.tipo_negocio || '—'}
                    </span>
                    <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center' }}>
                        {imovel.anuncio_expirado && <span title="Anúncio Expirado" style={{ fontSize: '0.6rem', color: 'var(--error)', background: 'rgba(239, 68, 68, 0.15)', padding: '2px 6px', borderRadius: 4, fontWeight: 600 }}>❌ EXPIRADO</span>}
                        {imovel.telefone_pesquisado && !imovel.telefone && !imovel.anuncio_expirado && <span title="Telefone não encontrado" style={{ fontSize: '0.6rem', color: 'var(--text-muted)', background: 'rgba(156, 163, 175, 0.15)', padding: '2px 6px', borderRadius: 4, fontWeight: 600 }}>🚫 S/ TEL</span>}
                        {imovel.telefone_pesquisado && <span title="Processado pelo Robô" style={{ fontSize: '0.6rem', color: 'var(--brand-500)', background: 'rgba(59, 130, 246, 0.1)', padding: '2px 5px', borderRadius: 4, fontWeight: 800 }}>🤖</span>}
                        {imovel.autorizado && <span title="Autorizado" style={{ fontSize: '0.68rem', color: 'var(--success)' }}>✅</span>}
                        {imovel.aceita_permuta === 'aceita' && <span title="Aceita permuta" style={{ fontSize: '0.68rem', color: 'var(--success)' }}>🔄</span>}
                    </div>
                </div>

                {/* Título */}
                <div style={{
                    fontSize: '0.83rem', fontWeight: 600, color: 'var(--text-primary)',
                    marginBottom: '0.25rem', overflow: 'hidden',
                    display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical'
                }}>
                    {imovel.titulo}
                </div>

                {/* Proprietário */}
                {imovel.vendedor_nome && (
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                        👤 {imovel.vendedor_nome}
                    </div>
                )}

                {/* Localização */}
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                    📍 {[imovel.bairro, imovel.cidade].filter(Boolean).join(', ') || '—'}
                </div>

                {/* Preço + Área */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.88rem' }}>
                        {formatPreco(imovel.preco, imovel.preco_str)}
                    </span>
                    {imovel.area_m2 && <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{imovel.area_m2} m²</span>}
                </div>

                {/* Atributos */}
                {(imovel.quartos || imovel.banheiros || imovel.vagas) && (
                    <div style={{ display: 'flex', gap: '0.6rem', fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '0.65rem' }}>
                        {imovel.quartos && <span>🛏️{imovel.quartos}</span>}
                        {imovel.suites && <span>🌟{imovel.suites}</span>}
                        {imovel.banheiros && <span>🚿{imovel.banheiros}</span>}
                        {imovel.vagas && <span>🚗{imovel.vagas}</span>}
                    </div>
                )}

                {/* Rodapé: Contato */}
                <div style={{
                    display: 'flex', gap: '0.4rem', alignItems: 'center',
                    borderTop: '1px solid var(--border)', paddingTop: '0.6rem', flexWrap: 'wrap'
                }} onClick={e => e.stopPropagation()}>
                    {/* WhatsApp */}
                    {waLink && (
                        <a href={waLink} target="_blank" rel="noopener noreferrer" title="WhatsApp"
                            style={{ background: 'rgba(34,197,94,0.15)', color: '#4ade80', borderRadius: 99, padding: '0.2rem 0.55rem', fontSize: '0.68rem', fontWeight: 600, textDecoration: 'none', border: '1px solid rgba(34,197,94,0.25)' }}>
                            WhatsApp
                        </a>
                    )}

                    {/* Chat OLX */}
                    {chatUrl && (
                        <a href={chatUrl} target="_blank" rel="noopener noreferrer" title="Abrir chat OLX"
                            style={{ background: 'rgba(251,191,36,0.15)', color: 'var(--gold-400)', borderRadius: 99, padding: '0.2rem 0.55rem', fontSize: '0.68rem', fontWeight: 600, textDecoration: 'none', border: '1px solid rgba(251,191,36,0.25)' }}>
                            💬 Chat OLX
                        </a>
                    )}

                    {/* Telefone Principal (Fallback se não houver extraídos) */}
                    {imovel.telefone && !waLink && !chatUrl && (!imovel.telefones_extraidos || imovel.telefones_extraidos.length === 0) && (
                        <span style={{ fontSize: '0.68rem', color: 'var(--success)' }}>
                            📞 {imovel.telefone || imovel.telefone_mascara}
                        </span>
                    )}

                    {!imovel.telefone && !waLink && !chatUrl && (!imovel.telefones_extraidos || imovel.telefones_extraidos.length === 0) && (
                        <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Sem contato</span>
                    )}

                    {/* Telefones Extraídos Detalhados */}
                    {imovel.telefones_extraidos && imovel.telefones_extraidos.length > 0 && (
                        <div style={{ width: '100%', display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.4rem' }}>
                            {imovel.telefones_extraidos.map((t, i) => (
                                <span key={i} style={{ fontSize: '0.65rem', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '0.25rem', background: 'rgba(34,197,94,0.08)', padding: '2px 6px', borderRadius: 4 }}>
                                    <span style={{ fontSize: '0.5rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                                        {t.origem || 'Botão'}
                                    </span>
                                    {t.nome ? `${t.nome}: ` : ''} <a href={`https://wa.me/55${t.telefone.replace(/\D/g, '')}`} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'none', fontWeight: 600 }}>{t.telefone}</a>
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Comissão */}
                    {imovel.comissao_pct && (
                        <span style={{ marginLeft: 'auto', fontSize: '0.68rem', color: 'var(--gold-400)', fontWeight: 600 }}>
                            {imovel.comissao_pct}%
                        </span>
                    )}
                </div>

                {/* Nota preview */}
                {imovel.notas_corretor && (
                    <div style={{
                        marginTop: '0.45rem', fontSize: '0.7rem', color: 'var(--text-muted)',
                        fontStyle: 'italic', overflow: 'hidden',
                        display: '-webkit-box', WebkitLineClamp: 1, WebkitBoxOrient: 'vertical'
                    }}>
                        📝 {imovel.notas_corretor}
                    </div>
                )}
            </div>

            {modalOpen && (
                <ImovelModal
                    imovel={imovel}
                    onClose={() => {
                        setModalOpen(false)
                        const currentUrl = new URL(window.location.href)
                        currentUrl.searchParams.delete('modal')
                        window.history.replaceState({}, '', currentUrl.toString())
                    }}
                    onUpdate={u => { onUpdate(u); setModalOpen(false) }}
                />
            )}
        </>
    )
})
