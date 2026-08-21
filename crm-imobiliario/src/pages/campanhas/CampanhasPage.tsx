import { useState, useEffect, useRef } from 'react'
import * as XLSX from 'xlsx'
import { supabase } from '../../lib/supabase'
import toast from 'react-hot-toast'
import './CampanhasPage.css' 

const ROBO_URL = 'http://localhost:8766'

// --- Components ---

function MarkdownRenderer({ content }: { content: string }) {
    if (!content) return <span style={{ color: '#535F70', fontStyle: 'italic' }}>Sem script definido.</span>
    
    // Parser restaurado com suporte total a mídias e IFrames
    let html = content
        .replace(/^# (.*?)$/gm, '<h1 class="m3-h1-script">$1</h1>')
        .replace(/^## (.*?)$/gm, '<h2 class="m3-h2-script">$2</h2>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Imagens
        .replace(/!\[(.*?)\]\((.*?)\)/g, '<div class="script-media"><img src="$2" alt="$1" style="max-width:100%; border-radius:12px;" /></div>')
        // Vídeos
        .replace(/\[video\]\((.*?)\)/g, '<div class="script-media"><video src="$1" controls style="width:100%; border-radius:12px;"></video></div>')
        // PDF integrado (IFrame)
        .replace(/\[pdf\]\((.*?)\)/g, '<div class="script-media iframe-container" style="border-radius:12px; overflow:hidden; border:1px solid #E1E2EC;"><iframe src="$1#toolbar=0" width="100%" height="500px"></iframe><div style="padding:8px; background:#F8FAFD; text-align:center;"><a href="$1" target="_blank" style="font-size:0.75rem; color:var(--m3-primary);">Ver PDF Fullscreen ↗</a></div></div>')
        .replace(/^\- (.*?)$/gm, '<li class="script-li">$1</li>')
        .replace(/\n/g, '<br />');

    return (
        <div className="m3-markdown-body" dangerouslySetInnerHTML={{ __html: html }} />
    );
}

// --- Types ---
interface Campanha {
    id: string
    nome: string
    tipo: 'Atualização' | 'Captação' | 'Prospecção' | string
    script: string
    criado_em: string
    _count?: { leads: number }
}

interface Lead {
    id: string
    campanha_id: string
    nome: string
    telefone: string
    metadata: any
    status_ligacao: string
    qualificacao: string
    observacoes: string
    data_retorno: string | null
}

export function CampanhasPage() {
    const [campanhas, setCampanhas] = useState<Campanha[]>([])
    const [campanhaSelecionada, setCampanhaSelecionada] = useState<Campanha | null>(null)
    const [leads, setLeads] = useState<Lead[]>([])
    const [leadAtualIdx, setLeadAtualIdx] = useState(0)
    const [loading, setLoading] = useState(true)
    const [modo, setModo] = useState<'lista' | 'nova' | 'execucao'>('lista')
    const [interacoesHoje, setInteracoesHoje] = useState(0)
    
    // Form nova campanha
    const [novoNome, setNovoNome] = useState('')
    const [novoTipo, setNovoTipo] = useState('Prospecção')
    const [novoScript, setNovoScript] = useState('')
    const [arquivo, setArquivo] = useState<File | null>(null)
    const [importando, setImportando] = useState(false)
    const [colunas, setColunas] = useState<string[]>([])
    const [mapNome, setMapNome] = useState('')
    const [mapTelefone, setMapTelefone] = useState('')
    const [mapProprietario, setMapProprietario] = useState('')

    // Aba ativa no modo edição
    const [abaEdicao, setAbaEdicao] = useState<'config' | 'importar'>('config')

    // Feedback lead
    const [showResultPanel, setShowResultPanel] = useState(false)
    const [feedbackStatus, setFeedbackStatus] = useState('')
    const [feedbackObs, setFeedbackObs] = useState('')
    const [feedbackQualif, setFeedbackQualif] = useState('')
    const [feedbackRetorno, setFeedbackRetorno] = useState('')

    // Edição rápida
    const [editLeadNome, setEditLeadNome] = useState('')
    const [editLeadTelefone, setEditLeadTelefone] = useState('')
    const [editLeadCEP, setEditLeadCEP] = useState('')
    const [editLeadEndereco, setEditLeadEndereco] = useState('')
    const [editLeadBairro, setEditLeadBairro] = useState('')
    const [editLeadCidade, setEditLeadCidade] = useState('')

    const fileMediaRef = useRef<HTMLInputElement>(null)
    const [subindoMedia, setSubindoMedia] = useState(false)

    useEffect(() => {
        carregarCampanhas()
        carregarStatsProdutividade()
    }, [])

    async function carregarStatsProdutividade() {
        const hoje = new Date()
        hoje.setHours(0, 0, 0, 0)
        
        const { count } = await supabase
            .from('leads_interacoes')
            .select('*', { count: 'exact', head: true })
            .gte('criado_em', hoje.toISOString())
        
        if (count !== null) setInteracoesHoje(count)
    }

    async function carregarCampanhas() {
        setLoading(true)
        const { data } = await supabase
            .from('campanhas_ligacao')
            .select('*, leads:leads_campanha(count)')
            .order('criado_em', { ascending: false })
        
        if (data) {
            setCampanhas(data.map((c: any) => ({
                ...c,
                _count: { leads: c.leads?.[0]?.count || 0 }
            })))
        }
        setLoading(false)
    }

    async function carregarLeads(campanhaId: string) {
        setLoading(true)
        const { data } = await supabase
            .from('leads_campanha')
            .select('*')
            .eq('campanha_id', campanhaId)
            .order('criado_em', { ascending: true })
        
        if (data && data.length > 0) {
            setLeads(data)
            const pIdx = data.findIndex(l => l.status_ligacao === 'Pendente')
            const idx = pIdx >= 0 ? pIdx : 0
            setLeadAtualIdx(idx)
            carregarDadosLead(data[idx])
        } else {
            setLeads([])
        }
        setLoading(false)
    }

    const carregarDadosLead = (lead: Lead | undefined) => {
        if (!lead) return
        setEditLeadNome(lead.nome || '')
        setEditLeadTelefone(lead.telefone || '')
        setEditLeadCEP(lead.metadata?.cep_residencial || '')
        setEditLeadEndereco(lead.metadata?.endereco_residencial || '')
        setEditLeadBairro(lead.metadata?.bairro_residencial || '')
        setEditLeadCidade(lead.metadata?.cidade_residencial || '')
    }

    useEffect(() => {
        if (leads[leadAtualIdx]) carregarDadosLead(leads[leadAtualIdx])
    }, [leadAtualIdx])

    // --- Actions ---

    async function handleCriarCampanha() {
        if (!novoNome || !arquivo) return toast.error('Nome e planilha são obrigatórios.')
        setImportando(true)
        try {
            const { data: campanha, error } = await supabase
                .from('campanhas_ligacao')
                .insert({ nome: novoNome, tipo: novoTipo, script: novoScript })
                .select().single()

            if (error || !campanha) throw error
            await processarPlanilha(campanha.id)
            toast.success('Campanha e leads processados! 🚀')
            setModo('lista')
            carregarCampanhas()
        } catch (e) { toast.error('Erro ao criar campanha.') }
        finally { setImportando(false) }
    }

    async function handleUpdateCampanha() {
        if (!campanhaSelecionada) return
        const { error } = await supabase
            .from('campanhas_ligacao')
            .update({ nome: novoNome, tipo: novoTipo, script: novoScript })
            .eq('id', campanhaSelecionada.id)
        
        if (!error) {
            if (arquivo) await processarPlanilha(campanhaSelecionada.id)
            toast.success('Campanha atualizada!')
            setModo('lista')
            carregarCampanhas()
        }
    }

    useEffect(() => {
        if (arquivo) extrairColunas()
    }, [arquivo])

    async function extrairColunas() {
        if (!arquivo) return
        const buffer = await arquivo.arrayBuffer()
        const wb = XLSX.read(buffer, { type: 'array' })
        const ws = wb.Sheets[wb.SheetNames[0]]
        const range = XLSX.utils.decode_range(ws['!ref'] || 'A1')
        const headers: string[] = []
        for (let C = range.s.c; C <= range.e.c; ++C) {
            const cell = ws[XLSX.utils.encode_cell({ r: range.s.r, c: C })]
            headers.push(cell ? cell.v : `Coluna ${C + 1}`)
        }
        setColunas(headers)
        
        // Tentativa de auto-mapeamento inteligente
        setMapNome(headers.find(h => h.toLowerCase().includes('condomini') || h.toLowerCase().includes('empresa') || h.toLowerCase().includes('nome')) || headers[0])
        setMapTelefone(headers.find(h => h.toLowerCase().includes('tel') || h.toLowerCase().includes('cel') || h.toLowerCase().includes('fone')) || headers[1])
        setMapProprietario(headers.find(h => h.toLowerCase().includes('proprietario') || h.toLowerCase().includes('sócio') || h.toLowerCase().includes('socio') || h.toLowerCase().includes('contato')) || '')
    }

    async function processarPlanilha(campanhaId: string) {
        if (!arquivo || !mapNome || !mapTelefone) return toast.error('Selecione as colunas de Nome e Telefone.')
        const buffer = await arquivo.arrayBuffer()
        const wb = XLSX.read(buffer, { type: 'array' })
        const rows: any[] = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], { defval: '' })

        const payloads = rows.map(row => {
            // Se o campo proprietário foi mapeado e existe na linha, vamos garantir que ele esteja no metadado
            const vProp = mapProprietario ? row[mapProprietario] : ''
            
            return {
                campanha_id: campanhaId,
                nome: String(row[mapNome] || ''),
                telefone: String(row[mapTelefone] || '').replace(/\D/g, ''),
                metadata: {
                    ...row,
                    // Garante que o campo de mapeamento esteja normalizado para 'proprietario' no JSON
                    proprietario_mapeado: vProp 
                },
            }
        }).filter(p => p.telefone.length >= 8)

        const LOTE = 100
        for (let i = 0; i < payloads.length; i += LOTE) {
            await supabase.from('leads_campanha').insert(payloads.slice(i, i + LOTE))
        }
    }

    async function handleDeletarCampanha(id: string) {
        if (!window.confirm('Excluir esta campanha e todos os seus leads?')) return
        const { error } = await supabase.from('campanhas_ligacao').delete().eq('id', id)
        if (!error) {
            toast.success('Campanha removida.')
            setModo('lista')
            setCampanhaSelecionada(null)
            carregarCampanhas()
        } else toast.error('Erro ao deletar.')
    }

    const handleUploadMedia = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return
        setSubindoMedia(true)
        const tid = toast.loading('Subindo mídia...')
        try {
            const ext = file.name.split('.').pop()
            const name = `${Math.random().toString(36).substring(2)}-${Date.now()}.${ext}`
            const path = `scripts/${name}`
            const { error: upErr } = await supabase.storage.from('crm-media').upload(path, file)
            if (upErr) throw upErr
            const { data: { publicUrl } } = supabase.storage.from('crm-media').getPublicUrl(path)
            let tag = ''
            if (file.type === 'application/pdf') tag = `\n[pdf](${publicUrl})\n`
            else if (file.type.startsWith('video')) tag = `\n[video](${publicUrl})\n`
            else tag = `\n![imagem](${publicUrl})\n`
            setNovoScript(prev => prev + tag)
            toast.success('Mídia anexada!', { id: tid })
        } catch { toast.error('Upload falhou.', { id: tid }) }
        finally { setSubindoMedia(false) }
    }

    async function registrarInteracao(tipo: string) {
        if (!leads[leadAtualIdx] || !campanhaSelecionada) return
        
        await supabase.from('leads_interacoes').insert({
            lead_id: leads[leadAtualIdx].id,
            campanha_id: campanhaSelecionada.id,
            tipo: tipo
        })
        
        setInteracoesHoje(prev => prev + 1)
    }

    // --- Communication Methods ---

    const discar = async (tel: string) => {
        try {
            await registrarInteracao('Chamada Android')
            const res = await fetch(`${ROBO_URL}/adb/dial`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telefone: tel })
            })
            const data = await res.json()
            if (data.ok) {
                toast.success('Discador aberto!')
                setTimeout(() => setShowResultPanel(true), 1500)
            } else toast.error(data.mensagem)
        } catch { toast.error('Servidor offline.') }
    }

    const abrirWhatsApp = async (tel: string, nome: string) => {
        try {
            await registrarInteracao('WhatsApp Msg')
            const clean = tel.replace(/\D/g, '')
            const numero = clean.startsWith('55') ? clean : '55' + clean

            // O backend fará o processamento do template, buscando o link se for campanha de atualização
            const res = await fetch(`${ROBO_URL}/adb/whatsapp-msg`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    telefone: numero, 
                    mensagem: '', 
                    nome: nome,
                    tipo_campanha: campanhaSelecionada?.tipo || '',
                    metadata: leads[leadAtualIdx]?.metadata || {}
                })
            })
            const data = await res.json()
            if (data.ok) {
                toast.success('WhatsApp aberto no celular! 📱')
                setTimeout(() => setShowResultPanel(true), 2000)
            } else {
                toast.error(data.mensagem)
            }
        } catch { toast.error('Robô Android offline.') }
    }

    const ligarWhatsApp = async (tel: string) => {
        try {
            await registrarInteracao('WhatsApp Call')
            const res = await fetch(`${ROBO_URL}/adb/whatsapp-call`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telefone: tel })
            })
            const data = await res.json()
            if (data.ok) {
                toast.success('Chamada WhatsApp iniciada!')
                setTimeout(() => setShowResultPanel(true), 2000)
            } else toast.error(data.mensagem)
        } catch { toast.error('Robô Android offline.') }
    }

    const enviarSMS = async (tel: string) => {
        const msg = `Olá, aqui é o Samuel. Gostaria de conversar sobre seu interesse. Pode falar?`
        try {
            await registrarInteracao('SMS')
            const res = await fetch(`${ROBO_URL}/adb/sms/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telefone: tel, mensagem: msg })
            })
            const data = await res.json()
            if (data.ok) {
                toast.success('SMS enviado via Android!')
                setTimeout(() => setShowResultPanel(true), 2000)
            } else toast.error(data.mensagem)
        } catch { toast.error('Android desconectado.') }
    }

    const salvarFeedback = async () => {
        const lead = leads[leadAtualIdx]
        if (!lead) return
        const tid = toast.loading('Registrando contato...')
        
        const novaInteracao = {
            data: new Date().toISOString(),
            status: feedbackStatus,
            qualificacao: feedbackQualif,
            observacoes: feedbackObs
        }
        const historico = Array.isArray(lead.metadata?.historico) ? [...lead.metadata.historico, novaInteracao] : [novaInteracao]

        const { error } = await supabase
            .from('leads_campanha')
            .update({
                nome: editLeadNome,
                telefone: editLeadTelefone,
                status_ligacao: ['Não atendeu', 'Ocupado'].includes(feedbackStatus) ? 'Pendente' : 'Concluído',
                qualificacao: feedbackQualif,
                observacoes: feedbackObs,
                data_retorno: feedbackRetorno || null,
                metadata: {
                    ...lead.metadata,
                    historico,
                    cep_residencial: editLeadCEP,
                    endereco_residencial: editLeadEndereco,
                    bairro_residencial: editLeadBairro,
                    cidade_residencial: editLeadCidade
                }
            })
            .eq('id', lead.id)

        if (!error) {
            toast.success('Qualificação salva! ✅', { id: tid })
            const updated = [...leads]; updated[leadAtualIdx] = { ...lead, metadata: { ...lead.metadata, historico } }
            setLeads(updated)
            setShowResultPanel(false)
            setFeedbackQualif(''); setFeedbackObs(''); setFeedbackStatus(''); setFeedbackRetorno('')
            if (leadAtualIdx < leads.length -1) setLeadAtualIdx(prev => prev + 1)
        } else toast.error('Erro ao salvar.', { id: tid })
    }

    if (loading && modo === 'lista') return (
        <div className="campaigns-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🚀</div>
                <div style={{ fontWeight: 800, color: '#535F70' }}>Sincronizando Motor de Campanhas...</div>
            </div>
        </div>
    )

    return (
        <div className="campaigns-container">
            <div className="campaigns-wrapper">
                
                {/* Header Section */}
                <header className="campaigns-header">
                    <div>
                        <h1>Motor de Campanhas</h1>
                        <p>{modo === 'execucao' ? `Ativo: ${campanhaSelecionada?.nome}` : 'Discador Automático & Interface de Alta Performance'}</p>
                    </div>
                    {modo === 'lista' ? (
                        <button onClick={() => setModo('nova')} className="m3-btn-primary" style={{ padding: '12px 24px', borderRadius: '12px', border: 'none', fontWeight: 800, cursor: 'pointer', background: 'var(--m3-primary)', color:'white' }}>
                            ➕ Nova Campanha
                        </button>
                    ) : (
                        <button onClick={() => { setModo('lista'); setCampanhaSelecionada(null); }} className="m3-btn-outline" style={{ padding: '12px 24px', borderRadius: '12px', border: '1px solid #C4C7C5', fontWeight: 800, cursor: 'pointer', background: 'white' }}>
                            ⬅️ Voltar
                        </button>
                    )
                    }
                </header>

                {modo === 'lista' && (
                    <>
                        <div className="stats-grid">
                            <StatCard label="Leads Totais" value={campanhas.reduce((acc, c) => acc + (c._count?.leads || 0), 0)} />
                            <StatCard label="Interações Hoje" value={interacoesHoje} highlight />
                            <StatCard label="Campanhas Ativas" value={campanhas.length} />
                        </div>

                        <div className="campaign-grid">
                            {campanhas.map(c => (
                                <article key={c.id} className="campaign-card-m3">
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                        <div>
                                            <h3 style={{ margin: 0, fontWeight: 900 }}>{c.nome}</h3>
                                            <span className="badge-m3" style={{ background: 'rgba(0, 86, 210, 0.1)', color: 'var(--m3-primary)', marginTop: '8px', display: 'inline-block' }}>{c.tipo || 'Prospecção'}</span>
                                        </div>
                                        <div style={{ display:'flex', gap:'8px' }}>
                                            <button className="m3-btn-icon" onClick={() => { setCampanhaSelecionada(c); setNovoNome(c.nome); setNovoTipo(c.tipo || 'Prospecção'); setNovoScript(c.script); setAbaEdicao('config'); setModo('nova'); }}>✏️</button>
                                            <button className="m3-btn-icon" onClick={() => handleDeletarCampanha(c.id)}>🗑️</button>
                                        </div>
                                    </div>
                                    <p style={{ margin: 0, fontSize: '0.85rem', color: '#535F70', flex: 1 }}>{c.script?.substring(0, 90)}...</p>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #F0F0F0', paddingTop: '1rem' }}>
                                        <div style={{ fontWeight: 800, color: '#006D3A' }}>{c._count?.leads} leads</div>
                                        <button onClick={() => { setCampanhaSelecionada(c); carregarLeads(c.id); setModo('execucao'); }} style={{ background: 'var(--m3-primary)', color: 'white', border: 'none', padding: '8px 20px', borderRadius: '8px', fontWeight: 700, cursor: 'pointer' }}>🚀 Abrir</button>
                                    </div>
                                </article>
                            ))}
                            <div onClick={() => setModo('nova')} style={{ border: '2px dashed var(--m3-outline)', borderRadius: 'var(--m3-radius-xl)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '240px', cursor: 'pointer', opacity: 0.6 }}>
                                <span style={{ fontSize: '2.5rem' }}>➕</span>
                                <span style={{ fontWeight: 800, marginTop: '8px' }}>Nova Campanha</span>
                            </div>
                        </div>
                    </>
                )}

                {modo === 'nova' && (
                    <div style={{ background: 'white', padding: '3rem', borderRadius: 'var(--m3-radius-xl)', boxShadow: 'var(--m3-shadow)', maxWidth: '1000px', margin: '0 auto' }}>

                        {/* Título */}
                        <h2 style={{ fontWeight: 900, marginBottom: '2rem' }}>
                            {campanhaSelecionada ? '🏷️ Editar Campanha' : '🚀 Lançar Nova Campanha'}
                        </h2>

                        {/* ── Abas: só exibe quando editando campanha existente ── */}
                        {campanhaSelecionada && (
                            <div style={{ display: 'flex', gap: '4px', marginBottom: '2rem', background: '#F3F4F6', borderRadius: '12px', padding: '4px' }}>
                                <button
                                    onClick={() => setAbaEdicao('config')}
                                    style={{
                                        flex: 1, padding: '10px 20px', borderRadius: '9px', border: 'none',
                                        fontWeight: 700, cursor: 'pointer', fontSize: '0.875rem',
                                        transition: 'all 0.2s',
                                        background: abaEdicao === 'config' ? 'white' : 'transparent',
                                        color: abaEdicao === 'config' ? 'var(--m3-primary)' : '#535F70',
                                        boxShadow: abaEdicao === 'config' ? '0 1px 4px rgba(0,0,0,0.12)' : 'none',
                                    }}
                                >
                                    ⚙️ Configurações
                                </button>
                                <button
                                    onClick={() => { setAbaEdicao('importar'); setArquivo(null); setColunas([]); }}
                                    style={{
                                        flex: 1, padding: '10px 20px', borderRadius: '9px', border: 'none',
                                        fontWeight: 700, cursor: 'pointer', fontSize: '0.875rem',
                                        transition: 'all 0.2s',
                                        background: abaEdicao === 'importar' ? 'white' : 'transparent',
                                        color: abaEdicao === 'importar' ? 'var(--m3-primary)' : '#535F70',
                                        boxShadow: abaEdicao === 'importar' ? '0 1px 4px rgba(0,0,0,0.12)' : 'none',
                                    }}
                                >
                                    📥 Importar Nova Planilha
                                </button>
                            </div>
                        )}

                        {/* ── ABA CONFIGURAÇÕES (ou formulário de criação) ── */}
                        {(!campanhaSelecionada || abaEdicao === 'config') && (
                            <>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
                                    <div>
                                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 800, color: '#535F70', textTransform: 'uppercase', marginBottom: '8px' }}>Nome da Campanha</label>
                                        <input className="m3-input" value={novoNome} onChange={e => setNovoNome(e.target.value)} placeholder="Ex: Leads Altíssimo Padrão" />
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 800, color: '#535F70', textTransform: 'uppercase', marginBottom: '8px' }}>Tipo</label>
                                        <select className="m3-input" value={novoTipo} onChange={e => setNovoTipo(e.target.value)}>
                                            <option value="Prospecção">💎 Prospecção Ativa</option>
                                            <option value="Captação">🎯 Captação Direta</option>
                                            <option value="Atualização">🔄 Atualização de Base</option>
                                        </select>
                                    </div>
                                </div>

                                <div style={{ marginBottom: '2rem' }}>
                                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 800, color: '#535F70', textTransform: 'uppercase', marginBottom: '8px' }}>Script Sugerido (Markdown)</label>
                                        <button
                                            onClick={() => fileMediaRef.current?.click()}
                                            className="m3-btn-outline"
                                            style={{ fontSize:'0.7rem', padding:'4px 12px', marginBottom:'8px' }}
                                        >
                                            📎 Anexar Mídia
                                        </button>
                                        <input type="file" ref={fileMediaRef} style={{ display:'none' }} onChange={handleUploadMedia} />
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', height: '400px' }}>
                                        <textarea className="m3-input" style={{ resize: 'none', fontFamily: 'monospace' }} value={novoScript} onChange={e => setNovoScript(e.target.value)} placeholder="Use **negrito**, # títulos..." />
                                        <div style={{ background: '#F8FAFD', border: '1px solid var(--m3-outline-variant)', borderRadius: '12px', padding: '1.5rem', overflowY: 'auto' }}>
                                            <MarkdownRenderer content={novoScript} />
                                        </div>
                                    </div>
                                </div>

                                {/* Upload de planilha só na criação */}
                                {!campanhaSelecionada && (
                                    <div style={{ padding: '2rem', background: '#F8FAFD', borderRadius: '16px', border: '1px dashed var(--m3-outline)', textAlign: 'center', marginBottom: '2rem' }}>
                                        <label style={{ fontWeight: 700, display: 'block', marginBottom: '12px' }}>Carregar Leads (.xlsx)</label>
                                        <input type="file" accept=".xlsx" onChange={e => setArquivo(e.target.files?.[0] || null)} />
                                        {colunas.length > 0 && (
                                            <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'white', borderRadius: '12px', border: '1px solid var(--m3-outline-variant)', textAlign: 'left' }}>
                                                <h4 style={{ margin: '0 0 1rem 0' }}>🗺️ Mapeamento de Colunas</h4>
                                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                                                    <div>
                                                        <label style={{ fontSize: '0.7rem', fontWeight: 800, color: '#535F70' }}>Nome (Condomínio)</label>
                                                        <select className="m3-input" value={mapNome} onChange={e => setMapNome(e.target.value)}>
                                                            <option value="">Selecione...</option>
                                                            {colunas.map(c => <option key={c} value={c}>{c}</option>)}
                                                        </select>
                                                    </div>
                                                    <div>
                                                        <label style={{ fontSize: '0.7rem', fontWeight: 800, color: '#535F70' }}>Telefone</label>
                                                        <select className="m3-input" value={mapTelefone} onChange={e => setMapTelefone(e.target.value)}>
                                                            <option value="">Selecione...</option>
                                                            {colunas.map(c => <option key={c} value={c}>{c}</option>)}
                                                        </select>
                                                    </div>
                                                    <div>
                                                        <label style={{ fontSize: '0.7rem', fontWeight: 800, color: '#535F70' }}>Proprietário (Contato)</label>
                                                        <select className="m3-input" value={mapProprietario} onChange={e => setMapProprietario(e.target.value)}>
                                                            <option value="">Nenhum</option>
                                                            {colunas.map(c => <option key={c} value={c}>{c}</option>)}
                                                        </select>
                                                    </div>
                                                </div>
                                                <p style={{ fontSize: '0.7rem', color: '#535F70', marginTop: '1rem' }}>* O sistema tentou identificar as colunas automaticamente. Ajuste se necessário.</p>
                                            </div>
                                        )}
                                    </div>
                                )}

                                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                                    {campanhaSelecionada && (
                                        <button onClick={() => handleDeletarCampanha(campanhaSelecionada.id)} className="m3-btn-outline" style={{ flex: 1, color:'#BA1A1A', borderColor:'#BA1A1A' }}>🗑️ Excluir permanentemente</button>
                                    )}
                                    <button onClick={() => setModo('lista')} className="m3-btn-outline" style={{ flex: 1 }}>Voltar</button>
                                    <button onClick={campanhaSelecionada ? handleUpdateCampanha : handleCriarCampanha} disabled={importando} className="m3-btn-primary" style={{ flex: 2, background: 'var(--m3-primary)', color:'white', border:'none', borderRadius:'12px', fontWeight:800 }}>
                                        {importando ? 'Sincronizando...' : (campanhaSelecionada ? '💾 Salvar Alterações' : '🚀 Iniciar Motor')}
                                    </button>
                                </div>
                            </>
                        )}

                        {/* ── ABA IMPORTAR PLANILHA (só em edição) ── */}
                        {campanhaSelecionada && abaEdicao === 'importar' && (
                            <>
                                {/* Banner informativo */}
                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '1rem 1.25rem', background: 'rgba(0,86,210,0.06)', borderRadius: '12px', border: '1px solid rgba(0,86,210,0.15)', marginBottom: '2rem' }}>
                                    <span style={{ fontSize: '1.25rem', flexShrink: 0 }}>ℹ️</span>
                                    <div>
                                        <div style={{ fontWeight: 800, fontSize: '0.875rem', color: 'var(--m3-primary)', marginBottom: '2px' }}>Adicionando leads à campanha existente</div>
                                        <div style={{ fontSize: '0.8rem', color: '#535F70' }}>Os novos leads serão <strong>adicionados ao final da lista</strong> da campanha <strong>"{campanhaSelecionada.nome}"</strong>, sem remover os anteriores.</div>
                                    </div>
                                </div>

                                <div style={{ padding: '2rem', background: '#F8FAFD', borderRadius: '16px', border: '1px dashed var(--m3-outline)', textAlign: 'center', marginBottom: '2rem' }}>
                                    <label style={{ fontWeight: 700, display: 'block', marginBottom: '12px' }}>Selecione a nova planilha (.xlsx)</label>
                                    <input type="file" accept=".xlsx" onChange={e => setArquivo(e.target.files?.[0] || null)} />
                                    {colunas.length > 0 && (
                                        <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'white', borderRadius: '12px', border: '1px solid var(--m3-outline-variant)', textAlign: 'left' }}>
                                            <h4 style={{ margin: '0 0 1rem 0' }}>🗺️ Mapeamento de Colunas</h4>
                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                                                <div>
                                                    <label style={{ fontSize: '0.7rem', fontWeight: 800, color: '#535F70' }}>Nome (Condomínio)</label>
                                                    <select className="m3-input" value={mapNome} onChange={e => setMapNome(e.target.value)}>
                                                        <option value="">Selecione...</option>
                                                        {colunas.map(c => <option key={c} value={c}>{c}</option>)}
                                                    </select>
                                                </div>
                                                <div>
                                                    <label style={{ fontSize: '0.7rem', fontWeight: 800, color: '#535F70' }}>Telefone</label>
                                                    <select className="m3-input" value={mapTelefone} onChange={e => setMapTelefone(e.target.value)}>
                                                        <option value="">Selecione...</option>
                                                        {colunas.map(c => <option key={c} value={c}>{c}</option>)}
                                                    </select>
                                                </div>
                                                <div>
                                                    <label style={{ fontSize: '0.7rem', fontWeight: 800, color: '#535F70' }}>Proprietário (Contato)</label>
                                                    <select className="m3-input" value={mapProprietario} onChange={e => setMapProprietario(e.target.value)}>
                                                        <option value="">Nenhum</option>
                                                        {colunas.map(c => <option key={c} value={c}>{c}</option>)}
                                                    </select>
                                                </div>
                                            </div>
                                            <p style={{ fontSize: '0.7rem', color: '#535F70', marginTop: '1rem' }}>* O sistema tentou identificar as colunas automaticamente. Ajuste se necessário.</p>
                                        </div>
                                    )}
                                </div>

                                <div style={{ display: 'flex', gap: '1rem' }}>
                                    <button onClick={() => setModo('lista')} className="m3-btn-outline" style={{ flex: 1 }}>Voltar</button>
                                    <button
                                        onClick={async () => {
                                            if (!arquivo) return toast.error('Selecione uma planilha primeiro.')
                                            setImportando(true)
                                            try {
                                                await processarPlanilha(campanhaSelecionada.id)
                                                toast.success('✅ Leads adicionados com sucesso!')
                                                setArquivo(null)
                                                setColunas([])
                                                setAbaEdicao('config')
                                                carregarCampanhas()
                                            } catch { toast.error('Erro ao importar planilha.') }
                                            finally { setImportando(false) }
                                        }}
                                        disabled={importando || !arquivo}
                                        className="m3-btn-primary"
                                        style={{ flex: 2, background: 'var(--m3-primary)', color:'white', border:'none', borderRadius:'12px', fontWeight:800, opacity: (!arquivo || importando) ? 0.6 : 1 }}
                                    >
                                        {importando ? '⏳ Importando...' : '📥 Adicionar Leads à Campanha'}
                                    </button>
                                </div>
                            </>
                        )}

                    </div>
                )}

                {modo === 'execucao' && leads[leadAtualIdx] && (
                    <div className="dialer-layout-3col">
                        
                        {/* COLUNA 1: DADOS E CONTEXTO (ESQUERDA) */}
                        <aside className="left-context-panel">
                            <h4 style={{ margin: '0 0 1.5rem 0', fontWeight: 900 }}>Contexto & Detalhes</h4>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                <div>
                                    <label className="stat-label">📍 Endereço Residencial</label>
                                    <div style={{ marginTop: '4px', fontSize: '0.85rem' }}>
                                        {editLeadEndereco ? `${editLeadEndereco}, ${editLeadBairro}` : 'Não informado'}
                                    </div>
                                </div>
                                
                                <div style={{ borderTop: '1px solid var(--m3-outline-variant)', paddingTop: '1.5rem' }}>
                                    <label className="stat-label">📅 Histórico Timeline</label>
                                    <div style={{ marginTop: '1rem' }}>
                                        {leads[leadAtualIdx]?.metadata?.historico?.slice().reverse().map((h: any, i: number) => (
                                            <div key={i} className="timeline-item">
                                                <div className="timeline-status" style={{ color: h.status === 'Atendeu' ? '#006D3A' : '#BA1A1A' }}>{h.status}</div>
                                                <div style={{ fontSize: '0.7rem', opacity: 0.6 }}>{new Date(h.data).toLocaleDateString()}</div>
                                                {h.observacoes && <div style={{ marginTop: '4px', fontSize:'0.75rem' }}>"{h.observacoes}"</div>}
                                            </div>
                                        )) || <div style={{ opacity: 0.5, fontSize: '0.8rem' }}>Sem interações.</div>}
                                    </div>
                                </div>

                                <div style={{ borderTop: '1px solid var(--m3-outline-variant)', paddingTop: '1.5rem' }}>
                                    <label className="stat-label">🔍 Dados Adicionais</label>
                                    <div style={{ marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                        {Object.entries(leads[leadAtualIdx]?.metadata || {})
                                            .filter(([k]) => !['historico', 'proprietario_mapeado'].includes(k))
                                            .map(([k, v]) => (
                                            <div key={k} style={{ fontSize: '0.7rem' }}>
                                                <span style={{ fontWeight: 700, color:'#535F70' }}>{k}:</span> {String(v)}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </aside>

                        {/* COLUNA 2: SCRIPT E IDENTIDADE (CENTRO) */}
                        <main className="center-script-panel">
                             <div style={{ marginBottom: '2.5rem' }}>
                                <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#535F70', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '4px' }}>
                                    Lead {leadAtualIdx + 1} de {leads.length} • {campanhaSelecionada?.tipo}
                                </div>
                                {leads[leadAtualIdx]?.metadata?.proprietario_mapeado && (
                                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--m3-primary)', textTransform: 'uppercase', marginBottom: '2px' }}>
                                        🏢 {leads[leadAtualIdx]?.nome}
                                    </div>
                                )}
                                <h2 style={{ fontSize: '2.5rem', fontWeight: 900, margin: 0, color: '#1A1C1E', lineHeight: 1.1 }}>
                                    {leads[leadAtualIdx]?.metadata?.proprietario_mapeado || leads[leadAtualIdx]?.nome || 'Misterioso'}
                                </h2>
                                <div style={{ fontSize: '1.5rem', color: 'var(--m3-secondary)', fontWeight: 600, marginTop: '8px' }}>{editLeadTelefone}</div>
                            </div>

                            <div style={{ background: '#F8FAFD', padding: '2rem', borderRadius: '16px', borderLeft: '5px solid var(--m3-primary)', marginBottom: '2rem' }}>
                                <div style={{ fontSize: '0.75rem', fontWeight: 900, color: 'var(--m3-primary)', textTransform: 'uppercase', marginBottom: '1rem' }}>Script de Vendas</div>
                                <MarkdownRenderer content={campanhaSelecionada?.script || ''} />
                            </div>

                            <div style={{ display: 'flex', gap: '1rem', borderTop: '1px solid #F0F0F0', paddingTop: '2rem' }}>
                                <button onClick={() => setLeadAtualIdx(prev => Math.max(0, prev - 1))} className="action-btn-m3 btn-communication-m3 btn-skip-m3" style={{ flex: 1 }} disabled={leadAtualIdx === 0}>⬅️ Voltar</button>
                                <button onClick={() => setLeadAtualIdx(prev => Math.min(leads.length-1, prev+1))} className="action-btn-m3 btn-communication-m3 btn-skip-m3" style={{ flex: 1 }} disabled={leadAtualIdx === leads.length - 1}>Pular ➡️</button>
                            </div>
                        </main>

                        {/* COLUNA 3: AÇÕES E FEEDBACK (DIREITA) */}
                        <aside className="right-action-panel">
                            <div className="action-card-m3">
                                <h4 style={{ margin: '0 0 1rem 0', fontSize: '0.85rem', textTransform: 'uppercase', color: '#535F70' }}>Iniciar Contato</h4>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                    <button onClick={() => discar(editLeadTelefone)} className="action-btn-m3 btn-dial-main" style={{ height: '56px', fontSize: '1rem' }}>📞 Ligar (Normal)</button>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                                        <button onClick={() => abrirWhatsApp(editLeadTelefone, editLeadNome)} className="action-btn-m3 btn-communication-m3 btn-wa-msg" style={{ height: '48px' }}>💬 WA Msg</button>
                                        <button onClick={() => ligarWhatsApp(editLeadTelefone)} className="action-btn-m3 btn-communication-m3 btn-wa-call" style={{ height: '48px' }}>📞 WA Call</button>
                                    </div>
                                    <button onClick={() => enviarSMS(editLeadTelefone)} className="action-btn-m3 btn-communication-m3 btn-sms-m3" style={{ height: '48px' }}>📨 Enviar SMS</button>
                                </div>
                            </div>

                            {showResultPanel && (
                                <div className="action-card-m3 feedback-panel-m3" style={{ background: '#F8FAFD' }}>
                                    <h3 style={{ margin: '0 0 1.5rem 0', fontSize: '1.1rem', fontWeight: 900 }}>Qualificar Contato</h3>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                                        <div>
                                            <label className="stat-label">Resultado</label>
                                            <select className="m3-input" value={feedbackStatus} onChange={e => setFeedbackStatus(e.target.value)}>
                                                <option value="">Selecione...</option>
                                                <option value="Atendeu">✅ Atendeu</option>
                                                <option value="Não atendeu">❌ Não atendeu</option>
                                                <option value="Ocupado">⏳ Ocupado</option>
                                                <option value="Caixa Postal">📵 Caixa Postal</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="stat-label">Qualificação</label>
                                            <select className="m3-input" value={feedbackQualif} onChange={e => setFeedbackQualif(e.target.value)}>
                                                <option value="">Selecione...</option>
                                                <option value="Interessado">💎 Interessado</option>
                                                <option value="Talvez">🧐 Pensativo</option>
                                                <option value="Sem Interesse">👎 Sem Interesse</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="stat-label">Agendar Retorno</label>
                                            <input type="date" className="m3-input" value={feedbackRetorno} onChange={e => setFeedbackRetorno(e.target.value)} />
                                        </div>
                                        <div>
                                            <label className="stat-label">Anotações</label>
                                            <textarea className="m3-input" placeholder="Resumo da conversa..." rows={3} value={feedbackObs} onChange={e => setFeedbackObs(e.target.value)} />
                                        </div>
                                        <div style={{ display: 'flex', gap: '0.75rem' }}>
                                            <button onClick={() => setShowResultPanel(false)} className="m3-btn-outline" style={{ flex: 1, padding: '10px', fontSize: '0.8rem' }}>Cancelar</button>
                                            <button onClick={salvarFeedback} className="m3-btn-primary" style={{ flex: 2, padding: '10px', background: 'var(--m3-primary)', color: 'white', fontWeight: 800, border: 'none', borderRadius: '12px' }}>✅ Salvar</button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </aside>

                    </div>
                )}

            </div>
        </div>
    )
}

function StatCard({ label, value, highlight }: { label: string, value: number, highlight?: boolean }) {
    return (
        <div className={`stat-card-m3 ${highlight ? 'stat-highlight-m3' : ''}`}>
            <span className="stat-label">{label}</span>
            <span className="stat-value" style={{ color: highlight ? 'var(--m3-primary)' : 'inherit' }}>{value}</span>
        </div>
    )
}
