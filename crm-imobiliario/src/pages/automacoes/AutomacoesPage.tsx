import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import toast from 'react-hot-toast'
import './AutomacoesPage.css'

interface ConfiguracaoIA {
    id: string
    prompt_personalidade: string
    requer_aprovacao_mensagens: boolean
    max_chats_dia: number
    delay_entre_chats: number
}

interface TemplateMensagem {
    id: string
    ordem: number
    tipo: 'inicial' | 'followup_sem_resposta' | 'followup_com_resposta'
    conteudo: string
    dias_aguardar: number
}

export function AutomacoesPage() {
    const [config, setConfig] = useState<ConfiguracaoIA | null>(null)
    const [savingConfig, setSavingConfig] = useState(false)

    const [templates, setTemplates] = useState<TemplateMensagem[]>([])
    const [loading, setLoading] = useState(true)

    // Form states para o modal de template
    const [isTemplateModalOpen, setTemplateModalOpen] = useState(false)
    const [editTemplate, setEditTemplate] = useState<TemplateMensagem | null>(null)
    const [savingTemplate, setSavingTemplate] = useState(false)

    // ── Chat OLX Bot ──────────────────────────────────────────────────────────
    const SCRAPER_URL = 'http://127.0.0.1:8765'
    const [chatRunning, setChatRunning] = useState(false)
    const [chatLoadingAction, setChatLoadingAction] = useState(false)
    const [chatsHoje, setChatsHoje] = useState(0)

    useEffect(() => {
        carregarDados()
        carregarStatusChat()
        // Polling do status do bot a cada 5s
        const interval = setInterval(carregarStatusChat, 5000)
        return () => clearInterval(interval)
    }, [])

    async function carregarStatusChat() {
        try {
            const [statusRes, countRes] = await Promise.all([
                fetch(`${SCRAPER_URL}/send-chat/status`).then(r => r.json()),
                supabase
                    .from('prospecoes_chat')
                    .select('id', { count: 'exact', head: true })
                    .gte('data_primeiro_envio', new Date().toISOString().slice(0, 10))
            ])
            setChatRunning(statusRes?.running ?? false)
            setChatsHoje(countRes.count ?? 0)
        } catch {
            // Scraper offline — não faz nada
        }
    }

    async function handleIniciarChat() {
        setChatLoadingAction(true)
        try {
            const res = await fetch(`${SCRAPER_URL}/send-chat/batch`, { method: 'POST' })
            const data = await res.json()
            if (data.status === 'already_running') {
                toast('Bot de chat já está rodando!')
            } else {
                toast.success('Lote de chat OLX iniciado!')
                setChatRunning(true)
            }
        } catch {
            toast.error('Erro ao conectar com o scraper. Ele está online?')
        } finally {
            setChatLoadingAction(false)
        }
    }

    async function handlePararChat() {
        setChatLoadingAction(true)
        try {
            await fetch(`${SCRAPER_URL}/send-chat/stop`, { method: 'POST' })
            toast.success('Sinal de parada enviado!')
            setChatRunning(false)
        } catch {
            toast.error('Erro ao conectar com o scraper.')
        } finally {
            setChatLoadingAction(false)
        }
    }

    async function carregarDados() {
        setLoading(true)
        try {
            const { data: configData } = await supabase
                .from('configuracoes_ia')
                .select('*')
                .single()
            if (configData) setConfig(configData)

            const { data: temp_data } = await supabase
                .from('templates_mensagem')
                .select('*')
                .order('ordem', { ascending: true })
            if (temp_data) setTemplates(temp_data)

        } catch (err: any) {
            console.error('Erro ao carregar configurações:', err)
        } finally {
            setLoading(false)
        }
    }

    async function handleSaveConfig() {
        if (!config) return
        setSavingConfig(true)
        try {
            const { error } = await supabase
                .from('configuracoes_ia')
                .update({
                    prompt_personalidade: config.prompt_personalidade,
                    requer_aprovacao_mensagens: config.requer_aprovacao_mensagens,
                    max_chats_dia: config.max_chats_dia,
                    delay_entre_chats: config.delay_entre_chats ?? 60
                })
                .eq('id', config.id)

            if (error) throw error
            toast.success('Configurações da IA salvas com sucesso!')
        } catch (err: any) {
            console.error(err)
            toast.error('Erro ao salvar as configurações.')
        } finally {
            setSavingConfig(false)
        }
    }

    async function handleSaveTemplate(e: React.FormEvent) {
        e.preventDefault()
        if (!editTemplate) return
        setSavingTemplate(true)

        try {
            if (editTemplate.id === 'new') {
                // Inserção
                const { id, ...newRecord } = editTemplate
                const { error } = await supabase.from('templates_mensagem').insert([newRecord])
                if (error) throw error
                toast.success('Template criado!')
            } else {
                // Atualização
                const { id, ...updateRecord } = editTemplate
                const { error } = await supabase.from('templates_mensagem').update(updateRecord).eq('id', id)
                if (error) throw error
                toast.success('Template atualizado!')
            }
            setTemplateModalOpen(false)
            carregarDados()
        } catch (err: any) {
            console.error(err)
            toast.error('Erro ao salvar o template.')
        } finally {
            setSavingTemplate(false)
        }
    }

    async function handleDeleteTemplate(id: string) {
        if (!window.confirm('Certeza que deseja deletar este template?')) return
        try {
            const { error } = await supabase.from('templates_mensagem').delete().eq('id', id)
            if (error) throw error
            toast.success('Template excluído.')
            carregarDados()
        } catch (err: any) {
            console.error(err)
            toast.error('Erro ao excluir template.')
        }
    }

    function openNewTemplateModal() {
        setEditTemplate({
            id: 'new',
            ordem: templates.length + 1,
            tipo: 'inicial',
            conteudo: '',
            dias_aguardar: 1
        })
        setTemplateModalOpen(true)
    }

    if (loading) return <div className="automacoes-container">Carregando automações...</div>

    return (
        <div className="automacoes-container">
            <div className="dashboard-wrapper">
                <header className="automacoes-header">
                    <h1>⚙️ Automações e IA</h1>
                    <p>Configure o comportamento do robô e templates de mensagens para prospecção.</p>
                </header>

                <div className="automacoes-grid">

                    {/* CONFIGURAÇÕES GLOBAIS DA IA */}
                    <div className="m3-card">
                        <h2 className="card-title">
                            🧠 Comportamento da IA
                        </h2>

                        {!config ? (
                            <div style={{ color: 'var(--m3-error)' }}>Problema ao carregar configs.</div>
                        ) : (
                            <div className="m3-form">
                                <div className="m3-field-group">
                                    <label className="m3-label">Prompt de Personalidade Geral</label>
                                    <textarea
                                        className="m3-textarea"
                                        value={config.prompt_personalidade}
                                        onChange={(e) => setConfig({ ...config, prompt_personalidade: e.target.value })}
                                        rows={6}
                                        placeholder="Ex: Você é um corretor de imóveis prestativo e direto..."
                                    />
                                    <small style={{ color: 'var(--m3-on-surface-variant)' }}>
                                        Defina como a IA deve conversar com o vendedor.
                                    </small>
                                </div>

                                <div className="m3-checkbox-group" onClick={() => setConfig({ ...config, requer_aprovacao_mensagens: !config.requer_aprovacao_mensagens })}>
                                    <input
                                        type="checkbox"
                                        className="m3-checkbox"
                                        checked={config.requer_aprovacao_mensagens}
                                        readOnly
                                    />
                                    <label>Requerer aprovação manual antes de disparar chats</label>
                                </div>

                                <div className="m3-field-group">
                                    <label className="m3-label">Máx de Chats Novos por Dia</label>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                        <input
                                            type="number"
                                            className="m3-input"
                                            style={{ width: '120px' }}
                                            value={config.max_chats_dia}
                                            onChange={(e) => setConfig({ ...config, max_chats_dia: Number(e.target.value) })}
                                        />
                                        <span style={{ fontSize: '0.85rem', color: 'var(--m3-on-surface-variant)' }}>
                                            Sugestão: 20-40 para evitar bloqueios.
                                        </span>
                                    </div>
                                </div>

                                <div className="m3-field-group">
                                    <label className="m3-label">Tempo de Espera entre Envios (segundos)</label>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                        <input
                                            type="number"
                                            className="m3-input"
                                            style={{ width: '120px' }}
                                            value={config.delay_entre_chats ?? 60}
                                            onChange={(e) => setConfig({ ...config, delay_entre_chats: Number(e.target.value) })}
                                        />
                                        <span style={{ fontSize: '0.85rem', color: 'var(--m3-on-surface-variant)' }}>
                                            O tempo que o robô pausa entre os disparos na OLX.
                                        </span>
                                    </div>
                                </div>

                                <button 
                                    className="m3-btn m3-btn-primary" 
                                    style={{ marginTop: '1rem' }} 
                                    onClick={handleSaveConfig} 
                                    disabled={savingConfig}
                                >
                                    {savingConfig ? 'Salvando...' : 'Salvar Configurações'}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* TEMPLATES DE MENSAGEM */}
                    <div className="m3-card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                            <h2 className="card-title" style={{ margin: 0 }}>
                                📝 Templates Base
                            </h2>
                            <button className="m3-btn m3-btn-secondary" onClick={openNewTemplateModal}>
                                + Novo Template
                            </button>
                        </div>

                        <div style={{ fontSize: '0.9rem', color: 'var(--m3-on-surface-variant)', marginBottom: '1.5rem' }}>
                            Os templates guiam o conteúdo da conversa que a IA reescreverá dinamicamente.
                        </div>

                        {templates.length === 0 ? (
                            <div style={{ color: 'var(--m3-on-surface-variant)', textAlign: 'center', padding: '3rem 0' }}>
                                Nenhum template encontrado.
                            </div>
                        ) : (
                            <div className="template-list">
                                {templates.map(t => (
                                    <div key={t.id} className="template-item">
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                                            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                                <span className="template-badge">Passo {t.ordem}</span>
                                                <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                                                    {t.tipo === 'inicial' ? 'Abertura' : t.tipo === 'followup_sem_resposta' ? 'Vácuo' : 'Follow-up'}
                                                </span>
                                            </div>
                                            <div style={{ display: 'flex', gap: '1rem' }}>
                                                <button onClick={() => { setEditTemplate(t); setTemplateModalOpen(true) }} className="m3-btn-text" style={{ border: 'none', background: 'none', color: 'var(--m3-primary)', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}>Editar</button>
                                                <button onClick={() => handleDeleteTemplate(t.id)} className="m3-btn-text" style={{ border: 'none', background: 'none', color: 'var(--m3-error)', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}>Excluir</button>
                                            </div>
                                        </div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--m3-on-surface-variant)' }}>
                                            ⏱ Aguardar: {t.dias_aguardar === 0 ? 'Imediato' : `${t.dias_aguardar} minuto(s)`}
                                        </div>
                                        <div className="template-content-preview">
                                            "{t.conteudo}"
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* DISPARO DE CHAT OLX */}
                    <div className={`m3-card status-card ${chatRunning ? 'running' : ''}`} style={{ gridColumn: '1 / -1' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                            <h2 className="card-title" style={{ margin: 0 }}>
                                💬 Robô de Chat OLX
                            </h2>
                            <div className={`status-indicator ${chatRunning ? 'running' : 'stopped'}`}>
                                {chatRunning && <div className="pulsing-dot" />}
                                {chatRunning ? 'RODANDO AGORA' : 'DESCONECTADO'}
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '3rem', flexWrap: 'wrap', alignItems: 'center' }}>
                            {/* Stats */}
                            <div style={{ display: 'flex', gap: '2rem' }}>
                                <div style={{ background: 'var(--m3-surface)', padding: '1.5rem', borderRadius: '20px', textAlign: 'center', minWidth: '140px', border: '1px solid var(--m3-outline-variant)' }}>
                                    <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--m3-primary)' }}>{chatsHoje}</div>
                                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--m3-secondary)', marginTop: '0.25rem' }}>ENVIADOS HOJE</div>
                                </div>
                                
                                {config && (
                                    <div style={{ background: 'var(--m3-surface)', padding: '1.5rem', borderRadius: '20px', textAlign: 'center', minWidth: '140px', border: '1px solid var(--m3-outline-variant)' }}>
                                        <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--m3-secondary)' }}>{config.max_chats_dia}</div>
                                        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--m3-secondary)', marginTop: '0.25rem' }}>LIMITE DIÁRIO</div>
                                    </div>
                                )}
                            </div>

                            {/* Controls */}
                            <div style={{ flex: 1, minWidth: '300px' }}>
                                <p style={{ fontSize: '1rem', color: 'var(--m3-on-surface-variant)', marginBottom: '1.5rem', lineHeight: 1.6 }}>
                                    O robô processa automaticamente novos leads da OLX, enviando a mensagem inicial com delay randomizado (sugerido 45-90s) para manter a conta segura.
                                </p>
                                <div style={{ display: 'flex', gap: '1rem' }}>
                                    {!chatRunning ? (
                                        <button
                                            className="m3-btn m3-btn-primary"
                                            style={{ padding: '1rem 2.5rem', fontSize: '1rem' }}
                                            onClick={handleIniciarChat}
                                            disabled={chatLoadingAction}
                                        >
                                            {chatLoadingAction ? '⏳ Iniciando...' : '▶ Enviar Scripts'}
                                        </button>
                                    ) : (
                                        <button
                                            className="m3-btn m3-btn-danger"
                                            style={{ padding: '1rem 2.5rem', fontSize: '1rem' }}
                                            onClick={handlePararChat}
                                            disabled={chatLoadingAction}
                                        >
                                            {chatLoadingAction ? '⏳ Parando...' : '⏹ Parar Operação'}
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* MODAL DE TEMPLATE */}
                {isTemplateModalOpen && editTemplate && (
                    <div className="m3-modal-overlay">
                        <div className="m3-modal" style={{ animation: 'slideUp 0.3s ease-out' }}>
                            <h3 className="card-title" style={{ fontSize: '1.5rem' }}>
                                {editTemplate.id === 'new' ? '✨ Novo Template' : '✏️ Editar Template'}
                            </h3>
                            <form onSubmit={handleSaveTemplate} className="m3-form">

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                                    <div className="m3-field-group" style={{ marginBottom: 0 }}>
                                        <label className="m3-label">Ordem do Passo</label>
                                        <input type="number" className="m3-input" required value={editTemplate.ordem} onChange={e => setEditTemplate({ ...editTemplate, ordem: Number(e.target.value) })} />
                                    </div>
                                    <div className="m3-field-group" style={{ marginBottom: 0 }}>
                                        <label className="m3-label">Minutos a Esperar</label>
                                        <input type="number" min="0" className="m3-input" required value={editTemplate.dias_aguardar} onChange={e => setEditTemplate({ ...editTemplate, dias_aguardar: Number(e.target.value) })} />
                                    </div>
                                </div>

                                <div className="m3-field-group">
                                    <label className="m3-label">Tipo de Mensagem</label>
                                    <select className="m3-select" value={editTemplate.tipo} onChange={e => setEditTemplate({ ...editTemplate, tipo: e.target.value as any })}>
                                        <option value="inicial">Inicial (Abertura de chat)</option>
                                        <option value="followup_sem_resposta">Follow-up (Sem Resposta)</option>
                                        <option value="followup_com_resposta">Follow-up (Com Resposta)</option>
                                    </select>
                                </div>

                                <div className="m3-field-group">
                                    <label className="m3-label">Gabarito (Instrução para a IA)</label>
                                    <textarea className="m3-textarea" required rows={5} value={editTemplate.conteudo} onChange={e => setEditTemplate({ ...editTemplate, conteudo: e.target.value })} placeholder="Descreva o que a IA deve falar neste passo..." />
                                </div>

                                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '2.5rem' }}>
                                    <button type="button" className="m3-btn m3-btn-secondary" onClick={() => setTemplateModalOpen(false)}>Cancelar</button>
                                    <button type="submit" className="m3-btn m3-btn-primary" disabled={savingTemplate}>{savingTemplate ? 'Salvando...' : 'Salvar Template'}</button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
