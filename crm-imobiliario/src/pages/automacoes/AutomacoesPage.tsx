import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import toast from 'react-hot-toast'

interface ConfiguracaoIA {
    id: string
    prompt_personalidade: string
    requer_aprovacao_mensagens: boolean
    max_chats_dia: number
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

    useEffect(() => {
        carregarDados()
    }, [])

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
                    max_chats_dia: config.max_chats_dia
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

    if (loading) return <div style={{ padding: '2rem' }}>Carregando automações...</div>

    return (
        <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                ⚙️ Automações e Inteligência Artificial
            </h1>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
                Configure o comportamento do robô de prospecção e defina os templates de mensagens para a OLX.
            </p>

            <div style={{ display: 'grid', gap: '2rem', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))' }}>

                {/* CONFIGURAÇÕES GLOBAIS DA IA */}
                <div style={{ background: 'var(--bg-card)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
                    <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        🧠 Comportamento da IA
                    </h2>

                    {!config ? (
                        <div style={{ color: 'var(--error)' }}>Problema ao carregar configs.</div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.25rem', fontWeight: 500 }}>
                                    Prompt de Personalidade Geral
                                </label>
                                <textarea
                                    value={config.prompt_personalidade}
                                    onChange={(e) => setConfig({ ...config, prompt_personalidade: e.target.value })}
                                    rows={4}
                                    style={{
                                        width: '100%', padding: '0.75rem', borderRadius: '8px',
                                        border: '1px solid var(--border)', background: 'var(--bg-body)', color: 'var(--text-primary)'
                                    }}
                                />
                                <small style={{ color: 'var(--text-muted)' }}>Defina como a IA deve conversar com o vendedor.</small>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <input
                                    type="checkbox"
                                    id="aprovacao"
                                    checked={config.requer_aprovacao_mensagens}
                                    onChange={(e) => setConfig({ ...config, requer_aprovacao_mensagens: e.target.checked })}
                                />
                                <label htmlFor="aprovacao">Requerer aprovação manual antes de disparar chats</label>
                            </div>

                            <div>
                                <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.25rem', fontWeight: 500 }}>
                                    Máx de Chats Novos por Dia
                                </label>
                                <input
                                    type="number"
                                    value={config.max_chats_dia}
                                    onChange={(e) => setConfig({ ...config, max_chats_dia: Number(e.target.value) })}
                                    style={{
                                        width: '100px', padding: '0.5rem', borderRadius: '8px',
                                        border: '1px solid var(--border)', background: 'var(--bg-body)', color: 'var(--text-primary)'
                                    }}
                                />
                                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '10px' }}>Para evitar bloqueios da OLX.</span>
                            </div>

                            <button className="btn-primary" style={{ marginTop: '1rem', alignSelf: 'flex-start' }} onClick={handleSaveConfig} disabled={savingConfig}>
                                {savingConfig ? 'Salvando...' : 'Salvar Configurações'}
                            </button>
                        </div>
                    )}
                </div>

                {/* TEMPLATES DE MENSAGEM */}
                <div style={{ background: 'var(--bg-card)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h2 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            📝 Templates Base de Resposta
                        </h2>
                        <button className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.85rem' }} onClick={openNewTemplateModal}>
                            + Novo Template
                        </button>
                    </div>

                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                        Os templates guiam o conteúdo da conversa. A IA reescreverá o template dinamicamente usando a personalidade acima para soar natural.
                    </div>

                    {templates.length === 0 ? (
                        <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem 0' }}>
                            Nenhum template encontrado.
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {templates.map(t => (
                                <div key={t.id} style={{ border: '1px solid var(--border)', borderRadius: '8px', padding: '1rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                        <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--primary)' }}>Passo {t.ordem}: {t.tipo === 'inicial' ? 'Inicial' : t.tipo === 'followup_sem_resposta' ? 'Follow-up (sem resp.)' : 'Follow-up (com resp.)'}</span>
                                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                                            <button onClick={() => { setEditTemplate(t); setTemplateModalOpen(true) }} style={{ border: 'none', background: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem' }}>Editar</button>
                                            <button onClick={() => handleDeleteTemplate(t.id)} style={{ border: 'none', background: 'none', color: 'var(--error)', cursor: 'pointer', fontSize: '0.9rem' }}>Excluir</button>
                                        </div>
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                                        Disparo em: {t.dias_aguardar === 0 ? 'No mesmo dia' : `Após ${t.dias_aguardar} dia(s)`}
                                    </div>
                                    <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontStyle: 'italic', background: 'var(--bg-body)', padding: '0.5rem', borderRadius: '4px' }}>
                                        "{t.conteudo}"
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* MODAL DE TEMPLATE */}
            {isTemplateModalOpen && editTemplate && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.5)', zIndex: 1000,
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                    <div style={{
                        background: 'var(--bg-card)', padding: '2rem', borderRadius: '12px',
                        width: '100%', maxWidth: '500px', border: '1px solid var(--border)'
                    }}>
                        <h3 style={{ fontSize: '1.2rem', marginBottom: '1.5rem', marginTop: 0 }}>
                            {editTemplate.id === 'new' ? 'Criar Template' : 'Editar Template'}
                        </h3>
                        <form onSubmit={handleSaveTemplate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

                            <div style={{ display: 'flex', gap: '1rem' }}>
                                <div style={{ flex: 1 }}>
                                    <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.2rem' }}>Ordem do Passo</label>
                                    <input type="number" required value={editTemplate.ordem} onChange={e => setEditTemplate({ ...editTemplate, ordem: Number(e.target.value) })} style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg-body)', color: 'var(--text-primary)' }} />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.2rem' }}>Dias a Esperar</label>
                                    <input type="number" min="0" required value={editTemplate.dias_aguardar} onChange={e => setEditTemplate({ ...editTemplate, dias_aguardar: Number(e.target.value) })} style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg-body)', color: 'var(--text-primary)' }} />
                                </div>
                            </div>

                            <div>
                                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.2rem' }}>Tipo de Mensagem</label>
                                <select value={editTemplate.tipo} onChange={e => setEditTemplate({ ...editTemplate, tipo: e.target.value as any })} style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg-body)', color: 'var(--text-primary)' }}>
                                    <option value="inicial">Inicial (Abertura de chat)</option>
                                    <option value="followup_sem_resposta">Follow-up (Sem Resposta)</option>
                                    <option value="followup_com_resposta">Follow-up (Contagem)</option>
                                </select>
                            </div>

                            <div>
                                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.2rem' }}>Gabarito da Mensagem (Instrução para a IA)</label>
                                <textarea required rows={4} value={editTemplate.conteudo} onChange={e => setEditTemplate({ ...editTemplate, conteudo: e.target.value })} style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg-body)', color: 'var(--text-primary)', resize: 'vertical' }} />
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
                                <button type="button" className="btn-secondary" onClick={() => setTemplateModalOpen(false)}>Cancelar</button>
                                <button type="submit" className="btn-primary" disabled={savingTemplate}>{savingTemplate ? 'Salvando...' : 'Salvar Template'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

        </div>
    )
}
