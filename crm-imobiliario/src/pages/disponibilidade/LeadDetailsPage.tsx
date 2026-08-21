import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { supabase } from '../../lib/supabase'
import toast from 'react-hot-toast'
import './LeadDetailsPage.css' // Importando o novo CSS

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
    cnae_descricao: string
    cnaes_secundarios: string
    notas_investigacao: string
    atualizado_em: string
}

export function LeadDetailsPage() {
    const { id } = useParams()
    const [empresa, setEmpresa] = useState<EmpresaCNPJ | null>(null)
    const [loading, setLoading] = useState(true)
    const [investigationNotes, setInvestigationNotes] = useState('')
    const [enriquecendoIndividual, setEnriquecendoIndividual] = useState(false)
    const [serverOnline, setServerOnline] = useState(false)
    const [showEditModal, setShowEditModal] = useState(false)
    const [editForm, setEditForm] = useState<Partial<EmpresaCNPJ>>({})

    useEffect(() => {
        if (id) {
            carregarDadosLead(id)
        }
        checkServerHealth()
        const iv = setInterval(checkServerHealth, 5000)
        return () => clearInterval(iv)
    }, [id])

    async function checkServerHealth() {
        try {
            const res = await fetch(`${ROBO_URL}/status`)
            setServerOnline(res.ok)
        } catch (e) {
            setServerOnline(false)
        }
    }

    async function carregarDadosLead(leadId: string) {
        setLoading(true)
        const { data, error } = await supabase
            .from('empresas_sjc')
            .select('*')
            .eq('id', leadId)
            .single()

        if (error) {
            toast.error('Erro ao carregar dados do lead.')
        } else {
            setEmpresa(data)
            setInvestigationNotes(data.notas_investigacao || '')
        }
        setLoading(false)
    }

    async function handleEnriquecerIndividual(cnpj: string) {
        if (!serverOnline) {
            toast.error('O Robô (8766) está offline.')
            return
        }
        setEnriquecendoIndividual(true)
        const tid = toast.loading('Acionando robô de inteligência...')
        try {
            const res = await fetch(`${ROBO_URL}/extrator/enriquecer-individual`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cnpj })
            })
            const data = await res.json()
            if (data.ok) {
                toast.success('Lead atualizado com sucesso!', { id: tid })
                if (id) carregarDadosLead(id)
            } else {
                toast.error(data.mensagem || 'Falha no enriquecimento.', { id: tid })
            }
        } catch (e) {
            toast.error('Erro de conexão com o robô.', { id: tid })
        } finally {
            setEnriquecendoIndividual(false)
        }
    }

    async function handleEnriquecerReceitaWS(cnpj: string) {
        if (!serverOnline) return toast.error('O Robô (8766) está offline.')
        setEnriquecendoIndividual(true)
        const tid = toast.loading('Consultando ReceitaWS (Premium)...')
        try {
            const res = await fetch(`${ROBO_URL}/extrator/enriquecer-receitaws`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cnpj })
            })
            const data = await res.json()
            if (data.ok) {
                toast.success('Dados enriquecidos com sucesso!', { id: tid })
                if (id) carregarDadosLead(id)
            } else {
                toast.error(data.mensagem || 'Falha no ReceitaWS.', { id: tid })
            }
        } catch (e) { toast.error('Erro de conexão.', { id: tid }) }
        finally { setEnriquecendoIndividual(false) }
    }
    
    function openEditModal() {
        if (!empresa) return
        setEditForm({
            whatsapp: empresa.whatsapp,
            email: empresa.email,
            email_site: empresa.email_site,
            tel_maps: empresa.tel_maps,
            telefone_completo_1: empresa.telefone_completo_1,
            tel_opencnpj: empresa.tel_opencnpj,
            site: empresa.site,
            site_google: empresa.site_google,
            notas_investigacao: empresa.notas_investigacao,
            razao_social: empresa.razao_social,
            nome_fantasia: empresa.nome_fantasia
        })
        setShowEditModal(true)
    }

    async function handleSaveDatabase() {
        if (!id || !empresa) return
        const tid = toast.loading('Salvando no banco de dados...')
        try {
            const { error } = await supabase
                .from('empresas_sjc')
                .update(editForm)
                .eq('id', id)

            if (error) throw error

            toast.success('Dados atualizados com sucesso!', { id: tid })
            setShowEditModal(false)
            carregarDadosLead(id)
        } catch (e) {
            toast.error('Erro ao salvar no banco de dados.', { id: tid })
        }
    }

    async function handleAdbCall(telefone: string) {
        if (!serverOnline) return toast.error('Servidor offline ⚠️')
        const num = String(telefone || '').replace(/\D/g, '')
        if (!num) return toast.error('Telefone inválido ❌')
        const tid = toast.loading('Acionando ADB...')
        try {
            const res = await fetch(`${ROBO_URL}/adb/dial`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telefone: num })
            })
            const data = await res.json()
            if (data.ok) toast.success('Chamada iniciada! 📱', { id: tid })
            else toast.error(data.mensagem, { id: tid })
        } catch (e) { toast.error('Erro de conexão.', { id: tid }) }
    }

    async function handleAdbWhatsapp(telefone: string) {
        if (!serverOnline) return toast.error('Servidor offline ⚠️')
        const num = String(telefone || '').replace(/\D/g, '')
        if (!num) return toast.error('WhatsApp inválido ❌')
        const tid = toast.loading('Abrindo WhatsApp...')
        try {
            const res = await fetch(`${ROBO_URL}/adb/whatsapp-call`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telefone: num })
            })
            const data = await res.json()
            if (data.ok) toast.success('WhatsApp aberto! 🟢', { id: tid })
            else toast.error(data.mensagem, { id: tid })
        } catch (e) { toast.error('Erro de conexão.', { id: tid }) }
    }

    const handleCopy = (txt: string) => {
        if (!txt) return
        navigator.clipboard.writeText(txt)
        toast.success('Copiado! 📋')
    }

    const getPorteDesc = (code: string) => {
        const mapping: any = {
            '01': 'Microempresa (ME)',
            '03': 'Empresa de Pequeno Porte (EPP)',
            '05': 'Normal (Demais)',
            '00': 'Não Informado'
        }
        return mapping[code] || code || 'Não Informado'
    }

    const getNaturezaDesc = (code: string) => {
        const mapping: any = {
            '3085': 'Condomínio Edilício',
            '2054': 'Sociedade Anônima Fechada',
            '2062': 'Sociedade Empresária Limitada',
            '2135': 'Empresário (Individual)',
            '3999': 'Associação Privada',
            '2046': 'Sociedade Simples Pura',
            '2011': 'Empresa Pública',
            '2143': 'Cooperativa'
        }
        const cleanCode = code ? String(code).replace(/^0+/, '') : ''
        return mapping[cleanCode] || code || 'N/I'
    }

    const getCNAEDesc = (code: string) => {
        const mapping: any = {
            '8112500': 'Condomínios Prediais',
            '6810201': 'Compra e venda de imóveis próprios',
            '6810202': 'Aluguel de imóveis próprios',
            '6821801': 'Corretagem na compra e venda e avaliação de imóveis',
            '6821802': 'Corretagem no aluguel de imóveis',
            '6822600': 'Gestão e administração da propriedade imobiliária',
            '4110700': 'Incorporação de empreendimentos imobiliários',
            '4120400': 'Construção de edifícios',
            '9499500': 'Atividades associativas não especificadas'
        }
        return mapping[code] || code || 'N/I'
    }

    if (loading) return <div className="dossier-container" style={{ textAlign: 'center', paddingTop: '10rem' }}>Carregando dossiê do lead...</div>
    if (!empresa) return <div className="dossier-container" style={{ textAlign: 'center', paddingTop: '10rem' }}>Lead não encontrado.</div>

    const displayName = empresa.nome_fantasia || 
        empresa.razao_social
            .replace(/CONDOMINIO\s+(DO\s+)?EDIFICIO\s+/gi, '')
            .replace(/CONDOMINIO\s+/gi, '')
            .replace(/EDIFICIO\s+/gi, '')
            .trim();

    return (
        <div className="dossier-container">
            <div className="dossier-paper">
                
                {/* Hero Header */}
                <header className="hero-header">
                    <div className="chips-row">
                        <span className="m3-chip m3-chip-outline">CNPJ: {empresa.cnpj}</span>
                        <span className={`m3-chip ${empresa.identificador_matriz_filial === '1' ? 'm3-chip-primary' : 'm3-chip-outline'}`}>
                            {empresa.identificador_matriz_filial === '1' ? '🏢 MATRIZ' : '🏛️ FILIAL'}
                        </span>
                        <span className="m3-chip m3-chip-success">{empresa.status}</span>
                    </div>
                    <h1>{empresa.razao_social}</h1>
                    <div className="subtitle">✨ {displayName}</div>
                </header>

                {/* Partners Quick Bar */}
                {empresa.socios && (
                    <div className="partners-bar">
                        <span className="label">👤 Sócio(s):</span>
                        <span className="list">{empresa.socios.split(' | ').join(' • ')}</span>
                    </div>
                )}

                <div className="dossier-grid">
                    
                    {/* Left Column */}
                    <main className="dossier-col-main">
                        
                        {/* Seção de Sócios Detalhada */}
                        <section>
                            <SectionTitle icon="👤" title="Quadro Societário (QSA)" />
                            <div className="partners-grid">
                                {empresa.qsa_completo ? (
                                    (() => {
                                        try {
                                            const qsa = typeof empresa.qsa_completo === 'string' ? JSON.parse(empresa.qsa_completo) : empresa.qsa_completo
                                            return qsa.map((s: any, i: number) => (
                                                <div key={i} className="partner-card">
                                                    <div className="partner-name">{s.nome}</div>
                                                    <div className="partner-role">{s.qualificacao}</div>{s.cpf && <div style={{fontSize: "0.75rem", opacity: 0.8, color: "#535f70", marginTop: "4px"}}>CPF: {s.cpf}</div>}
                                                    <div style={{ display: 'flex', gap: '8px' }}>
                                                        <InvestigateBtn icon="⚖️" label="Jusbrasil" url={`https://www.jusbrasil.com.br/busca?q=${encodeURIComponent(s.nome)}`} />
                                                        <InvestigateBtn icon="💼" label="LinkedIn" url={`https://www.linkedin.com/search/results/all/?keywords=${encodeURIComponent(s.nome)}`} />
                                                    </div>
                                                </div>
                                            ))
                                        } catch (e) { return <div>Erro ao processar QSA</div> }
                                    })()
                                ) : (
                                    <div className="m3-card" style={{ gridColumn: '1/-1', textAlign: 'center', background: '#F8FAFD', borderStyle: 'dashed' }}>
                                        <p style={{ color: '#535F70', fontSize: '0.9rem', marginBottom: '1rem' }}>Dados de sócios não disponíveis.</p>
                                        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                                            <button className="btn-small" onClick={() => handleEnriquecerReceitaWS(empresa.cnpj)}>🚀 ReceitaWS</button>
                                            <button className="btn-small" onClick={() => handleEnriquecerIndividual(empresa.cnpj)}>🔍 OpenCNPJ</button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </section>

                        {/* Informações Institucionais */}
                        <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                            <div>
                                <SectionTitle icon="🏛️" title="Institucional" />
                                <div className="m3-card m3-card-elevated">
                                    <InfoItem label="Natureza Jurídica" value={getNaturezaDesc(empresa.natureza_juridica)} bold color="var(--m3-primary)" />
                                    <InfoItem label="CNAE Principal" value={`${empresa.cnae} - ${empresa.cnae_descricao || getCNAEDesc(empresa.cnae)}`} bold />
                                    
                                    {empresa.cnaes_secundarios && (
                                        <div style={{ marginTop: '1rem', padding: '12px', background: '#F0F4F8', borderRadius: '8px' }}>
                                            <div style={{ fontSize: '0.65rem', fontWeight: 900, color: '#535F70', textTransform: 'uppercase', marginBottom: '8px' }}>Atividades Secundárias</div>
                                            <div style={{ fontSize: '0.75rem', color: '#1A1C1E', whiteSpace: 'pre-line', lineHeight: '1.4' }}>
                                                {empresa.cnaes_secundarios}
                                            </div>
                                        </div>
                                    )}

                                    <InfoItem label="Porte" value={getPorteDesc(empresa.porte)} bold />
                                    <InfoItem label="Capital Social" value={empresa.capital_social ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(empresa.capital_social) : 'N/I'} />
                                    <InfoItem label="Início Atividade" value={empresa.data_inicio_atividade} />
                                </div>
                            </div>
                            <div>
                                <SectionTitle icon="📍" title="Localização" />
                                <div className="m3-card m3-card-elevated">
                                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#1A1C1E', marginBottom: '0.5rem' }}>{empresa.logradouro}, {empresa.numero}</div>
                                    <div style={{ color: '#535F70', fontWeight: 600 }}>{empresa.bairro}</div>
                                    <div style={{ color: '#535F70' }}>{empresa.municipio} — {empresa.uf}</div>
                                    <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#8E9199' }}>CEP: {empresa.cep}</div>
                                    {empresa.complemento && <div style={{ fontSize: '0.85rem', color: '#8E9199' }}>Complemento: {empresa.complemento}</div>}
                                </div>
                            </div>
                        </section>

                        {/* Anotações */}
                        <section style={{ marginTop: '2.5rem' }}>
                            <SectionTitle icon="📝" title="Anotações de Investigação" />
                            <textarea 
                                className="notes-area"
                                value={investigationNotes}
                                onChange={(e) => setInvestigationNotes(e.target.value)}
                                placeholder="Registre aqui insights sobre decisores, melhores horários e histórico..."
                            />
                            <button className="btn-save" onClick={async () => {
                                const { error } = await supabase.from('empresas_sjc').update({ notas_investigacao: investigationNotes }).eq('id', empresa.id)
                                if (error) toast.error('Erro ao salvar.')
                                else toast.success('Anotações salvas! ✅')
                            }}>
                                💾 Salvar Anotações
                            </button>
                        </section>
                    </main>

                    {/* Right Column */}
                    <aside className="dossier-col-side">
                        
                        {/* Inteligência & Score */}
                        <section className="m3-card hub-card">
                            <div className="score-display">
                                <div style={{ fontSize: '0.7rem', fontWeight: 900, color: 'var(--m3-primary)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Qualificação do Prospecto</div>
                                <div className="score-dots">
                                    {[1,2,3,4,5].map(s => (
                                        <div key={s} className="score-dot" style={{ background: s <= empresa.score ? 'var(--m3-primary)' : '#D3E3FD' }} />
                                    ))}
                                </div>
                                <div className="score-value">{empresa.score}/5</div>
                            </div>

                            <SectionTitle icon="🚀" title="Hub de Investigação" />
                            <div className="hub-actions-grid">
                                <HubBtn icon="🏢" label="JUCESP" url="https://www.jucesponline.sp.gov.br/Default.aspx" color="#C00" active />
                                <HubBtn icon="🗺️" label="Maps" url={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(empresa.razao_social + ' ' + empresa.municipio)}`} color="#4285F4" active />
                                <HubBtn icon="🌐" label="Site" url={empresa.site || empresa.site_google} color="#34A853" active={!!(empresa.site || empresa.site_google)} />
                                <HubBtn icon="⚖️" label="Jusbrasil" url={`https://www.jusbrasil.com.br/busca?q=${empresa.cnpj?.replace(/\D/g, '')}`} color="#1F1F1F" active />
                                <HubBtn icon="💼" label="LinkedIn" url={`https://www.google.com.br/search?q=site:linkedin.com/company+"${encodeURIComponent(empresa.razao_social.replace(/CONDOMINIO\s+(DO\s+)?EDIFICIO\s+/gi, ''))}"`} color="#0077B5" active />
                                <HubBtn icon="📸" label="Instagram" url={`https://www.google.com.br/search?q=site:instagram.com+"${encodeURIComponent(empresa.razao_social)}"+${empresa.municipio}`} color="#E1306C" active />
                            </div>

                            <div style={{ marginTop: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '12px', background: serverOnline ? '#E6F4EA' : '#FCE8E6', borderRadius: '12px' }}>
                                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: serverOnline ? '#1E8E3E' : '#D93025' }} />
                                <span style={{ fontSize: '0.65rem', fontWeight: 800, color: serverOnline ? '#1E8E3E' : '#D93025' }}>ROBÔ {serverOnline ? 'ONLINE' : 'OFFLINE'}</span>
                            </div>
                        </section>

                        {/* Comunicação */}
                        <section style={{ marginTop: '2.5rem' }}>
                            <SectionTitle icon="📱" title="Canais de Contato" />
                            <div className="action-grid" style={{ gridTemplateColumns: '1fr' }}>
                                <ActionBtn icon="💬" label="WhatsApp" value={empresa.whatsapp} url={`https://wa.me/55${empresa.whatsapp}`} active={!!empresa.whatsapp} onAdbCall={handleAdbCall} onAdbWhats={handleAdbWhatsapp} onCopy={handleCopy} color="#25D366" />
                                <ActionBtn icon="📍" label="Maps (Tel)" value={empresa.tel_maps} url={`tel:${empresa.tel_maps}`} active={!!empresa.tel_maps} onAdbCall={handleAdbCall} onCopy={handleCopy} color="#4285F4" />
                                <ActionBtn icon="🏢" label="Receita" value={empresa.telefone_completo_1} active={!!empresa.telefone_completo_1} onAdbCall={handleAdbCall} onCopy={handleCopy} color="#5F6368" />
                                <ActionBtn icon="💎" label="OpenCNPJ" value={empresa.tel_opencnpj} active={!!empresa.tel_opencnpj} onAdbCall={handleAdbCall} onCopy={handleCopy} color="#F9AB00" />
                            </div>
                            
                            {empresa.email && (
                                <div className="m3-card" style={{ marginTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#F8FAFD' }}>
                                    <div style={{ overflow: 'hidden' }}>
                                        <div className="m3-label">E-mail Oficial</div>
                                        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--m3-primary)', textOverflow: 'ellipsis', overflow: 'hidden' }}>{empresa.email}</div>
                                    </div>
                                    <button className="btn-icon" onClick={() => handleCopy(empresa.email)}>📋</button>
                                </div>
                            )}

                            <button onClick={openEditModal} className="btn-secondary" style={{ width: '100%', marginTop: '1.5rem', padding: '1rem', border: '1px solid var(--m3-outline)', borderRadius: '12px', background: 'white', fontWeight: 800, cursor: 'pointer' }}>
                                ⚙️ Editar Dados no Banco
                            </button>
                        </section>
                    </aside>
                </div>

                {/* Footer Meta */}
                <footer style={{ padding: '1.5rem 3rem', background: '#F8FAFD', borderTop: '1px solid var(--m3-outline-variant)', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#8E9199' }}>
                    <span>ID: {empresa.id}</span>
                    <span>Atualizado em: {new Date(empresa.atualizado_em).toLocaleString('pt-BR')}</span>
                </footer>
            </div>

            {/* Modal de Edição */}
            {showEditModal && (
                <div className="m3-modal-overlay">
                    <div className="m3-modal">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem' }}>
                            <div>
                                <h2 style={{ margin: 0, fontWeight: 900 }}>Editar Dossiê</h2>
                                <p style={{ margin: 0, color: '#535F70', fontSize: '0.85rem' }}>Ajuste os dados capturados manualmente.</p>
                            </div>
                            <button onClick={() => setShowEditModal(false)} className="btn-icon">✕</button>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                            <EditField label="Razão Social" value={editForm.razao_social} onChange={v => setEditForm({...editForm, razao_social: v})} />
                            <EditField label="Nome Fantasia" value={editForm.nome_fantasia} onChange={v => setEditForm({...editForm, nome_fantasia: v})} />
                            <EditField label="WhatsApp" value={editForm.whatsapp} onChange={v => setEditForm({...editForm, whatsapp: v})} />
                            <EditField label="Telefone Maps" value={editForm.tel_maps} onChange={v => setEditForm({...editForm, tel_maps: v})} />
                            <EditField label="Telefone Receita" value={editForm.telefone_completo_1} onChange={v => setEditForm({...editForm, telefone_completo_1: v})} />
                            <EditField label="Telefone OpenCNPJ" value={editForm.tel_opencnpj} onChange={v => setEditForm({...editForm, tel_opencnpj: v})} />
                            <EditField label="E-mail" value={editForm.email} onChange={v => setEditForm({...editForm, email: v})} />
                            <EditField label="E-mail Capturado" value={editForm.email_site} onChange={v => setEditForm({...editForm, email_site: v})} />
                        </div>

                        <div style={{ display: 'flex', gap: '1rem', marginTop: '2.5rem' }}>
                            <button onClick={() => setShowEditModal(false)} className="btn-flat" style={{ flex: 1 }}>Cancelar</button>
                            <button onClick={handleSaveDatabase} className="btn-save" style={{ flex: 2, margin: 0 }}>Salvar Alterações</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

// Internal Mini Components
function SectionTitle({ icon, title }: { icon: string, title: string }) {
    return (
        <h4 className="section-title">
            <span>{icon}</span> {title}
        </h4>
    )
}

function InfoItem({ label, value, bold, color }: { label: string, value: any, bold?: boolean, color?: string }) {
    return (
        <div style={{ marginBottom: '1rem' }}>
            <div className="m3-label">{label}</div>
            <div style={{ fontSize: '0.95rem', color: color || '#1F1F1F', fontWeight: bold ? 800 : 500 }}>{value || '—'}</div>
        </div>
    )
}

function InvestigateBtn({ icon, label, url }: { icon: string, label: string, url: string }) {
    return (
        <a href={url} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', background: 'white', borderRadius: '30px', border: '1px solid #E1E2EC', textDecoration: 'none', color: '#44474E', fontSize: '0.7rem', fontWeight: 700 }}>
            <span>{icon}</span> {label}
        </a>
    )
}

function ActionBtn({ icon, label, value, color, active, onAdbCall, onAdbWhats, onCopy }: any) {
    if (!active) return null
    const values = String(value || '').split('|').map(v => v.trim()).filter(v => v)

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {values.map((v, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px' }}>
                    <div className="m3-btn-action" style={{ flex: 1 }}>
                        <span className="icon">{icon}</span>
                        <div style={{ overflow: 'hidden' }}>
                            <div className="label">{label} {values.length > 1 ? `#${i+1}` : ''}</div>
                            <div className="value">{v}</div>
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: '4px' }}>
                        <button onClick={() => onCopy(v)} className="btn-icon-small" title="Copiar">📋</button>
                        <button onClick={() => onAdbCall(v)} className="btn-icon-small" title="Ligar">📱</button>
                        {onAdbWhats && <button onClick={() => onAdbWhats(v)} className="btn-icon-small" style={{ color: '#25D366' }} title="WhatsApp">🟢</button>}
                    </div>
                </div>
            ))}
        </div>
    )
}

function HubBtn({ icon, label, url, active, color }: any) {
    return (
        <a href={active ? url : '#'} target={active ? "_blank" : "_self"} rel="noreferrer" className="hub-btn" style={{ opacity: active ? 1 : 0.3, pointerEvents: active ? 'auto' : 'none' }}>
            <span style={{ fontSize: '1.4rem' }}>{icon}</span>
            <div style={{ fontSize: '0.6rem', fontWeight: 800, color: active ? color : '#8E9199', textTransform: 'uppercase' }}>{label}</div>
        </a>
    )
}

function EditField({ label, value, onChange }: { label: string, value: any, onChange: (v: string) => void }) {
    return (
        <div className="m3-input-group">
            <label className="m3-label">{label}</label>
            <input type="text" className="m3-input" value={value || ''} onChange={e => onChange(e.target.value)} />
        </div>
    )
}
