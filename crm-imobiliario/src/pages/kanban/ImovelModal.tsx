import { useState, useRef, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { useAuth } from '../../contexts/AuthContext'
import type { ImovelKanban } from './types'
import { getChatUrl } from './types'
import toast from 'react-hot-toast'

interface Props {
    imovel: ImovelKanban
    onClose: () => void
    onUpdate: (updated: Partial<ImovelKanban>) => void
}

type Aba = 'proprietario' | 'endereco' | 'imovel' | 'fotos' | 'notas' | 'historico'

const PERMUTA_OPTS = [
    { value: 'nao_informado', label: 'Não informado' },
    { value: 'aceita', label: '✅ Aceita' },
    { value: 'nao_aceita', label: '❌ Não aceita' },
] as const

function Field({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="form-group">
            <label className="form-label">{label}</label>
            {children}
        </div>
    )
}


export function ImovelModal({ imovel, onClose, onUpdate }: Props) {
    const { profile } = useAuth()
    const [aba, setAba] = useState<Aba>('proprietario')
    const [editando, setEditando] = useState(false)
    const [saving, setSaving] = useState(false)

    // ── Campos editáveis ──────────────────────────────────────

    // Proprietário
    const [titulo, setTitulo] = useState(imovel.titulo || '')
    const [vendedorNome, setVendedorNome] = useState(imovel.vendedor_nome || '')
    const [vendedorEmail, setVendedorEmail] = useState(imovel.vendedor_email || '')
    const [telefone, setTelefone] = useState(imovel.telefone_mascara || imovel.telefone || '')
    const [whatsapp, setWhatsapp] = useState(imovel.vendedor_whatsapp || '')
    const [autorizado, setAutorizado] = useState(imovel.autorizado ?? false)
    const [comissaoPct, setComissaoPct] = useState(imovel.comissao_pct?.toString() || '')
    const [permuta, setPermuta] = useState(imovel.aceita_permuta)

    // Endereço
    const [rua, setRua] = useState(imovel.rua || '')
    const [numero, setNumero] = useState(imovel.numero || '')
    const [complemento, setComplemento] = useState(imovel.complemento || '')
    const [bairro, setBairro] = useState(imovel.bairro || '')
    const [cidade, setCidade] = useState(imovel.cidade || '')
    const [estado, setEstado] = useState(imovel.estado || '')
    const [cep, setCep] = useState(imovel.cep || '')
    const [emCond, setEmCond] = useState(imovel.em_condominio ?? false)
    const [nomeCond, setNomeCond] = useState(imovel.nome_condominio || '')
    const [bloco, setBloco] = useState(imovel.bloco || '')
    const [numApto, setNumApto] = useState(imovel.numero_apartamento || '')

    // Imóvel
    const [preco, setPreco] = useState(imovel.preco?.toString() || '')
    const [condominio, setCondominio] = useState(imovel.condominio?.toString() || '')
    const [iptu, setIptu] = useState(imovel.iptu?.toString() || '')
    const [areaConstruida, setAreaConstruida] = useState(imovel.area_construida_m2?.toString() || imovel.area_m2?.toString() || '')
    const [areaTerreno, setAreaTerreno] = useState(imovel.area_terreno_m2?.toString() || '')
    const [quartos, setQuartos] = useState(imovel.quartos?.toString() || '')
    const [suites, setSuites] = useState(imovel.suites?.toString() || '')
    const [banheiros, setBanheiros] = useState(imovel.banheiros?.toString() || '')
    const [vagas, setVagas] = useState(imovel.vagas?.toString() || '')
    const [salas, setSalas] = useState(imovel.salas?.toString() || '')
    const [cozinha, setCozinha] = useState(imovel.tem_cozinha ?? true)
    const [outrasCarac, setOutrasCarac] = useState(imovel.outras_caracteristicas || '')

    // Fotos
    const [fotos, setFotos] = useState<string[]>(imovel.fotos || [])
    const [novaFotoUrl, setNovaFotoUrl] = useState('')

    // Notas
    const [notas, setNotas] = useState(imovel.notas_corretor || '')
    const notasTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

    // Fechar Escape
    useEffect(() => {
        const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', h)
        return () => window.removeEventListener('keydown', h)
    }, [onClose])

    // Auto-save notas
    useEffect(() => {
        if (notasTimer.current) clearTimeout(notasTimer.current)
        notasTimer.current = setTimeout(async () => {
            if (notas !== (imovel.notas_corretor || '')) {
                await supabase.from('imoveis').update({ notas_corretor: notas }).eq('id', imovel.id)
                onUpdate({ notas_corretor: notas })
            }
        }, 1200)
        return () => { if (notasTimer.current) clearTimeout(notasTimer.current) }
    }, [notas])

    function handleCancelar() {
        setTitulo(imovel.titulo || '')
        setVendedorNome(imovel.vendedor_nome || '')
        setVendedorEmail(imovel.vendedor_email || '')
        setTelefone(imovel.telefone_mascara || imovel.telefone || '')
        setWhatsapp(imovel.vendedor_whatsapp || '')
        setAutorizado(imovel.autorizado ?? false)
        setComissaoPct(imovel.comissao_pct?.toString() || '')
        setPermuta(imovel.aceita_permuta)
        setRua(imovel.rua || ''); setNumero(imovel.numero || ''); setComplemento(imovel.complemento || '')
        setBairro(imovel.bairro || ''); setCidade(imovel.cidade || ''); setEstado(imovel.estado || ''); setCep(imovel.cep || '')
        setEmCond(imovel.em_condominio ?? false); setNomeCond(imovel.nome_condominio || ''); setBloco(imovel.bloco || ''); setNumApto(imovel.numero_apartamento || '')
        setAreaConstruida(imovel.area_construida_m2?.toString() || imovel.area_m2?.toString() || '')
        setAreaTerreno(imovel.area_terreno_m2?.toString() || '')
        setPreco(imovel.preco?.toString() || '')
        setCondominio(imovel.condominio?.toString() || '')
        setIptu(imovel.iptu?.toString() || '')
        setQuartos(imovel.quartos?.toString() || ''); setSuites(imovel.suites?.toString() || '')
        setBanheiros(imovel.banheiros?.toString() || ''); setVagas(imovel.vagas?.toString() || ''); setSalas(imovel.salas?.toString() || '')
        setCozinha(imovel.tem_cozinha ?? true); setOutrasCarac(imovel.outras_caracteristicas || '')
        setFotos(imovel.fotos || [])
        setEditando(false)
    }

    async function handleSalvar() {
        setSaving(true)
        const fields: Partial<ImovelKanban> = {
            titulo,
            vendedor_nome: vendedorNome || null,
            vendedor_email: vendedorEmail || null,
            telefone: telefone.replace(/\D/g, '') || null,
            telefone_mascara: telefone || null,
            vendedor_whatsapp: whatsapp || null,
            autorizado,
            comissao_pct: comissaoPct ? parseFloat(comissaoPct) : null,
            aceita_permuta: permuta,
            rua: rua || null, numero: numero || null, complemento: complemento || null,
            bairro: bairro || null, cidade: cidade || null, estado: estado || null, cep: cep || null,
            em_condominio: emCond,
            nome_condominio: emCond ? nomeCond || null : null,
            bloco: emCond ? bloco || null : null,
            numero_apartamento: emCond ? numApto || null : null,
            preco: preco ? parseFloat(preco) : null,
            condominio: condominio ? parseFloat(condominio) : null,
            iptu: iptu ? parseFloat(iptu) : null,
            area_construida_m2: areaConstruida ? parseFloat(areaConstruida) : null,
            area_terreno_m2: areaTerreno ? parseFloat(areaTerreno) : null,
            quartos: quartos ? parseInt(quartos) : null,
            suites: suites ? parseInt(suites) : null,
            banheiros: banheiros ? parseInt(banheiros) : null,
            vagas: vagas ? parseInt(vagas) : null,
            salas: salas ? parseInt(salas) : null,
            tem_cozinha: cozinha,
            outras_caracteristicas: outrasCarac || null,
            fotos,
            foto_capa: fotos[0] || imovel.foto_capa,
            // Atribui corretor logado se ainda não tem
            corretor_id: imovel.corretor_id || profile?.id || null,
        }
        const { error } = await supabase.from('imoveis').update(fields).eq('id', imovel.id)
        setSaving(false)
        if (error) { toast.error('Erro ao salvar: ' + error.message); return }
        onUpdate(fields)
        toast.success('✅ Dados salvos!')
        setEditando(false)
    }

    // Fotos
    function addFoto() {
        const url = novaFotoUrl.trim()
        if (!url) return
        setFotos(prev => [...prev, url])
        setNovaFotoUrl('')
    }
    function removeFoto(idx: number) { setFotos(prev => prev.filter((_, i) => i !== idx)) }

    const abas: { id: Aba; label: string }[] = [
        { id: 'proprietario', label: '👤 Proprietário' },
        { id: 'endereco', label: '📍 Endereço' },
        { id: 'imovel', label: '🏠 Imóvel' },
        { id: 'fotos', label: '📷 Fotos' },
        { id: 'notas', label: '📝 Notas' },
        { id: 'historico', label: '📅 Histórico' },
    ]

    const inp = !editando
        ? { readOnly: true, style: { background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)', color: 'var(--text-muted)', padding: '0.65rem 0.9rem', fontFamily: 'Inter, sans-serif', fontSize: '0.88rem', width: '100%', cursor: 'default' } as React.CSSProperties }
        : { readOnly: false }

    return (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
            <div className="modal" style={{ maxWidth: 680 }}>

                {/* ── Header ── */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', marginBottom: '0.75rem' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                        {editando ? (
                            <input className="form-input" value={titulo} onChange={e => setTitulo(e.target.value)}
                                style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.3rem' }} placeholder="Título do imóvel" />
                        ) : (
                            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.2rem', lineHeight: 1.3 }}>
                                {imovel.titulo}
                            </h2>
                        )}
                        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '0.7rem', color: imovel.tipo_negocio === 'venda' ? 'var(--gold-400)' : '#a78bfa', fontWeight: 600, textTransform: 'uppercase' }}>
                                {imovel.tipo_imovel} · {imovel.tipo_negocio}
                            </span>
                            {imovel.autorizado && <span style={{ fontSize: '0.7rem', background: 'rgba(16,185,129,0.15)', color: 'var(--success)', padding: '0.1rem 0.5rem', borderRadius: 99 }}>✅ Autorizado</span>}
                            {imovel.aceita_permuta === 'aceita' && <span style={{ fontSize: '0.7rem', color: 'var(--success)' }}>🔄 Permuta</span>}
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexShrink: 0 }}>
                        <a href={imovel.url} target="_blank" rel="noopener noreferrer"
                            style={{ fontSize: '0.75rem', color: 'var(--brand-500)', textDecoration: 'none' }}>↗ Anúncio</a>
                        <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}>✕</button>
                    </div>
                </div>

                {/* Resumo rápido */}
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    <span style={{ fontWeight: 800, color: 'var(--text-primary)', fontSize: '1.1rem' }}>
                        {imovel.preco_str || (imovel.preco ? `R$ ${imovel.preco.toLocaleString('pt-BR')}` : 'Sob consulta')}
                    </span>
                    {imovel.area_m2 && <span>📐 {imovel.area_m2} m²</span>}
                    {imovel.quartos && <span>🛏️ {imovel.quartos}</span>}
                    {imovel.banheiros && <span>🚿 {imovel.banheiros}</span>}
                    {imovel.vagas && <span>🚗 {imovel.vagas}</span>}
                    {/* Corretor */}
                    {profile && (
                        <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            🧑‍💼 {profile.nome_completo || 'Corretor'}
                            {imovel.comissao_pct && ` · ${imovel.comissao_pct}%`}
                        </span>
                    )}
                </div>

                {/* ── Abas ── */}
                <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border)', marginBottom: '1.25rem', overflowX: 'auto' }}>
                    {abas.map(a => (
                        <button key={a.id} onClick={() => setAba(a.id)} style={{
                            background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap',
                            padding: '0.5rem 0.9rem', fontSize: '0.8rem',
                            fontWeight: aba === a.id ? 600 : 400,
                            color: aba === a.id ? 'var(--brand-500)' : 'var(--text-muted)',
                            borderBottom: aba === a.id ? '2px solid var(--brand-500)' : '2px solid transparent',
                            marginBottom: '-1px', transition: 'color 200ms'
                        }}>{a.label}</button>
                    ))}
                </div>

                {/* ── ABA: PROPRIETÁRIO ── */}
                {aba === 'proprietario' && (
                    <div>
                        <div className="form-row">
                            <Field label="Nome do proprietário">
                                {editando ? <input className="form-input" value={vendedorNome} onChange={e => setVendedorNome(e.target.value)} placeholder="Nome completo" />
                                    : <div style={{ padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)', color: 'var(--text-muted)', fontSize: '0.88rem' }}>{vendedorNome || '—'}</div>}
                            </Field>
                            <Field label="E-mail">
                                {editando ? <input className="form-input" type="email" value={vendedorEmail} onChange={e => setVendedorEmail(e.target.value)} placeholder="email@exemplo.com" />
                                    : <div style={{ padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)', color: 'var(--text-muted)', fontSize: '0.88rem' }}>{vendedorEmail || '—'}</div>}
                            </Field>
                        </div>
                        <div className="form-row">
                            <Field label="Telefone">
                                {editando ? <input className="form-input" value={telefone} onChange={e => setTelefone(e.target.value)} placeholder="(11) 99999-9999" />
                                    : <div style={{ padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)', color: 'var(--text-muted)', fontSize: '0.88rem' }}>{telefone || '—'}</div>}
                            </Field>
                            <Field label="WhatsApp">
                                {editando ? <input className="form-input" value={whatsapp} onChange={e => setWhatsapp(e.target.value)} placeholder="(11) 99999-9999" />
                                    : <div style={{ padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)', color: 'var(--text-muted)', fontSize: '0.88rem' }}>{whatsapp || '—'}</div>}
                            </Field>
                        </div>

                        {/* Autorização */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.9rem', background: autorizado ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)', border: `1px solid ${autorizado ? 'rgba(16,185,129,0.25)' : 'var(--border)'}`, marginBottom: '1rem', cursor: editando ? 'pointer' : 'default' }}
                            onClick={() => editando && setAutorizado(!autorizado)}>
                            <input type="checkbox" checked={autorizado} readOnly disabled={!editando}
                                style={{ width: 18, height: 18, accentColor: 'var(--success)', flexShrink: 0, cursor: editando ? 'pointer' : 'default' }} />
                            <div>
                                <div style={{ fontWeight: 600, color: autorizado ? 'var(--success)' : 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                    {autorizado ? '✅ Proprietário autorizou trabalharmos' : '⏳ Aguardando autorização'}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                    Autorização para intermediar a negociação
                                </div>
                            </div>
                        </div>

                        <div className="form-row">
                            <Field label="Comissão (%)">
                                {editando ? <input className="form-input" type="number" step="0.5" min="0" max="100" value={comissaoPct} onChange={e => setComissaoPct(e.target.value)} placeholder="6" />
                                    : <div style={{ padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)', color: 'var(--text-muted)', fontSize: '0.88rem' }}>{comissaoPct ? `${comissaoPct}%` : '—'}</div>}
                            </Field>
                            <Field label="Aceita permuta?">
                                {editando ? (
                                    <select className="form-select" value={permuta} onChange={e => setPermuta(e.target.value as typeof permuta)}>
                                        {PERMUTA_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                                    </select>
                                ) : <div style={{ padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)', color: 'var(--text-muted)', fontSize: '0.88rem' }}>{PERMUTA_OPTS.find(o => o.value === permuta)?.label}</div>}
                            </Field>
                        </div>

                        {/* Contato rápido quando leitura */}
                        {!editando && (whatsapp || telefone || imovel.ad_id) && (
                            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                                {telephoneLink(telefone)}
                                {whatsapp && <a href={`https://wa.me/55${whatsapp.replace(/\D/g, '')}`} target="_blank" rel="noopener noreferrer"
                                    style={{ background: 'rgba(34,197,94,0.15)', color: '#4ade80', borderRadius: 99, padding: '0.35rem 1rem', fontSize: '0.82rem', textDecoration: 'none', fontWeight: 600 }}>
                                    💬 WhatsApp
                                </a>}
                                {getChatUrl(imovel) && <a href={getChatUrl(imovel)!} target="_blank" rel="noopener noreferrer"
                                    style={{ background: 'rgba(251,191,36,0.15)', color: 'var(--gold-400)', borderRadius: 99, padding: '0.35rem 1rem', fontSize: '0.82rem', textDecoration: 'none', fontWeight: 600 }}>
                                    💬 Chat OLX
                                </a>}
                            </div>
                        )}
                    </div>
                )}

                {/* ── ABA: ENDEREÇO ── */}
                {aba === 'endereco' && (
                    <div>
                        <div className="form-row">
                            <Field label="CEP">
                                {editando ? <input className="form-input" value={cep} onChange={e => setCep(e.target.value)} placeholder="00000-000" /> : <div {...inp}>{cep || '—'}</div>}
                            </Field>
                            <Field label="Estado (UF)">
                                {editando ? <input className="form-input" value={estado} onChange={e => setEstado(e.target.value)} maxLength={2} placeholder="SP" /> : <div {...inp}>{estado || '—'}</div>}
                            </Field>
                        </div>
                        <Field label="Rua / Avenida">
                            {editando ? <input className="form-input" value={rua} onChange={e => setRua(e.target.value)} placeholder="Rua das Flores" /> : <div {...inp}>{rua || '—'}</div>}
                        </Field>
                        <div className="form-row">
                            <Field label="Número">
                                {editando ? <input className="form-input" value={numero} onChange={e => setNumero(e.target.value)} /> : <div {...inp}>{numero || '—'}</div>}
                            </Field>
                            <Field label="Complemento">
                                {editando ? <input className="form-input" value={complemento} onChange={e => setComplemento(e.target.value)} placeholder="Apto 12..." /> : <div {...inp}>{complemento || '—'}</div>}
                            </Field>
                        </div>
                        <div className="form-row">
                            <Field label="Bairro">
                                {editando ? <input className="form-input" value={bairro} onChange={e => setBairro(e.target.value)} /> : <div {...inp}>{bairro || '—'}</div>}
                            </Field>
                            <Field label="Cidade">
                                {editando ? <input className="form-input" value={cidade} onChange={e => setCidade(e.target.value)} /> : <div {...inp}>{cidade || '—'}</div>}
                            </Field>
                        </div>

                        {/* Condomínio */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', marginTop: '0.5rem' }}>
                            <input type="checkbox" id="cond" checked={emCond} onChange={e => editando && setEmCond(e.target.checked)}
                                disabled={!editando} style={{ width: 16, height: 16, accentColor: 'var(--brand-500)', cursor: editando ? 'pointer' : 'default' }} />
                            <label htmlFor="cond" style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', cursor: editando ? 'pointer' : 'default' }}>Em condomínio</label>
                        </div>
                        {emCond && (
                            <>
                                <Field label="Nome do condomínio">
                                    {editando ? <input className="form-input" value={nomeCond} onChange={e => setNomeCond(e.target.value)} /> : <div {...inp}>{nomeCond || '—'}</div>}
                                </Field>
                                <div className="form-row-3">
                                    <Field label="Bloco">
                                        {editando ? <input className="form-input" value={bloco} onChange={e => setBloco(e.target.value)} placeholder="A" /> : <div {...inp}>{bloco || '—'}</div>}
                                    </Field>
                                    <Field label="Nº apartamento">
                                        {editando ? <input className="form-input" value={numApto} onChange={e => setNumApto(e.target.value)} placeholder="101" /> : <div {...inp}>{numApto || '—'}</div>}
                                    </Field>
                                    <div />
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* ── ABA: IMÓVEL ── */}
                {aba === 'imovel' && (
                    <div>
                        <div className="form-row-3">
                            <Field label="Preço (R$)">
                                {editando ? <input className="form-input" type="number" step="1000" value={preco} onChange={e => setPreco(e.target.value)} /> : <div {...inp}>{preco ? `R$ ${Number(preco).toLocaleString('pt-BR')}` : '—'}</div>}
                            </Field>
                            <Field label="Condomínio (R$)">
                                {editando ? <input className="form-input" type="number" step="10" value={condominio} onChange={e => setCondominio(e.target.value)} /> : <div {...inp}>{condominio ? `R$ ${Number(condominio).toLocaleString('pt-BR')}` : '—'}</div>}
                            </Field>
                            <Field label="IPTU (R$)">
                                {editando ? <input className="form-input" type="number" step="10" value={iptu} onChange={e => setIptu(e.target.value)} /> : <div {...inp}>{iptu ? `R$ ${Number(iptu).toLocaleString('pt-BR')}` : '—'}</div>}
                            </Field>
                        </div>
                        <div className="form-row">
                            <Field label="Área construída (m²)">
                                {editando ? <input className="form-input" type="number" value={areaConstruida} onChange={e => setAreaConstruida(e.target.value)} /> : <div {...inp}>{areaConstruida ? `${areaConstruida} m²` : '—'}</div>}
                            </Field>
                            <Field label="Área do terreno (m²)">
                                {editando ? <input className="form-input" type="number" value={areaTerreno} onChange={e => setAreaTerreno(e.target.value)} /> : <div {...inp}>{areaTerreno ? `${areaTerreno} m²` : '—'}</div>}
                            </Field>
                        </div>
                        <div className="form-row-3">
                            <Field label="Quartos">
                                {editando ? <input className="form-input" type="number" min="0" value={quartos} onChange={e => setQuartos(e.target.value)} /> : <div {...inp}>{quartos || '—'}</div>}
                            </Field>
                            <Field label="Suítes">
                                {editando ? <input className="form-input" type="number" min="0" value={suites} onChange={e => setSuites(e.target.value)} /> : <div {...inp}>{suites || '—'}</div>}
                            </Field>
                            <Field label="Banheiros">
                                {editando ? <input className="form-input" type="number" min="0" value={banheiros} onChange={e => setBanheiros(e.target.value)} /> : <div {...inp}>{banheiros || '—'}</div>}
                            </Field>
                        </div>
                        <div className="form-row-3">
                            <Field label="Vagas garage">
                                {editando ? <input className="form-input" type="number" min="0" value={vagas} onChange={e => setVagas(e.target.value)} /> : <div {...inp}>{vagas || '—'}</div>}
                            </Field>
                            <Field label="Salas">
                                {editando ? <input className="form-input" type="number" min="0" value={salas} onChange={e => setSalas(e.target.value)} /> : <div {...inp}>{salas || '—'}</div>}
                            </Field>
                            <Field label="Cozinha">
                                {editando ? (
                                    <select className="form-select" value={cozinha ? 'sim' : 'nao'} onChange={e => setCozinha(e.target.value === 'sim')}>
                                        <option value="sim">✅ Sim</option>
                                        <option value="nao">❌ Não</option>
                                    </select>
                                ) : <div {...inp}>{cozinha ? '✅ Sim' : '❌ Não'}</div>}
                            </Field>
                        </div>
                        <Field label="Outras características">
                            {editando
                                ? <textarea className="form-input" value={outrasCarac} onChange={e => setOutrasCarac(e.target.value)}
                                    placeholder="Piscina, churrasqueira, área de serviço, etc." rows={3}
                                    style={{ resize: 'vertical', fontFamily: 'Inter, sans-serif' }} />
                                : <div {...inp} style={{ ...inp.style, minHeight: 60, whiteSpace: 'pre-wrap' }}>{outrasCarac || '—'}</div>}
                        </Field>
                    </div>
                )}

                {/* ── ABA: FOTOS ── */}
                {aba === 'fotos' && (
                    <div>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                            {fotos.length} foto{fotos.length !== 1 ? 's' : ''} · A primeira foto é usada como capa
                        </p>

                        {/* Grade de fotos */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginBottom: '1rem' }}>
                            {fotos.map((url, i) => (
                                <div key={i} style={{ position: 'relative', borderRadius: 'var(--radius-sm)', overflow: 'hidden', aspectRatio: '4/3', background: 'var(--bg-base)' }}>
                                    <img src={url} alt={`Foto ${i + 1}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                        onError={e => { (e.target as HTMLImageElement).style.opacity = '0.2' }} />
                                    {i === 0 && <span style={{ position: 'absolute', top: 4, left: 4, background: 'rgba(0,0,0,0.7)', color: 'var(--gold-400)', fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: 4 }}>CAPA</span>}
                                    {editando && (
                                        <button onClick={() => removeFoto(i)} style={{
                                            position: 'absolute', top: 4, right: 4, background: 'rgba(239,68,68,0.85)',
                                            border: 'none', borderRadius: '50%', width: 22, height: 22, cursor: 'pointer',
                                            color: '#fff', fontSize: '0.7rem', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center'
                                        }}>✕</button>
                                    )}
                                </div>
                            ))}
                        </div>

                        {/* Adicionar foto por URL */}
                        {editando && (
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <input className="form-input" value={novaFotoUrl} onChange={e => setNovaFotoUrl(e.target.value)}
                                    placeholder="URL da foto (https://...)" style={{ flex: 1 }}
                                    onKeyDown={e => { if (e.key === 'Enter') addFoto() }} />
                                <button className="btn btn-primary" onClick={addFoto} style={{ width: 'auto', padding: '0.65rem 1rem' }}>
                                    + Adicionar
                                </button>
                            </div>
                        )}

                        {!editando && fotos.length === 0 && (
                            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem 0' }}>Nenhuma foto cadastrada</p>
                        )}
                    </div>
                )}

                {/* ── ABA: NOTAS ── */}
                {aba === 'notas' && (
                    <div>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '0.75rem' }}>
                            Auto-salva enquanto você digita ✏️
                        </p>
                        <textarea value={notas} onChange={e => setNotas(e.target.value)}
                            placeholder="Anotações sobre o proprietário, negociação, visita..." rows={10}
                            style={{ width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontFamily: 'Inter, sans-serif', fontSize: '0.9rem', padding: '0.75rem 1rem', resize: 'vertical', outline: 'none' }} />
                    </div>
                )}

                {/* ── ABA: HISTÓRICO ── */}
                {aba === 'historico' && (
                    <div>
                        {(!imovel.historico_kanban?.length) ? (
                            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem 0' }}>Nenhuma movimentação registrada</p>
                        ) : [...imovel.historico_kanban].reverse().map((h, i) => (
                            <div key={i} style={{ display: 'flex', gap: '0.75rem', padding: '0.75rem', marginBottom: '0.5rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                                <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--brand-500)', marginTop: 6, flexShrink: 0 }} />
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '0.87rem' }}>{h.coluna}</div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{new Date(h.data).toLocaleString('pt-BR')}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* ── Rodapé: Editar / Salvar / Cancelar ── */}
                {aba !== 'notas' && aba !== 'historico' && (
                    <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                        {!editando ? (
                            <button className="btn btn-primary" onClick={() => setEditando(true)} style={{ width: 'auto' }}>
                                ✏️ Editar dados
                            </button>
                        ) : (
                            <>
                                <button className="btn btn-primary" onClick={handleSalvar} disabled={saving} style={{ width: 'auto' }}>
                                    {saving ? <><span className="spinner" /> Salvando...</> : '💾 Salvar'}
                                </button>
                                <button className="btn btn-danger" onClick={handleCancelar} disabled={saving} style={{ width: 'auto', padding: '0.8rem 1.25rem' }}>
                                    Cancelar
                                </button>
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}

// Helper para link de telefone
function telephoneLink(tel: string) {
    if (!tel) return null
    return (
        <a href={`tel:${tel.replace(/\D/g, '')}`}
            style={{ background: 'rgba(59,130,246,0.15)', color: 'var(--brand-500)', borderRadius: 99, padding: '0.35rem 1rem', fontSize: '0.82rem', textDecoration: 'none', fontWeight: 600 }}>
            📞 Ligar
        </a>
    )
}
