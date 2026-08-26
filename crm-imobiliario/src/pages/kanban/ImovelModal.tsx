import { useState, useRef, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { useAuth } from '../../contexts/AuthContext'
import type { ImovelKanban } from './types'
import { getChatUrl } from './types'
import { LocationPicker } from '../../components/LocationPicker'
import toast from 'react-hot-toast'

interface Props {
    imovel: ImovelKanban
    onClose: () => void
    onUpdate: (updated: Partial<ImovelKanban>) => void
}

type Aba = 'proprietario' | 'endereco' | 'imovel' | 'descricao' | 'fotos' | 'notas' | 'historico'

const PERMUTA_OPTS = [
    { value: 'nao_informado', label: 'Nao informado' },
    { value: 'aceita', label: 'Aceita' },
    { value: 'nao_aceita', label: 'Nao aceita' },
] as const

function Field({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="form-group">
            <label className="form-label">{label}</label>
            {children}
        </div>
    )
}

function telephoneLink(tel: string) {
    if (!tel || tel.includes('.')) return null
    return (
        <a href={`tel:${tel.replace(/\D/g, '')}`}
            style={{ background: 'rgba(59,130,246,0.15)', color: 'var(--brand-500)', borderRadius: 99, padding: '0.3rem 0.85rem', fontSize: '0.8rem', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
            Ligar
        </a>
    )
}

function timeAgo(dateStr: string): string {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const mins = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)
    if (mins < 2) return 'agora mesmo'
    if (mins < 60) return `ha ${mins} min`
    if (hours < 24) return `ha ${hours}h`
    if (days === 1) return 'ontem'
    if (days < 30) return `ha ${days} dias`
    return date.toLocaleDateString('pt-BR')
}

const readonlyStyle: React.CSSProperties = {
    padding: '0.65rem 0.9rem',
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.05)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-muted)',
    fontSize: '0.88rem',
    minHeight: '2.5rem',
    display: 'flex',
    alignItems: 'center',
}

const chipStyle: React.CSSProperties = {
    fontSize: '0.72rem',
    fontWeight: 600,
    color: 'var(--text-secondary)',
    background: 'var(--bg-surface)',
    border: '1px solid var(--border)',
    borderRadius: 99,
    padding: '2px 8px',
    whiteSpace: 'nowrap',
}

export function ImovelModal({ imovel, onClose, onUpdate }: Props) {
    const { profile } = useAuth()
    const [aba, setAba] = useState<Aba>('proprietario')
    const [editando] = useState(true)
    const [saving, setSaving] = useState(false)
    const [buscandoTelefone] = useState(false)
    const [buscandoCep, setBuscandoCep] = useState(false)
    const [calculandoGps, setCalculandoGps] = useState(false)
    const [mostrarMapa, setMostrarMapa] = useState(false)
    const [latitude, setLatitude] = useState(imovel.latitude || null)
    const [longitude, setLongitude] = useState(imovel.longitude || null)
    const [buscandoGeocodaGoogle, setBuscandoGeocodaGoogle] = useState(false)
    const [kanbanColunas, setKanbanColunas] = useState<{ id: string, nome: string }[]>([])

    useEffect(() => {
        supabase.from('kanban_colunas').select('id, nome').order('ordem').then(({ data }) => {
            if (data) setKanbanColunas(data)
        })
    }, [])

    const [titulo, setTitulo] = useState(imovel.titulo || '')
    const [vendedorNome, setVendedorNome] = useState(imovel.vendedor_nome || '')
    const [vendedorEmail, setVendedorEmail] = useState(imovel.vendedor_email || '')
    const [telefone, setTelefone] = useState(imovel.telefone || imovel.telefone_mascara || '')
    const [telefonesExtraidos, setTelefonesExtraidos] = useState<{ origem?: string, telefone: string, nome?: string | null }[]>(imovel.telefones_extraidos || [])
    const [temWhatsapp, setTemWhatsapp] = useState(imovel.vendedor_whatsapp ?? false)
    const [autorizado, setAutorizado] = useState(imovel.autorizado ?? false)
    const [comissaoPct, setComissaoPct] = useState(imovel.comissao_pct?.toString() || '')
    const [permuta, setPermuta] = useState(imovel.aceita_permuta)
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
    const [fotos, setFotos] = useState<string[]>(imovel.fotos || [])
    const [novaFotoUrl, setNovaFotoUrl] = useState('')
    const [notas, setNotas] = useState(imovel.notas_corretor || '')
    const notasTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

    useEffect(() => {
        const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', h)
        return () => window.removeEventListener('keydown', h)
    }, [onClose])

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

    useEffect(() => {
        if (imovel.telefone_pesquisado) {
            if (imovel.telefones_extraidos && imovel.telefones_extraidos.length > 0) {
                setTelefonesExtraidos(imovel.telefones_extraidos)
                if (imovel.telefone && !telefone) setTelefone(imovel.telefone)
            }
        }
    }, [imovel.telefone_pesquisado, imovel.telefones_extraidos, imovel.telefone])

    async function handleBuscarCep(v: string) {
        const apenas = v.replace(/\D/g, '')
        setCep(v)
        if (apenas.length !== 8) return
        setBuscandoCep(true)
        try {
            const res = await fetch(`https://viacep.com.br/ws/${apenas}/json/`)
            const data = await res.json()
            if (!data.erro) {
                setRua(data.logradouro || '')
                setBairro(data.bairro || '')
                setCidade(data.localidade || '')
                setEstado(data.uf || '')
            } else {
                toast.error('CEP nao encontrado')
            }
        } catch {
            toast.error('Erro ao buscar CEP')
        } finally {
            setBuscandoCep(false)
        }
    }

    async function handleRevisarGoogle() {
        if (buscandoGeocodaGoogle) return
        setBuscandoGeocodaGoogle(true)
        const loadingToast = toast.loading('Consultando Google Maps...')
        try {
            const res = await fetch('http://127.0.0.1:8765/geocode/google/single', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ imovel_id: imovel.id })
            })
            if (!res.ok) throw new Error('Servidor de geocodificacao offline')
            const data = await res.json()
            if (data.sucesso) {
                setLatitude(data.coords.lat)
                setLongitude(data.coords.lng)
                toast.success('Localizacao atualizada via Google!', { id: loadingToast })
            } else {
                toast.error(data.erro || 'Falha ao geocodificar', { id: loadingToast })
            }
        } catch (err) {
            toast.error('Erro de conexao com o motor Google.', { id: loadingToast })
        } finally {
            setBuscandoGeocodaGoogle(false)
        }
    }

    async function obterCoordenadas(log: string, num: string, cid: string, est: string): Promise<{ lat: number; lng: number } | null> {
        if (!log || !cid) return null
        setCalculandoGps(true)
        try {
            const query = encodeURIComponent(`${log}, ${num}, ${cid} - ${est}, Brasil`)
            const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${query}&limit=1`, {
                headers: { 'User-Agent': 'CRM-Imobiliario-App-Samuel' }
            })
            const data = await res.json()
            if (data && data.length > 0) {
                return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) }
            }
        } catch (e) {
            console.error('Erro no geocoding:', e)
        } finally {
            setCalculandoGps(false)
        }
        return null
    }

    function handleCancelar() {
        setTitulo(imovel.titulo || '')
        setVendedorNome(imovel.vendedor_nome || '')
        setVendedorEmail(imovel.vendedor_email || '')
        setTelefone(imovel.telefone || imovel.telefone_mascara || '')
        setTelefonesExtraidos(imovel.telefones_extraidos || [])
        setTemWhatsapp(imovel.vendedor_whatsapp ?? false)
        setAutorizado(imovel.autorizado ?? false)
        setComissaoPct(imovel.comissao_pct?.toString() || '')
        setPermuta(imovel.aceita_permuta)
        setRua(imovel.rua || ''); setNumero(imovel.numero || ''); setComplemento(imovel.complemento || '')
        setBairro(imovel.bairro || ''); setCidade(imovel.cidade || ''); setEstado(imovel.estado || ''); setCep(imovel.cep || '')
        setEmCond(imovel.em_condominio ?? false); setNomeCond(imovel.nome_condominio || ''); setBloco(imovel.bloco || ''); setNumApto(imovel.numero_apartamento || '')
        setAreaConstruida(imovel.area_construida_m2?.toString() || imovel.area_m2?.toString() || '')
        setAreaTerreno(imovel.area_terreno_m2?.toString() || '')
        setPreco(imovel.preco?.toString() || ''); setCondominio(imovel.condominio?.toString() || ''); setIptu(imovel.iptu?.toString() || '')
        setQuartos(imovel.quartos?.toString() || ''); setSuites(imovel.suites?.toString() || '')
        setBanheiros(imovel.banheiros?.toString() || ''); setVagas(imovel.vagas?.toString() || ''); setSalas(imovel.salas?.toString() || '')
        setCozinha(imovel.tem_cozinha ?? true); setOutrasCarac(imovel.outras_caracteristicas || '')
        setFotos(imovel.fotos || [])
    }

    async function handleSalvar() {
        setSaving(true)
        let lat = latitude
        let lng = longitude
        if (!mostrarMapa && rua && cidade && (rua !== imovel.rua || cidade !== imovel.cidade || !lat)) {
            const coords = await obterCoordenadas(rua, numero, cidade, estado)
            if (coords) { lat = coords.lat; lng = coords.lng }
        }
        const fields: Partial<ImovelKanban> = {
            titulo,
            vendedor_nome: vendedorNome || null,
            vendedor_email: vendedorEmail || null,
            telefone: telefone.replace(/\D/g, '') || null,
            telefone_mascara: telefone || null,
            telefones_extraidos: telefonesExtraidos.length > 0 ? telefonesExtraidos.map(t => ({ ...t, nome: t.nome || null })) : undefined,
            vendedor_whatsapp: temWhatsapp,
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
            latitude: lat,
            longitude: lng,
            corretor_id: imovel.corretor_id || profile?.id || null,
        }
        const { error } = await supabase.from('imoveis').update(fields).eq('id', imovel.id)
        setSaving(false)
        if (error) { toast.error('Erro ao salvar: ' + error.message); return }
        onUpdate(fields)
        toast.success('Dados salvos!')
    }

    function addFoto() {
        const url = novaFotoUrl.trim()
        if (!url) return
        setFotos(prev => [...prev, url])
        setNovaFotoUrl('')
    }
    function removeFoto(idx: number) { setFotos(prev => prev.filter((_, i) => i !== idx)) }

    type TimelineEntry = {
        type: 'kanban' | 'telefone' | 'expirado' | 'autorizado'
        label: string
        sublabel?: string
        date?: string
        icon: string
        color: string
    }

    const buildTimeline = (): TimelineEntry[] => {
        const entries: TimelineEntry[] = []
        if (imovel.historico_kanban?.length) {
            imovel.historico_kanban.forEach(h => {
                entries.push({ type: 'kanban', label: h.coluna, sublabel: 'Movido para esta coluna', date: h.data, icon: 'coluna', color: 'var(--brand-500)' })
            })
        }
        if (imovel.autorizado) {
            entries.push({ type: 'autorizado', label: 'Proprietario autorizou', sublabel: 'Autorizacao para intermediar a negociacao', icon: 'autorizado', color: 'var(--success)' })
        }
        if (imovel.anuncio_expirado) {
            entries.push({ type: 'expirado', label: 'Anuncio expirado na OLX', sublabel: 'Detectado pelo robo de varredura', icon: 'expirado', color: '#ef4444' })
        }
        if (imovel.telefone_pesquisado) {
            entries.push({
                type: 'telefone',
                label: imovel.telefone ? `Telefone extraido: ${imovel.telefone_mascara || imovel.telefone}` : 'Telefone pesquisado - nao encontrado',
                sublabel: 'Extracao automatica via robo OLX',
                icon: 'telefone',
                color: imovel.telefone ? '#4ade80' : 'var(--text-muted)',
            })
        }
        return entries.sort((a, b) => {
            if (!a.date && !b.date) return 0
            if (!a.date) return -1
            if (!b.date) return 1
            return new Date(b.date).getTime() - new Date(a.date).getTime()
        })
    }

    const getTimelineIcon = (type: string) => {
        if (type === 'kanban') return '📌'
        if (type === 'autorizado') return '✅'
        if (type === 'expirado') return '❌'
        if (type === 'telefone') return '📞'
        return '•'
    }

    const abas: { id: Aba; label: string }[] = [
        { id: 'proprietario', label: 'Proprietario' },
        { id: 'endereco', label: 'Endereco' },
        { id: 'imovel', label: 'Imovel' },
        { id: 'descricao', label: 'Descricao' },
        { id: 'fotos', label: 'Fotos' },
        { id: 'notas', label: 'Notas' },
        { id: 'historico', label: 'Historico' },
    ]

    const inp = !editando
        ? { readOnly: true, style: readonlyStyle }
        : { readOnly: false }

    const fotoCapa = fotos[0] || imovel.foto_capa

    return (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
            <div className="modal" style={{ maxWidth: 720 }}>

                {/* HEADER */}
                <div style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>

                        {/* Thumbnail */}
                        <div style={{ width: 72, height: 72, flexShrink: 0, borderRadius: 'var(--radius-md)', overflow: 'hidden', background: 'var(--bg-base)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            {fotoCapa
                                ? <img src={fotoCapa} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} referrerPolicy="no-referrer" />
                                : <span style={{ fontSize: '1.8rem', opacity: 0.2 }}>🏠</span>
                            }
                        </div>

                        {/* Titulo + badges */}
                        <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
                                <span title="Clique para copiar ID" onClick={() => { navigator.clipboard.writeText(String(imovel.id)); toast.success('ID copiado!') }}
                                    style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700, cursor: 'pointer', background: 'var(--bg-base)', padding: '2px 8px', borderRadius: 99, border: '1px solid var(--border)', flexShrink: 0 }}>
                                    #{imovel.id}
                                </span>
                                {imovel.tipo_negocio && (
                                    <span style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: imovel.tipo_negocio === 'venda' ? '#fbbf24' : '#a78bfa', background: imovel.tipo_negocio === 'venda' ? 'rgba(251,191,36,0.12)' : 'rgba(167,139,250,0.12)', padding: '2px 8px', borderRadius: 99, flexShrink: 0 }}>
                                        {imovel.tipo_negocio === 'venda' ? 'Venda' : 'Aluguel'}
                                    </span>
                                )}
                                {imovel.tipo_imovel && (
                                    <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', background: 'var(--bg-surface)', padding: '2px 8px', borderRadius: 99, border: '1px solid var(--border)', flexShrink: 0 }}>
                                        {imovel.tipo_imovel}
                                    </span>
                                )}
                                {imovel.autorizado && <span style={{ fontSize: '0.7rem', fontWeight: 700, background: 'rgba(16,185,129,0.15)', color: 'var(--success)', padding: '2px 8px', borderRadius: 99, flexShrink: 0 }}>Autorizado</span>}
                                {imovel.anuncio_expirado && <span style={{ fontSize: '0.7rem', fontWeight: 700, background: 'rgba(239,68,68,0.12)', color: '#ef4444', padding: '2px 8px', borderRadius: 99, flexShrink: 0 }}>Expirado</span>}
                            </div>

                            {editando ? (
                                <input className="form-input" value={titulo} onChange={e => setTitulo(e.target.value)}
                                    style={{ fontSize: '0.97rem', fontWeight: 700, marginBottom: '0.4rem' }} placeholder="Titulo do imovel" />
                            ) : (
                                <div style={{ fontSize: '0.97rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.35, marginBottom: '0.4rem' }}>
                                    {imovel.titulo}
                                </div>
                            )}

                            <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
                                <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--brand-500)', lineHeight: 1 }}>
                                    {imovel.preco_str || (imovel.preco ? `R$ ${imovel.preco.toLocaleString('pt-BR')}` : 'Sob consulta')}
                                </span>
                                {imovel.area_m2 && <span style={chipStyle}>{imovel.area_m2} m²</span>}
                                {imovel.quartos && <span style={chipStyle}>{imovel.quartos} quartos</span>}
                                {imovel.banheiros && <span style={chipStyle}>{imovel.banheiros} banh.</span>}
                                {imovel.vagas && <span style={chipStyle}>{imovel.vagas} vagas</span>}
                                {profile && imovel.comissao_pct && <span style={{ ...chipStyle, color: '#4ade80', background: 'rgba(74,222,128,0.1)', borderColor: 'rgba(74,222,128,0.2)' }}>{imovel.comissao_pct}% com.</span>}
                            </div>
                        </div>

                        {/* Acoes do header */}
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start', flexShrink: 0 }}>
                            {kanbanColunas.length > 0 && (
                                <select className="form-select" value={imovel.kanban_coluna_id || ''}
                                    onChange={async (e) => {
                                        const newCol = e.target.value
                                        const { error } = await supabase.from('imoveis').update({ kanban_coluna_id: newCol }).eq('id', imovel.id)
                                        if (!error) { onUpdate({ kanban_coluna_id: newCol }); toast.success('Imovel movido!') }
                                        else toast.error('Erro ao mover')
                                    }}
                                    style={{ padding: '0.3rem 1.8rem 0.3rem 0.6rem', fontSize: '0.75rem', width: 'auto', height: 'auto', backgroundPosition: 'right 0.4rem center' }}
                                >
                                    <option value="" disabled style={{ background: 'var(--bg-surface)' }}>Mover para...</option>
                                    {kanbanColunas.map(c => (
                                        <option key={c.id} value={c.id} style={{ background: 'var(--bg-surface)', color: 'var(--text-primary)' }}>{c.nome}</option>
                                    ))}
                                </select>
                            )}
                            {imovel.url && (
                                <a href={imovel.url} target="_blank" rel="noopener noreferrer"
                                    style={{ fontSize: '0.78rem', color: 'var(--brand-500)', textDecoration: 'none', background: 'rgba(59,130,246,0.1)', padding: '0.3rem 0.7rem', borderRadius: 99, border: '1px solid rgba(59,130,246,0.2)', fontWeight: 600, whiteSpace: 'nowrap' }}>
                                    Anuncio
                                </a>
                            )}
                            <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem', lineHeight: 1, padding: '0.3rem', borderRadius: '50%' }}>x</button>
                        </div>
                    </div>
                </div>

                {/* ABAS */}
                <div style={{ display: 'flex', gap: 0, borderBottom: '2px solid var(--border)', marginBottom: '1.25rem', overflowX: 'auto' }}>
                    {abas.map(a => (
                        <button key={a.id} onClick={() => setAba(a.id)} style={{
                            background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap',
                            padding: '0.55rem 0.85rem', fontSize: '0.8rem',
                            fontWeight: aba === a.id ? 700 : 400,
                            color: aba === a.id ? 'var(--brand-500)' : 'var(--text-muted)',
                            borderBottom: aba === a.id ? '2px solid var(--brand-500)' : '2px solid transparent',
                            marginBottom: '-2px', transition: 'color 150ms'
                        }}>{a.label}</button>
                    ))}
                </div>

                {/* ABA: PROPRIETARIO */}
                {aba === 'proprietario' && (
                    <div>
                        <div className="form-row">
                            <Field label="Nome do proprietario">
                                {editando ? <input className="form-input" value={vendedorNome} onChange={e => setVendedorNome(e.target.value)} placeholder="Nome completo" />
                                    : <div style={readonlyStyle}>{vendedorNome || '-'}</div>}
                            </Field>
                            <Field label="E-mail">
                                {editando ? <input className="form-input" type="email" value={vendedorEmail} onChange={e => setVendedorEmail(e.target.value)} placeholder="email@exemplo.com" />
                                    : <div style={readonlyStyle}>{vendedorEmail || '-'}</div>}
                            </Field>
                        </div>

                        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                            <div style={{ flex: 2, minWidth: '200px', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                                {(telefonesExtraidos && telefonesExtraidos.length > 0) ? (
                                    telefonesExtraidos.map((t, idx) => {
                                        const origName = t.origem ? t.origem.charAt(0).toUpperCase() + t.origem.slice(1) : 'Botao'
                                        const labelBase = telefonesExtraidos.length === 1 ? 'Telefone' : `Telefone ${origName}`
                                        return (
                                            <Field key={idx} label={labelBase}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                                                    {telephoneLink(t.telefone)}
                                                    <a href={`https://wa.me/55${t.telefone.replace(/\D/g, '')}`} target="_blank" rel="noopener noreferrer"
                                                        style={{ background: 'rgba(34,197,94,0.15)', color: '#4ade80', borderRadius: 99, padding: '0.3rem 0.85rem', fontSize: '0.8rem', textDecoration: 'none', fontWeight: 600 }}>
                                                        WhatsApp
                                                    </a>
                                                    <input className="form-input" value={t.telefone}
                                                        onChange={e => {
                                                            const arr = [...telefonesExtraidos]
                                                            arr[idx] = { ...arr[idx], telefone: e.target.value }
                                                            setTelefonesExtraidos(arr)
                                                            if (idx === 0) setTelefone(e.target.value)
                                                        }}
                                                        style={{ flex: 1, minWidth: '130px' }} />
                                                </div>
                                            </Field>
                                        )
                                    })
                                ) : (
                                    <Field label="Telefone">
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                                            {telefone && telephoneLink(telefone)}
                                            {telefone && temWhatsapp && (
                                                <a href={`https://wa.me/55${telefone.replace(/\D/g, '')}`} target="_blank" rel="noopener noreferrer"
                                                    style={{ background: 'rgba(34,197,94,0.15)', color: '#4ade80', borderRadius: 99, padding: '0.3rem 0.85rem', fontSize: '0.8rem', textDecoration: 'none', fontWeight: 600 }}>
                                                    WhatsApp
                                                </a>
                                            )}
                                            <input className="form-input" value={telefone} onChange={e => setTelefone(e.target.value)} placeholder="(11) 99999-9999" style={{ flex: 1, minWidth: '130px' }} />
                                            {imovel.telefone_pesquisado && !telefone && <span style={{ fontSize: '0.75rem', color: '#ef4444', fontWeight: 600 }}>Nenhum na OLX</span>}
                                            {buscandoTelefone && (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', color: '#a78bfa' }}>
                                                    <span className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
                                                    Buscando...
                                                </div>
                                            )}
                                        </div>
                                    </Field>
                                )}
                            </div>

                            <div style={{ flex: 1, minWidth: '130px' }}>
                                <Field label="WhatsApp">
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.65rem 0.9rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)', cursor: editando ? 'pointer' : 'default' }}
                                        onClick={() => editando && setTemWhatsapp(!temWhatsapp)}>
                                        <input type="checkbox" checked={temWhatsapp} readOnly disabled={!editando} style={{ width: 14, height: 14, accentColor: '#4ade80', cursor: editando ? 'pointer' : 'default' }} />
                                        <span style={{ fontSize: '0.8rem', color: temWhatsapp ? '#4ade80' : 'var(--text-muted)' }}>
                                            {temWhatsapp ? 'Ativo' : 'Sem Wpp'}
                                        </span>
                                    </div>
                                </Field>
                            </div>
                        </div>

                        {/* Autorizacao */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.9rem', background: autorizado ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)', border: `1px solid ${autorizado ? 'rgba(16,185,129,0.25)' : 'var(--border)'}`, marginBottom: '1rem', cursor: editando ? 'pointer' : 'default' }}
                            onClick={() => editando && setAutorizado(!autorizado)}>
                            <input type="checkbox" checked={autorizado} readOnly disabled={!editando} style={{ width: 18, height: 18, accentColor: 'var(--success)', flexShrink: 0, cursor: editando ? 'pointer' : 'default' }} />
                            <div>
                                <div style={{ fontWeight: 600, color: autorizado ? 'var(--success)' : 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                    {autorizado ? 'Proprietario autorizou trabalharmos' : 'Aguardando autorizacao'}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Autorizacao para intermediar a negociacao</div>
                            </div>
                        </div>

                        <div className="form-row">
                            <Field label="Comissao (%)">
                                {editando ? <input className="form-input" type="number" step="0.5" min="0" max="100" value={comissaoPct} onChange={e => setComissaoPct(e.target.value)} placeholder="6" />
                                    : <div style={readonlyStyle}>{comissaoPct ? `${comissaoPct}%` : '-'}</div>}
                            </Field>
                            <Field label="Aceita permuta?">
                                {editando ? (
                                    <select className="form-select" value={permuta} onChange={e => setPermuta(e.target.value as typeof permuta)}>
                                        {PERMUTA_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                                    </select>
                                ) : <div style={readonlyStyle}>{PERMUTA_OPTS.find(o => o.value === permuta)?.label}</div>}
                            </Field>
                        </div>

                        {/* Contato rapido */}
                        {(imovel.ad_id || imovel.url) && (
                            <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.75rem', flexWrap: 'wrap', alignItems: 'center', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
                                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginRight: '0.25rem' }}>Contato rapido</span>
                                {getChatUrl(imovel) && (
                                    <a href={getChatUrl(imovel)!} target="_blank" rel="noopener noreferrer"
                                        style={{ background: 'rgba(251,191,36,0.15)', color: '#fbbf24', borderRadius: 99, padding: '0.35rem 1rem', fontSize: '0.82rem', textDecoration: 'none', fontWeight: 600 }}>
                                        Chat OLX
                                    </a>
                                )}
                                {imovel.anuncio_expirado && <span style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', borderRadius: 99, padding: '0.35rem 1rem', fontSize: '0.82rem', fontWeight: 600 }}>Anuncio Expirado</span>}
                                {imovel.telefone_pesquisado && (!telefone || telefone.includes('.')) && !imovel.anuncio_expirado && (
                                    <span style={{ background: 'rgba(156,163,175,0.1)', color: 'var(--text-muted)', borderRadius: 99, padding: '0.35rem 1rem', fontSize: '0.82rem', fontWeight: 600 }}>
                                        S/ Telefone
                                    </span>
                                )}
                            </div>
                        )}

                        {/* Importar como contato */}
                        {vendedorNome && (
                            <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                                <button
                                    onClick={async () => {
                                        const { supabase: sb } = await import('../../lib/supabase')
                                        const payload = {
                                            nome_completo: vendedorNome || 'Sem nome',
                                            telefone: telefone && !telefone.includes('.') ? telefone : null,
                                            whatsapp: temWhatsapp && telefone && !telefone.includes('.') ? telefone : null,
                                            email: imovel.vendedor_email || null,
                                            tipo_contato: 'proprietario',
                                            cidade: imovel.cidade || null,
                                            estado: imovel.estado || null,
                                            bairro: imovel.bairro || null,
                                            logradouro: imovel.rua || null,
                                            numero: imovel.numero || null,
                                            cep: imovel.cep || null,
                                            origem: 'OLX',
                                            vinculo_imovel_id: String(imovel.id),
                                        }
                                        const { error } = await sb.from('contatos').insert(payload)
                                        if (error) {
                                            toast.error(error.code === '23505' ? 'Proprietario ja importado como contato.' : 'Erro ao importar: ' + error.message)
                                        } else {
                                            toast.success('Proprietario importado como Contato!')
                                        }
                                    }}
                                    style={{ background: 'rgba(59,130,246,0.12)', color: 'var(--brand-500)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: 'var(--radius-sm)', padding: '0.5rem 1rem', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
                                >
                                    Importar proprietario como Contato
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* ABA: ENDERECO */}
                {aba === 'endereco' && (
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                                Localizacao {buscandoCep && '...'}
                            </div>
                            <div style={{ display: 'flex', gap: '1rem' }}>
                                <button type="button" onClick={handleRevisarGoogle} disabled={buscandoGeocodaGoogle}
                                    style={{ background: 'none', border: 'none', color: buscandoGeocodaGoogle ? 'var(--text-muted)' : '#6366f1', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    {buscandoGeocodaGoogle ? 'Consultando...' : 'Corrigir com Google'}
                                </button>
                                <button type="button" onClick={() => setMostrarMapa(!mostrarMapa)}
                                    style={{ background: 'none', border: 'none', color: 'var(--brand-500)', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}>
                                    {mostrarMapa ? 'Ocultar Mapa' : 'Visualizar/Ajustar no Mapa'}
                                </button>
                            </div>
                        </div>
                        {mostrarMapa && (
                            <LocationPicker initialLat={latitude} initialLng={longitude}
                                onLocationSelected={({ lat, lng, address }) => {
                                    setLatitude(lat); setLongitude(lng)
                                    if (address) {
                                        if (address.road) setRua(address.road)
                                        if (address.suburb || address.neighbourhood) setBairro(address.suburb || address.neighbourhood)
                                        if (address.city || address.town || address.village) setCidade(address.city || address.town || address.village)
                                        if (address.state) setEstado(address.state)
                                        if (address.postcode) setCep(address.postcode)
                                        if (address.house_number) setNumero(address.house_number)
                                    }
                                }}
                            />
                        )}
                        <div className="form-row">
                            <Field label="CEP">
                                {editando ? <input className="form-input" value={cep} onChange={e => handleBuscarCep(e.target.value)} placeholder="00000-000" /> : <div {...inp}>{cep || '-'}</div>}
                                {buscandoCep && <span style={{ fontSize: '0.65rem', color: 'var(--brand-500)' }}>Buscando...</span>}
                            </Field>
                            <Field label="Estado (UF)">
                                {editando ? <input className="form-input" value={estado} onChange={e => setEstado(e.target.value)} maxLength={2} placeholder="SP" /> : <div {...inp}>{estado || '-'}</div>}
                            </Field>
                        </div>
                        <Field label="Rua / Avenida">
                            {editando ? <input className="form-input" value={rua} onChange={e => setRua(e.target.value)} placeholder="Rua das Flores" /> : <div {...inp}>{rua || '-'}</div>}
                        </Field>
                        <div className="form-row">
                            <Field label="Numero">
                                {editando ? <input className="form-input" value={numero} onChange={e => setNumero(e.target.value)} /> : <div {...inp}>{numero || '-'}</div>}
                            </Field>
                            <Field label="Complemento">
                                {editando ? <input className="form-input" value={complemento} onChange={e => setComplemento(e.target.value)} placeholder="Apto 12..." /> : <div {...inp}>{complemento || '-'}</div>}
                            </Field>
                        </div>
                        <div className="form-row">
                            <Field label="Bairro">
                                {editando ? <input className="form-input" value={bairro} onChange={e => setBairro(e.target.value)} /> : <div {...inp}>{bairro || '-'}</div>}
                            </Field>
                            <Field label="Cidade">
                                {editando ? <input className="form-input" value={cidade} onChange={e => setCidade(e.target.value)} /> : <div {...inp}>{cidade || '-'}</div>}
                            </Field>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', marginTop: '0.5rem' }}>
                            <input type="checkbox" id="cond" checked={emCond} onChange={e => editando && setEmCond(e.target.checked)} disabled={!editando} style={{ width: 16, height: 16, accentColor: 'var(--brand-500)', cursor: editando ? 'pointer' : 'default' }} />
                            <label htmlFor="cond" style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', cursor: editando ? 'pointer' : 'default' }}>Em condominio</label>
                        </div>
                        {emCond && (
                            <>
                                <Field label="Nome do condominio">
                                    {editando ? <input className="form-input" value={nomeCond} onChange={e => setNomeCond(e.target.value)} /> : <div {...inp}>{nomeCond || '-'}</div>}
                                </Field>
                                <div className="form-row-3">
                                    <Field label="Bloco">
                                        {editando ? <input className="form-input" value={bloco} onChange={e => setBloco(e.target.value)} placeholder="A" /> : <div {...inp}>{bloco || '-'}</div>}
                                    </Field>
                                    <Field label="No apartamento">
                                        {editando ? <input className="form-input" value={numApto} onChange={e => setNumApto(e.target.value)} placeholder="101" /> : <div {...inp}>{numApto || '-'}</div>}
                                    </Field>
                                    <div />
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* ABA: IMOVEL */}
                {aba === 'imovel' && (
                    <div>
                        <div className="form-row-3">
                            <Field label="Preco (R$)">
                                {editando ? <input className="form-input" type="number" step="1000" value={preco} onChange={e => setPreco(e.target.value)} /> : <div {...inp}>{preco ? `R$ ${Number(preco).toLocaleString('pt-BR')}` : '-'}</div>}
                            </Field>
                            <Field label="Condominio (R$)">
                                {editando ? <input className="form-input" type="number" step="10" value={condominio} onChange={e => setCondominio(e.target.value)} /> : <div {...inp}>{condominio ? `R$ ${Number(condominio).toLocaleString('pt-BR')}` : '-'}</div>}
                            </Field>
                            <Field label="IPTU (R$)">
                                {editando ? <input className="form-input" type="number" step="10" value={iptu} onChange={e => setIptu(e.target.value)} /> : <div {...inp}>{iptu ? `R$ ${Number(iptu).toLocaleString('pt-BR')}` : '-'}</div>}
                            </Field>
                        </div>
                        <div className="form-row">
                            <Field label="Area construida (m2)">
                                {editando ? <input className="form-input" type="number" value={areaConstruida} onChange={e => setAreaConstruida(e.target.value)} /> : <div {...inp}>{areaConstruida ? `${areaConstruida} m2` : '-'}</div>}
                            </Field>
                            <Field label="Area do terreno (m2)">
                                {editando ? <input className="form-input" type="number" value={areaTerreno} onChange={e => setAreaTerreno(e.target.value)} /> : <div {...inp}>{areaTerreno ? `${areaTerreno} m2` : '-'}</div>}
                            </Field>
                        </div>
                        <div className="form-row-3">
                            <Field label="Quartos">
                                {editando ? <input className="form-input" type="number" min="0" value={quartos} onChange={e => setQuartos(e.target.value)} /> : <div {...inp}>{quartos || '-'}</div>}
                            </Field>
                            <Field label="Suites">
                                {editando ? <input className="form-input" type="number" min="0" value={suites} onChange={e => setSuites(e.target.value)} /> : <div {...inp}>{suites || '-'}</div>}
                            </Field>
                            <Field label="Banheiros">
                                {editando ? <input className="form-input" type="number" min="0" value={banheiros} onChange={e => setBanheiros(e.target.value)} /> : <div {...inp}>{banheiros || '-'}</div>}
                            </Field>
                        </div>
                        <div className="form-row-3">
                            <Field label="Vagas garage">
                                {editando ? <input className="form-input" type="number" min="0" value={vagas} onChange={e => setVagas(e.target.value)} /> : <div {...inp}>{vagas || '-'}</div>}
                            </Field>
                            <Field label="Salas">
                                {editando ? <input className="form-input" type="number" min="0" value={salas} onChange={e => setSalas(e.target.value)} /> : <div {...inp}>{salas || '-'}</div>}
                            </Field>
                            <Field label="Cozinha">
                                {editando ? (
                                    <select className="form-select" value={cozinha ? 'sim' : 'nao'} onChange={e => setCozinha(e.target.value === 'sim')}>
                                        <option value="sim">Sim</option>
                                        <option value="nao">Nao</option>
                                    </select>
                                ) : <div {...inp}>{cozinha ? 'Sim' : 'Nao'}</div>}
                            </Field>
                        </div>
                        <Field label="Outras caracteristicas">
                            {editando
                                ? <textarea className="form-input" value={outrasCarac} onChange={e => setOutrasCarac(e.target.value)} placeholder="Piscina, churrasqueira, area de servico, etc." rows={3} style={{ resize: 'vertical', fontFamily: 'Inter, sans-serif' }} />
                                : <div {...inp} style={{ ...inp.style, minHeight: 60, whiteSpace: 'pre-wrap' }}>{outrasCarac || '-'}</div>}
                        </Field>
                    </div>
                )}

                {/* ABA: DESCRICAO */}
                {aba === 'descricao' && (
                    <div>
                        {imovel.descricao ? (
                            <>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Descricao do anuncio</span>
                                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', background: 'var(--bg-surface)', padding: '1px 8px', borderRadius: 99, border: '1px solid var(--border)' }}>somente leitura</span>
                                </div>
                                <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem', fontSize: '0.9rem', lineHeight: 1.75, color: 'var(--text-primary)', whiteSpace: 'pre-wrap', maxHeight: 380, overflowY: 'auto' }}>
                                    {imovel.descricao}
                                </div>
                                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.6rem' }}>
                                    A descricao e gerada automaticamente pelo scraper e atualizada a cada coleta.
                                </p>
                            </>
                        ) : (
                            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                                <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem', opacity: 0.3 }}>📄</div>
                                <p style={{ fontSize: '0.88rem' }}>Nenhuma descricao disponivel para este imovel.</p>
                                <p style={{ fontSize: '0.78rem', marginTop: '0.25rem', opacity: 0.7 }}>A descricao e coletada automaticamente pelo scraper quando disponivel no anuncio.</p>
                            </div>
                        )}
                    </div>
                )}

                {/* ABA: FOTOS */}
                {aba === 'fotos' && (
                    <div>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                            {fotos.length} foto{fotos.length !== 1 ? 's' : ''} - A primeira foto e usada como capa
                        </p>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginBottom: '1rem' }}>
                            {fotos.map((url, i) => (
                                <div key={i} style={{ position: 'relative', borderRadius: 'var(--radius-sm)', overflow: 'hidden', aspectRatio: '4/3', background: 'var(--bg-base)' }}>
                                    <img src={typeof url === 'string' ? url : ((url as any).original || (url as any).url || (url as any).webp || '')}
                                        alt={`Foto ${i + 1}`} referrerPolicy="no-referrer" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                        onError={e => { (e.target as HTMLImageElement).style.opacity = '0.2' }} />
                                    {i === 0 && <span style={{ position: 'absolute', top: 4, left: 4, background: 'rgba(0,0,0,0.7)', color: '#fbbf24', fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: 4 }}>CAPA</span>}
                                    {editando && (
                                        <button onClick={() => removeFoto(i)} style={{ position: 'absolute', top: 4, right: 4, background: 'rgba(239,68,68,0.85)', border: 'none', borderRadius: '50%', width: 22, height: 22, cursor: 'pointer', color: '#fff', fontSize: '0.7rem', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>x</button>
                                    )}
                                </div>
                            ))}
                        </div>
                        {editando && (
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <input className="form-input" value={novaFotoUrl} onChange={e => setNovaFotoUrl(e.target.value)} placeholder="URL da foto (https://...)" style={{ flex: 1 }} onKeyDown={e => { if (e.key === 'Enter') addFoto() }} />
                                <button className="btn btn-primary" onClick={addFoto} style={{ width: 'auto', padding: '0.65rem 1rem' }}>+ Adicionar</button>
                            </div>
                        )}
                        {fotos.length === 0 && <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem 0' }}>Nenhuma foto cadastrada</p>}
                    </div>
                )}

                {/* ABA: NOTAS */}
                {aba === 'notas' && (
                    <div>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '0.75rem' }}>Auto-salva enquanto voce digita</p>
                        <textarea value={notas} onChange={e => setNotas(e.target.value)}
                            placeholder="Anotacoes sobre o proprietario, negociacao, visita..." rows={10}
                            style={{ width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontFamily: 'Inter, sans-serif', fontSize: '0.9rem', padding: '0.75rem 1rem', resize: 'vertical', outline: 'none' }} />
                    </div>
                )}

                {/* ABA: HISTORICO */}
                {aba === 'historico' && (
                    <div>
                        {buildTimeline().length === 0 ? (
                            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                                <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem', opacity: 0.3 }}>📅</div>
                                <p style={{ fontSize: '0.88rem' }}>Nenhuma movimentacao registrada ainda.</p>
                            </div>
                        ) : (
                            <div style={{ position: 'relative', paddingLeft: '1.75rem' }}>
                                {/* Linha vertical */}
                                <div style={{ position: 'absolute', left: '0.85rem', top: 14, bottom: 14, width: 2, background: 'var(--border)', borderRadius: 2 }} />

                                {buildTimeline().map((entry, i) => (
                                    <div key={i} style={{ display: 'flex', gap: '1rem', marginBottom: '0.65rem', position: 'relative' }}>
                                        {/* Icone */}
                                        <div style={{ position: 'absolute', left: '-1.75rem', width: 28, height: 28, borderRadius: '50%', background: 'var(--bg-card)', border: `2px solid ${entry.color}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', flexShrink: 0, zIndex: 1 }}>
                                            {getTimelineIcon(entry.type)}
                                        </div>

                                        {/* Conteudo */}
                                        <div style={{ flex: 1, background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', padding: '0.6rem 0.875rem' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                                                <div style={{ fontWeight: 600, fontSize: '0.87rem', color: 'var(--text-primary)' }}>{entry.label}</div>
                                                {entry.date && (
                                                    <span title={new Date(entry.date).toLocaleString('pt-BR')} style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', flexShrink: 0 }}>
                                                        {timeAgo(entry.date)}
                                                    </span>
                                                )}
                                            </div>
                                            {entry.sublabel && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>{entry.sublabel}</div>}
                                            {entry.date && (
                                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.15rem', opacity: 0.7 }}>
                                                    {new Date(entry.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* RODAPE */}
                {aba !== 'notas' && aba !== 'historico' && aba !== 'descricao' && (
                    <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border)', alignItems: 'center' }}>
                        <button className="btn btn-primary" onClick={handleSalvar} disabled={saving} style={{ width: 'auto' }}>
                            {saving ? (
                                <>{<span className="spinner" />}{calculandoGps ? 'Obtendo GPS...' : 'Salvando...'}</>
                            ) : 'Salvar'}
                        </button>
                        <button className="btn btn-danger" onClick={handleCancelar} disabled={saving} style={{ width: 'auto', padding: '0.8rem 1.25rem' }}>Cancelar</button>
                        {profile && <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)' }}>{profile.nome_completo || 'Corretor'}</span>}
                    </div>
                )}
            </div>
        </div>
    )
}
