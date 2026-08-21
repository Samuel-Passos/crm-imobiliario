import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import { createClient } from '@supabase/supabase-js'
import './TemplatesPage.css' // Importando o novo CSS

const supabase = createClient(
    import.meta.env.VITE_SUPABASE_URL,
    import.meta.env.VITE_SUPABASE_ANON_KEY
)

const ROBO_URL = 'http://localhost:8766'

interface Settings {
    [key: string]: string | number
}

export function TemplatesPage() {
    const [settings, setSettings] = useState<Settings | null>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)

    useEffect(() => {
        carregarSettings()
    }, [])

    async function carregarSettings() {
        try {
            const res = await fetch(`${ROBO_URL}/adb/settings`)
            const data = await res.json()
            if (data.ok) setSettings(data.settings)
            else toast.error('Erro ao carregar templates.')
        } catch (error) { toast.error('Servidor offline.') }
        finally { setLoading(false) }
    }

    async function salvarSettings() {
        if (!settings) return
        setSaving(true)
        const tid = toast.loading('Salvando fábrica...')
        try {
            const res = await fetch(`${ROBO_URL}/adb/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ settings })
            })
            const data = await res.json()
            if (data.ok) toast.success('Escritório de Mensagens atualizado! 📝', { id: tid })
            else toast.error(data.mensagem || 'Erro ao salvar.', { id: tid })
        } catch (error) { toast.error('Falha de conexão.', { id: tid }) }
        finally { setSaving(false) }
    }

    const handleChange = (key: string, value: string | number) => {
        setSettings(prev => prev ? { ...prev, [key]: value } : null)
    }

    async function salvarUnico(key: string, value: any) {
        setSaving(true)
        const tid = toast.loading('Salvando template...')
        try {
            const updatedSettings = { ...settings, [key]: value }
            const res = await fetch(`${ROBO_URL}/adb/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ settings: updatedSettings })
            })
            const data = await res.json()
            if (data.ok) toast.success('Salvo individualmente! ✅', { id: tid })
            else toast.error('Erro ao salvar.', { id: tid })
        } catch (error) { toast.error('Falha de conexão.', { id: tid }) }
        finally { setSaving(false) }
    }

    if (loading) return (
        <div className="templates-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📝</div>
                <div style={{ fontWeight: 800, color: '#535F70' }}>Abrindo Fábrica de Mensagens...</div>
            </div>
        </div>
    )

    return (
        <div className="templates-container">
            <div className="templates-wrapper">
                
                {/* Header Section */}
                <header className="templates-header">
                    <div>
                        <h1>Fábrica de Mensagens</h1>
                        <p>Customize os scripts e automações de comunicação.</p>
                    </div>
                    <button onClick={salvarSettings} className="m3-btn m3-btn-primary" disabled={saving}>
                        {saving ? 'Gravando...' : '💾 Salvar Todos os Templates'}
                    </button>
                </header>

                <div style={{ display: 'grid', gap: '4rem' }}>
                    
                    {/* SEÇÃO 1: DISPONIBILIDADE */}
                    <section>
                        <header className="category-header">
                            <h2><span>🤖</span> Robô de Disponibilidade</h2>
                            <p>Mensagens de verificação automática enviadas aos proprietários.</p>
                        </header>

                        <TemplateEditor 
                            title="Verificação de Imóvel (WhatsApp)"
                            subtitle="Template padrão usado para confirmar se o imóvel ainda está disponível."
                            icon="📱"
                            id="tpl_whatsapp"
                            fieldKey="TEMPLATE_WHATSAPP_DISP"
                            value={settings?.TEMPLATE_WHATSAPP_DISP as string}
                            tags={['{proprietario}', '{referencia}', '{remetente}', '{link}']}
                            onSave={salvarUnico}
                            onChange={handleChange}
                        />

                        <TemplateEditor 
                            title="Corpo de E-Mail"
                            subtitle="Estrutura do e-mail de sondagem para proprietários."
                            icon="📧"
                            id="tpl_email"
                            fieldKey="TEMPLATE_EMAIL_CORPO"
                            value={settings?.TEMPLATE_EMAIL_CORPO as string}
                            tags={['{proprietario}', '{referencia}', '{remetente}']}
                            onSave={salvarUnico}
                            onChange={handleChange}
                            isEmail
                            subject={settings?.TEMPLATE_EMAIL_ASSUNTO as string}
                            onSubjectChange={(v: any) => handleChange('TEMPLATE_EMAIL_ASSUNTO', v)}
                        />
                    </section>

                    {/* SEÇÃO 2: CAMPANHAS */}
                    <section>
                        <header className="category-header" style={{ borderColor: '#8b5cf6' }}>
                            <h2 style={{ color: '#8b5cf6' }}><span>🚀</span> Motor de Campanhas (Leads)</h2>
                            <p>Textos para disparos em massa e primeira abordagem de novos leads.</p>
                        </header>

                        <TemplateEditor 
                            title="Campanha de Vendas (WhatsApp)"
                            subtitle="Script de impacto para campanhas enviadas via ADB."
                            icon="💬"
                            id="tpl_camp_wa"
                            fieldKey="TEMPLATE_WHATSAPP_CAMPANHA"
                            value={settings?.TEMPLATE_WHATSAPP_CAMPANHA as string}
                            tags={['{nome}', '{remetente}', '{link}']}
                            onSave={salvarUnico}
                            onChange={handleChange}
                        />

                        <TemplateEditor 
                            title="Disparo Masivo (SMS)"
                            subtitle="Mensagem curta e objetiva para o robô de SMS."
                            icon="📨"
                            id="tpl_sms"
                            fieldKey="TEMPLATE_SMS_CAMPANHA"
                            value={settings?.TEMPLATE_SMS_CAMPANHA as string}
                            tags={['{nome}', '{remetente}']}
                            onSave={salvarUnico}
                            onChange={handleChange}
                        />

                        <TemplateEditor 
                            title="Nutrição de Leads (E-Mail)"
                            subtitle="Script para contato oficial por e-mail em campanhas de prospecção."
                            icon="📧"
                            id="tpl_camp_email"
                            fieldKey="TEMPLATE_EMAIL_CAMPANHA_CORPO"
                            value={settings?.TEMPLATE_EMAIL_CAMPANHA_CORPO as string}
                            tags={['{nome}', '{remetente}']}
                            onSave={salvarUnico}
                            onChange={handleChange}
                            isEmail
                            subject={settings?.TEMPLATE_EMAIL_CAMPANHA_ASSUNTO as string}
                            onSubjectChange={(v: any) => handleChange('TEMPLATE_EMAIL_CAMPANHA_ASSUNTO', v)}
                        />
                    </section>
                </div>
            </div>
        </div>
    )
}

function TemplateEditor({ title, subtitle, icon, id, fieldKey, value, tags, onSave, onChange, isEmail, subject, onSubjectChange }: any) {
    const fileRef = useRef<HTMLInputElement>(null)
    const [subindo, setSubindo] = useState(false)

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return
        setSubindo(true)
        const tid = toast.loading('Subindo mídia...')
        try {
            const ext = file.name.split('.').pop()
            const name = `${Math.random().toString(36).substring(2)}-${Date.now()}.${ext}`
            const path = `templates/${name}`

            const { error: upErr } = await supabase.storage.from('crm-media').upload(path, file)
            if (upErr) throw upErr

            const { data: { publicUrl } } = supabase.storage.from('crm-media').getPublicUrl(path)

            let tag = ''
            if (file.type === 'application/pdf') tag = `\n[pdf](${publicUrl})\n`
            else if (file.type.startsWith('video')) tag = `\n[video](${publicUrl})\n`
            else tag = `\n![imagem](${publicUrl})\n`

            onChange(fieldKey, (value || '') + tag)
            toast.success('Mídia vinculada!', { id: tid })
        } catch (err) {
            toast.error('Erro no upload. Verifique o servidor.', { id: tid })
        } finally {
            setSubindo(false)
        }
    }

    return (
        <article className="template-card">
            <div className="template-card-header">
                <div>
                    <h3 style={{ margin: 0, fontWeight: 900, fontSize: '1.25rem' }}>{icon} {title}</h3>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#535F70' }}>{subtitle}</p>
                </div>
                <button onClick={() => onSave(fieldKey, value)} className="m3-btn m3-btn-outline">
                    💾 Salvar Este
                </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '2rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    
                    {isEmail && (
                        <div className="m3-field">
                            <label className="m3-label">Assunto do E-mail</label>
                            <input 
                                className="m3-input" 
                                value={subject || ''} 
                                onChange={e => onSubjectChange(e.target.value)}
                                placeholder="Digite o assunto relevante..."
                            />
                        </div>
                    )}

                    <div className="variable-chip-container">
                        {tags.map((tag: string) => (
                             <button 
                                key={tag} 
                                onClick={() => {
                                    const tx = document.getElementById(id) as HTMLTextAreaElement
                                    if (!tx) return
                                    const start = tx.selectionStart
                                    const end = tx.selectionEnd
                                    const val = tx.value
                                    onChange(fieldKey, val.substring(0, start) + tag + val.substring(end))
                                    setTimeout(() => { tx.focus(); tx.setSelectionRange(start + tag.length, start + tag.length); }, 0)
                                }}
                                className="variable-chip"
                            >
                                {tag}
                            </button>
                        ))}
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <div className="m3-toolbar">
                             <ToolbarButton icon="B" onClick={() => {
                                const tx = document.getElementById(id) as HTMLTextAreaElement
                                if (!tx) return
                                const s = tx.selectionStart; const e = tx.selectionEnd
                                const val = tx.value
                                onChange(fieldKey, val.substring(0, s) + '*' + val.substring(s, e) + '*' + val.substring(e))
                             }} />
                             <ToolbarButton icon="I" onClick={() => {
                                const tx = document.getElementById(id) as HTMLTextAreaElement
                                if (!tx) return
                                const s = tx.selectionStart; const e = tx.selectionEnd
                                const val = tx.value
                                onChange(fieldKey, val.substring(0, s) + '_' + val.substring(s, e) + '_' + val.substring(e))
                             }} />
                             <ToolbarButton icon="📎" onClick={() => fileRef.current?.click()} loading={subindo} />
                        </div>
                        <textarea 
                            id={id}
                            className="m3-template-editor"
                            value={value || ''}
                            onChange={e => onChange(fieldKey, e.target.value)}
                            placeholder="Escreva sua mensagem aqui..."
                        />
                        <input type="file" ref={fileRef} style={{ display: 'none' }} onChange={handleUpload} />
                    </div>
                </div>

                <div className="preview-container">
                    <div style={{ fontSize: '0.75rem', fontWeight: 900, color: '#535F70', textAlign: 'right', textTransform: 'uppercase' }}>Preview em Tempo Real</div>
                    <div className="chat-preview-window">
                        <div className="m3-chat-bubble">
                             <PreviewContent text={value} subject={subject} />
                             <div className="bubble-meta">
                                 {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ✓✓
                             </div>
                        </div>
                    </div>
                </div>
            </div>
        </article>
    )
}

function PreviewContent({ text, subject }: any) {
    if (!text) return <em style={{ color: '#999' }}>Escreva o template para ver o preview...</em>
    
    let processed = text
        .replace(/{proprietario}|{nome}/g, 'João da Silva')
        .replace(/{referencia}/g, 'REF-8821')
        .replace(/{remetente}/g, 'Equipe de Vendas')
        .replace(/{link}/g, 'https://imovel.link/v123')

    // Mídias
    const mediaRegex = /(!\[.*?\]\((https?:\/\/.*?)\)|\[(video|pdf)\]\((https?:\/\/.*?)\))/g
    const contents: any[] = []
    let lastIndex = 0
    let match

    while ((match = mediaRegex.exec(processed)) !== null) {
        if (match.index > lastIndex) contents.push(processed.substring(lastIndex, match.index))
        const url = match[2] || match[4]
        const type = match[3] || 'image'

        if (type === 'image') contents.push(<img src={url} style={{ width: '100%', borderRadius: '8px', margin: '8px 0' }} />)
        else if (type === 'video') contents.push(<div style={{ background: '#000', color: 'white', padding: '1.5rem', textAlign: 'center', borderRadius: '8px', margin: '8px 0', fontSize: '0.8rem' }}>🎥 Vídeo Anexo</div>)
        else contents.push(<div style={{ background: '#f0f2f5', border: '1px solid #ddd', padding: '8px', borderRadius: '8px', margin: '8px 0', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem' }}>📄 PDF: Arquivo Anexo</div>)
        
        lastIndex = mediaRegex.lastIndex
    }
    if (lastIndex < processed.length) contents.push(processed.substring(lastIndex))

    return (
        <div>
            {subject && <div style={{ fontWeight: 900, borderBottom: '1px solid #f0f2f5', marginBottom: '8px', paddingBottom: '4px', fontSize: '0.85rem' }}>E-mail: {subject}</div>}
            {contents.map((c, i) => <span key={i}>{c}</span>)}
        </div>
    )
}

function ToolbarButton({ icon, onClick, loading }: any) {
    return (
        <button onClick={onClick} className="toolbar-btn" disabled={loading}>
            {loading ? <span className="spin">⌛</span> : icon}
        </button>
    )
}
