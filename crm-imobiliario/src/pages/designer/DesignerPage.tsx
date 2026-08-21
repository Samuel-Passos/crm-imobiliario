import React, { useState, useRef, useEffect } from 'react'
import toast from 'react-hot-toast'
import { supabase } from '../../lib/supabase'
import './DesignerPage.css'

const ROBO_URL = 'http://localhost:8766'

interface Message {
    role: 'user' | 'model'
    text: string
    timestamp: number
    image?: string
    generated_image?: string // Nova propriedade para imagem gerada pela IA
}

interface Agente {
    id: string
    nome: string
    icone: string
    descricao: string
}

export function DesignerPage() {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [selectedImage, setSelectedImage] = useState<string | null>(null)
    const [history, setHistory] = useState<{title: string, id: number}[]>([])
    
    // --- Agentes ---
    const [agentes, setAgentes] = useState<Agente[]>([])
    const [agenteAtivo, setAgenteAtivo] = useState<Agente | null>(null)
    const [buscandoAgentes, setBuscandoAgentes] = useState(true)
    
    // --- Modal Editor ---
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [editData, setEditData] = useState<any>({ nome: '', icone: '✨', descricao: '', instrucao_sistema: '' })
    const [isSavingAgent, setIsSavingAgent] = useState(false)
    const [activeModalTab, setActiveModalTab] = useState<'brain' | 'files'>('brain')
    const [agentFiles, setAgentFiles] = useState<any[]>([])
    const [uploadingFile, setUploadingFile] = useState(false)
    const [selectedModel, setSelectedModel] = useState('gemini-flash-latest')

    const scrollRef = useRef<HTMLDivElement>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)
    const agentFileInputRef = useRef<HTMLInputElement>(null)

    useEffect(() => {
        carregarAgentes()
    }, [])

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [messages])

    async function carregarAgentes() {
        try {
            const { data, error } = await supabase
                .from('agentes_ia')
                .select('*')
                .order('criado_em', { ascending: true })
            
            if (error) throw error
            setAgentes(data || [])
            
            // Define o primeiro agente como padrão se nenhum estiver ativo
            if (data && data.length > 0 && !agenteAtivo) {
                setAgenteAtivo(data[0])
            }
        } catch (err) {
            console.error('Erro ao buscar agentes:', err)
        } finally {
            setBuscandoAgentes(false)
        }
    }

    const openEditor = (agente?: Agente) => {
        if (agente) {
            const fullAgent = agentes.find(a => a.id === agente.id) as any
            setEditData({ ...fullAgent })
            carregarArquivosAgente(agente.id)
        } else {
            setEditData({ 
                nome: '', 
                icone: '✨', 
                descricao: '', 
                instrucao_sistema: 'Você é um assistente criativo imobiliário...\n\nREGRAS:\n1. Se faltar dados (Preço, Área, etc), peça ao usuário.\n2. Peça de 1 a 3 fotos do imóvel para compor o post.' 
            })
            setAgentFiles([])
        }
        setActiveModalTab('brain')
        setIsModalOpen(true)
    }

    const carregarArquivosAgente = async (agenteId: string) => {
        try {
            const res = await fetch(`${ROBO_URL}/api/designer/agents/${agenteId}/files`)
            const data = await res.json()
            if (data.ok) setAgentFiles(data.arquivos)
        } catch (err) { console.error('Erro ao carregar arquivos:', err) }
    }

    const handleUploadArquivo = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!editData.id) { toast.error('Salve o agente antes de subir arquivos.'); return }
        const file = e.target.files?.[0]
        if (!file) return

        setUploadingFile(true)
        const formData = new FormData()
        formData.append('file', file)

        try {
            const res = await fetch(`${ROBO_URL}/api/designer/agents/${editData.id}/upload`, {
                method: 'POST',
                body: formData
            })
            const data = await res.json()
            if (data.ok) {
                toast.success('Arquivo arquivado na base de conhecimento!')
                carregarArquivosAgente(editData.id)
            } else {
                toast.error(data.mensagem)
            }
        } catch (err) { toast.error('Erro no upload.') }
        finally { setUploadingFile(false) }
    }

    const handleExcluirArquivo = async (fileId: string) => {
        if (!confirm('Excluir arquivo de referência?')) return
        try {
            const res = await fetch(`${ROBO_URL}/api/designer/agents/files/${fileId}`, { method: 'DELETE' })
            const data = await res.json()
            if (data.ok) {
                toast.success('Arquivo removido.')
                setAgentFiles(prev => prev.filter(f => f.id !== fileId))
            }
        } catch (err) { toast.error('Erro ao excluir.') }
    }

    const handleSaveAgent = async () => {
        if (!editData.nome || !editData.instrucao_sistema) {
            toast.error('Nome e Instrução são obrigatórios')
            return
        }

        setIsSavingAgent(true)
        try {
            const { data, error } = await supabase
                .from('agentes_ia')
                .upsert({
                    id: editData.id || undefined,
                    nome: editData.nome,
                    icone: editData.icone,
                    descricao: editData.descricao,
                    instrucao_sistema: editData.instrucao_sistema,
                    atualizado_em: new Date().toISOString()
                })
                .select()

            if (error) throw error
            
            toast.success('Agente salvo com sucesso!')
            if (!editData.id) {
                // Se era novo, mantém aberto para subir arquivos
                setEditData(data[0])
                carregarAgentes()
            } else {
                setIsModalOpen(false)
                carregarAgentes()
            }
            if (data && data[0]) setAgenteAtivo(data[0])
        } catch (err: any) {
            toast.error('Erro ao salvar agente: ' + err.message)
        } finally {
            setIsSavingAgent(false)
        }
    }

    const handleDeleteAgent = async (id: string) => {
        if (!confirm('Tem certeza que deseja excluir este agente?')) return

        try {
            const { error } = await supabase
                .from('agentes_ia')
                .delete()
                .eq('id', id)
            
            if (error) throw error
            
            toast.success('Agente excluído.')
            setAgentes(prev => prev.filter(a => a.id !== id))
            if (agenteAtivo?.id === id) setAgenteAtivo(agentes[0] || null)
        } catch (err: any) {
            toast.error('Erro ao excluir: ' + err.message)
        }
    }

    const handleSend = async (customPrompt?: string) => {
        const textToSend = customPrompt || input
        if (!textToSend.trim() && !selectedImage) return

        const userMsg: Message = {
            role: 'user',
            text: textToSend,
            timestamp: Date.now(),
            image: selectedImage || undefined
        }

        setMessages(prev => [...prev, userMsg])
        setInput('')
        setSelectedImage(null)
        setLoading(true)

        try {
            const res = await fetch(`${ROBO_URL}/api/designer/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: textToSend,
                    image: userMsg.image,
                    agente_id: agenteAtivo?.id,
                    model: selectedModel, // <-- Envia o modelo selecionado
                    history: messages.map(m => ({
                        role: m.role,
                        parts: [{ text: m.text }]
                    }))
                })
            })

            const data = await res.json()
            if (data.ok) {
                const aiMsg: Message = {
                    role: 'model',
                    text: data.resposta,
                    timestamp: Date.now(),
                    generated_image: data.image_url // Captura a URL da imagem gerada
                }
                setMessages(prev => [...prev, aiMsg])
            } else {
                toast.error(data.mensagem || 'Falha na resposta da IA')
            }
        } catch (error) {
            toast.error('Erro ao conectar ao motor criativo.')
        } finally {
            setLoading(false)
        }
    }

    const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            const reader = new FileReader()
            reader.onloadend = () => {
                setSelectedImage(reader.result as string)
            }
            reader.readAsDataURL(file)
        }
    }

    const presets = [
        { icon: '🎨', text: 'Crie uma copy e descrição para um post de cobertura luxuosa em SJC', prompt: 'Crie um post para uma cobertura de luxo em São José dos Campos.' },
        { icon: '📸', text: 'Sugira 3 variações de artes publicitárias para o Facebook Ads', prompt: 'Sugira 3 conceitos visuais para Facebook Ads imobiliário.' },
        { icon: '🔍', text: 'Analise o design desta peça (faça upload da imagem)', prompt: 'Analise o design desta imagem publicitária que acabei de subir.' }
    ]

    return (
        <div className="designer-container">
            {/* Sidebar Histórico e Agentes */}
            <aside className="designer-history">
                <button className="new-chat-btn" onClick={() => setMessages([])}>
                    <span>+</span> Novo Chat
                </button>
                
                <div style={{ fontSize: '0.7rem', fontWeight: 800, color: '#535f70', marginBottom: '0.75rem', marginLeft: '8px', letterSpacing: '0.05em' }}>MEUS AGENTES</div>
                <div className="agentes-list" style={{ marginBottom: '2rem' }}>
                    {buscandoAgentes ? (
                        <div style={{ padding: '8px', fontSize: '0.8rem', color: '#8e918f' }}>Carregando agentes...</div>
                    ) : agentes.map(a => (
                        <div 
                            key={a.id} 
                            className={`history-item ${agenteAtivo?.id === a.id ? 'active' : ''}`}
                            onClick={() => { setAgenteAtivo(a); setMessages([]); }}
                            title={a.descricao}
                            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                        >
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <span style={{ marginRight: '10px' }}>{a.icone}</span>
                                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '140px' }}>{a.nome}</span>
                            </div>
                            <div className="history-item-actions">
                                <button className="action-icon-btn" onClick={(e) => { e.stopPropagation(); openEditor(a); }}>✏️</button>
                                <button className="action-icon-btn" onClick={(e) => { e.stopPropagation(); handleDeleteAgent(a.id); }}>🗑️</button>
                            </div>
                        </div>
                    ))}
                    <button 
                        className="history-item" 
                        style={{ border: '1px dashed #c4c7c5', marginTop: '8px', textAlign: 'center', color: '#0b57d0', fontWeight: 600, width: '100%' }}
                        onClick={() => openEditor()}
                    >
                        + Criar Novo Agente
                    </button>
                </div>

                <div style={{ fontSize: '0.7rem', fontWeight: 800, color: '#535f70', marginBottom: '0.75rem', marginLeft: '8px', letterSpacing: '0.05em' }}>CONVERSAS RECENTES</div>
                <div className="history-list">
                    {history.length === 0 ? (
                        <div style={{ padding: '8px', fontSize: '0.8rem', color: '#8e918f' }}>Nenhum histórico recente</div>
                    ) : (
                        history.map(h => (
                            <div key={h.id} className="history-item">{h.title}</div>
                        ))
                    )}
                </div>
            </aside>

            {/* Main Area */}
            <main className="designer-main">
                {messages.length === 0 ? (
                    <div className="designer-empty">
                        <div className="empty-title">Olá, Samuel</div>
                        <div className="empty-subtitle">
                            Eu sou seu <strong>{agenteAtivo?.nome || 'Assistente Criativo'}</strong>.<br />
                            Como podemos brilhar hoje?
                        </div>
                        
                        <div className="preset-grid">
                            {presets.map((p, idx) => (
                                <div key={idx} className="preset-card" onClick={() => handleSend(p.prompt)}>
                                    <span className="preset-icon">{p.icon}</span>
                                    <span className="preset-text">{p.text}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="chat-scroller" ref={scrollRef}>
                        {messages.map((m, idx) => (
                            <div key={idx} className="chat-message">
                                <div className={`message-avatar ${m.role === 'user' ? 'avatar-user' : 'avatar-ai'}`}>
                                    {m.role === 'user' ? 'S' : agenteAtivo?.icone || '✨'}
                                </div>
                                <div className="message-content">
                                    {m.image && <img src={m.image} alt="Upload" className="preview-img" style={{ marginBottom: '1rem', maxWidth: '300px' }} />}
                                    <div style={{ whiteSpace: 'pre-wrap' }}>{m.text}</div>
                                    {m.generated_image && (
                                        <div className="generated-image-container" style={{ marginTop: '1.5rem' }}>
                                            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#0b57d0', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                ✨ IMAGEM GERADA COM SUCESSO
                                            </div>
                                            <img 
                                                src={`${ROBO_URL}${m.generated_image}`} 
                                                alt="IA Generated" 
                                                style={{ 
                                                    width: '100%', 
                                                    maxWidth: '800px', 
                                                    borderRadius: '24px', 
                                                    boxShadow: '0 12px 40px rgba(0,0,0,0.15)', 
                                                    border: '1px solid #e1e3e1',
                                                    display: 'block'
                                                }} 
                                            />
                                            <div style={{ marginTop: '8px' }}>
                                                <a 
                                                    href={`${ROBO_URL}${m.generated_image}`} 
                                                    download={`post_${Date.now()}.jpg`}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="btn-secondary"
                                                    style={{ display: 'inline-block', textDecoration: 'none', fontSize: '0.8rem' }}
                                                >
                                                    📥 Baixar Imagem PNG/JPEG
                                                </a>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="chat-message">
                                <div className="message-avatar avatar-ai">{agenteAtivo?.icone || '✨'}</div>
                                <div className="message-content">
                                    <div className="loading-dots">Gerando resposta...</div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Input Area */}
                <div className="designer-input-wrapper">
                    {selectedImage && (
                        <div className="upload-preview">
                            <img src={selectedImage} alt="Preview" className="preview-img" />
                            <div style={{ flex: 1, fontSize: '0.8rem' }}>Imagem carregada para análise</div>
                            <button onClick={() => setSelectedImage(null)} style={{ border: 'none', background: 'transparent', cursor: 'pointer' }}>✕</button>
                        </div>
                    )}
                    
                    <div className="model-selector-wrapper">
                        <select 
                            className="model-dropdown-m3"
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                        >
                            <optgroup label="✨ Inteligência Superior (Gemini 2.x)">
                                <option value="gemini-2.5-flash">Gemini 2.5 Flash (Preview)</option>
                                <option value="gemini-2.5-pro">Gemini 2.5 Pro (Preview)</option>
                                <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                                <option value="gemini-2.0-flash-lite">Gemini 2.0 Flash Lite</option>
                            </optgroup>
                            <optgroup label="⚡ Equilíbrio e Velocidade (Gemini 1.5)">
                                <option value="gemini-1.5-flash">Gemini 1.5 Flash (Recomendado)</option>
                                <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                                <option value="gemini-flash-latest">Gemini Flash Latest</option>
                            </optgroup>
                            <optgroup label="🧪 Laboratório / Experimental">
                                <option value="gemini-3.1-pro-preview">Gemini 3.1 Pro Preview</option>
                                <option value="nano-banana-pro-preview">Nano Banana Pro</option>
                                <option value="deep-research-pro-preview-12-2025">Deep Research</option>
                                <option value="gemma-3-27b-it">Gemma 3 (27B)</option>
                            </optgroup>
                        </select>
                    </div>

                    <div className="designer-input-box">
                        <textarea 
                            className="designer-textarea"
                            placeholder={`Falar com ${agenteAtivo?.nome}...`}
                            rows={1}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault()
                                    handleSend()
                                }
                            }}
                        />
                        <div className="input-actions">
                            <input 
                                type="file" 
                                ref={fileInputRef} 
                                style={{ display: 'none' }} 
                                accept="image/*" 
                                onChange={handleImageUpload} 
                            />
                            <button className="action-btn" onClick={() => fileInputRef.current?.click()}>🖼️</button>
                            <button 
                                className="action-btn send-btn" 
                                disabled={loading || (!input.trim() && !selectedImage)}
                                onClick={() => handleSend()}
                            >
                                🚀
                            </button>
                        </div>
                    </div>
                    <div style={{ textAlign: 'center', fontSize: '0.7rem', color: '#8e918f', marginTop: '12px' }}>
                        Usando motor <strong>{selectedModel}</strong>. {agenteAtivo?.nome} está ativo.
                    </div>
                </div>
            </main>

            {/* Modal de Editor de Agente */}
            {isModalOpen && (
                <div className="modal-overlay">
                    <div className="agent-modal">
                        <div className="modal-header">
                            <div className="modal-title">
                                {editData.id ? 'Editar Agente' : 'Novo Agente'}
                            </div>
                            <button className="action-icon-btn" onClick={() => setIsModalOpen(false)}>✕</button>
                        </div>

                        <div className="m3-tabs" style={{ borderBottom: '1px solid #e1e3e1', marginBottom: '1rem' }}>
                            <button className={`m3-tab-btn ${activeModalTab === 'brain' ? 'active' : ''}`} onClick={() => setActiveModalTab('brain')}>🧠 Cérebro</button>
                            <button className={`m3-tab-btn ${activeModalTab === 'files' ? 'active' : ''}`} onClick={() => setActiveModalTab('files')}>📂 Conhecimento</button>
                        </div>
                        
                        {activeModalTab === 'brain' ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: '1rem' }}>
                                    <div className="modal-input-group">
                                        <label>Ícone</label>
                                        <input 
                                            className="modal-input" 
                                            style={{ textAlign: 'center', fontSize: '1.5rem' }} 
                                            value={editData.icone} 
                                            onChange={e => setEditData({...editData, icone: e.target.value})}
                                        />
                                    </div>
                                    <div className="modal-input-group">
                                        <label>Nome do Agente</label>
                                        <input 
                                            className="modal-input" 
                                            placeholder="Ex: Redator Publicitário"
                                            value={editData.nome} 
                                            onChange={e => setEditData({...editData, nome: e.target.value})}
                                        />
                                    </div>
                                </div>

                                <div className="modal-input-group">
                                    <label>Descrição Curta</label>
                                    <input 
                                        className="modal-input" 
                                        placeholder="Para que serve este agente?"
                                        value={editData.descricao} 
                                        onChange={e => setEditData({...editData, descricao: e.target.value})}
                                    />
                                </div>

                                <div className="modal-input-group">
                                    <label>Instrução de Sistema (Persona)</label>
                                    <textarea 
                                        className="modal-input modal-textarea" 
                                        placeholder="Regras, tom de voz e comportamentos..."
                                        value={editData.instrucao_sistema} 
                                        onChange={e => setEditData({...editData, instrucao_sistema: e.target.value})}
                                    />
                                </div>
                            </div>
                        ) : (
                            <div className="knowledge-base-section">
                                <div style={{ marginBottom: '1rem' }}>
                                    <div style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '4px' }}>Base de Conhecimento</div>
                                    <div style={{ fontSize: '0.8rem', color: '#535f70' }}>Arquivos que este agente usará como referência constante.</div>
                                </div>

                                <div className="files-list" style={{ minHeight: '150px', background: '#f8fafd', borderRadius: '12px', padding: '1rem' }}>
                                    {agentFiles.length === 0 ? (
                                        <div style={{ textAlign: 'center', padding: '2rem', color: '#8e918f', fontSize: '0.85rem' }}>
                                            Nenhum arquivo de referência anexado.
                                        </div>
                                    ) : (
                                        agentFiles.map(f => {
                                            const isImage = f.tipo_mime?.startsWith('image/');
                                            return (
                                                <div key={f.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px', borderBottom: '1px solid #e1e3e1' }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
                                                        <span>{isImage ? '🖼️' : '📄'}</span>
                                                        <span style={{ fontWeight: 600 }}>{f.nome_arquivo}</span>
                                                        <span style={{ fontSize: '0.7rem', color: '#8e918f' }}>({(f.tamanho_bytes/1024).toFixed(1)} KB)</span>
                                                    </div>
                                                    <button className="action-icon-btn" onClick={() => handleExcluirArquivo(f.id)}>🗑️</button>
                                                </div>
                                            );
                                        })
                                    )}
                                </div>

                                <div style={{ marginTop: '1.5rem' }}>
                                    <input 
                                        type="file" 
                                        ref={agentFileInputRef} 
                                        style={{ display: 'none' }} 
                                        onChange={handleUploadArquivo} 
                                        accept=".pdf,.txt,.md,.json,.jpg,.jpeg,.png,.webp" 
                                    />
                                    <button 
                                        className="btn-secondary" 
                                        style={{ width: '100%', borderStyle: 'dashed' }}
                                        onClick={() => agentFileInputRef.current?.click()}
                                        disabled={uploadingFile || !editData.id}
                                    >
                                        {uploadingFile ? '⏳ Subindo...' : '+ Anexar Referência (PDF, Imagem ou Texto)'}
                                    </button>
                                    {!editData.id && <div style={{ fontSize: '0.7rem', color: '#d93025', marginTop: '4px' }}>* Salve o agente primeiro para habilitar o upload.</div>}
                                </div>
                            </div>
                        )}

                        <div className="modal-actions">
                            <button className="btn-secondary" onClick={() => setIsModalOpen(false)} disabled={isSavingAgent}>Cancelar</button>
                            <button className="btn-primary" onClick={handleSaveAgent} disabled={isSavingAgent}>
                                {isSavingAgent ? 'Salvando...' : 'Salvar TUDO'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}


