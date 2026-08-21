import React, { useState, useCallback, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import * as XLSX from 'xlsx'
import toast from 'react-hot-toast'

interface ColumnMapping {
    source: string
    target: string
}

const TARGET_FIELDS = [
    { value: 'nome_completo', label: 'Nome Completo' },
    { value: 'telefone', label: 'Telefone' },
    { value: 'whatsapp', label: 'WhatsApp' },
    { value: 'email', label: 'E-mail' },
    { value: 'cidade', label: 'Cidade' },
    { value: 'logradouro', label: 'Endereço/Rua' },
    { value: 'notas', label: 'Notas/Observações' },
]

export function ImportPage() {
    const [file, setFile] = useState<File | null>(null)
    const [step, setStep] = useState(1)
    const [headers, setHeaders] = useState<string[]>([])
    const [rawData, setRawData] = useState<any[]>([])
    const [mapping, setMapping] = useState<ColumnMapping[]>([])
    const [campanhas, setCampanhas] = useState<any[]>([])
    const [selectedCampaign, setSelectedCampaign] = useState<string>('')
    const [isImporting, setIsImporting] = useState(false)
    const [progress, setProgress] = useState(0)

    useEffect(() => {
        carregarCampanhas()
    }, [])

    async function carregarCampanhas() {
        const { data } = await supabase.from('campanhas_ligacao').select('*').order('nome')
        if (data) setCampanhas(data)
    }

    const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const f = e.target.files?.[0]
        if (f) {
            setFile(f)
            processFile(f)
        }
    }

    const processFile = (f: File) => {
        const reader = new FileReader()
        reader.onload = (evt) => {
            const bstr = evt.target?.result
            const wb = XLSX.read(bstr, { type: 'binary' })
            const wsname = wb.SheetNames[0]
            const ws = wb.Sheets[wsname]
            const data = XLSX.utils.sheet_to_json(ws, { header: 1 }) as any[][]
            
            if (data.length > 0) {
                const headerRow = data[0].map(h => String(h || ''))
                setHeaders(headerRow)
                // Convert to array of objects for easier mapping later
                const rows = XLSX.utils.sheet_to_json(ws)
                setRawData(rows)
                
                // Auto-mapping sugerido
                const initialMapping: ColumnMapping[] = []
                headerRow.forEach(h => {
                    const low = h.toLowerCase()
                    if (low.includes('nome')) initialMapping.push({ source: h, target: 'nome_completo' })
                    else if (low.includes('tel') || low.includes('cel')) initialMapping.push({ source: h, target: 'telefone' })
                    else if (low.includes('whats')) initialMapping.push({ source: h, target: 'whatsapp' })
                    else if (low.includes('mail')) initialMapping.push({ source: h, target: 'email' })
                })
                setMapping(initialMapping)
                setStep(2)
            }
        }
        reader.readAsBinaryString(f)
    }

    const handleMappingChange = (source: string, target: string) => {
        setMapping(prev => {
            const filtered = prev.filter(m => m.source !== source)
            if (target) {
                return [...filtered, { source, target }]
            }
            return filtered
        })
    }

    const runImport = async () => {
        if (!mapping.length) return toast.error('Mapeie pelo menos um campo.')
        setIsImporting(true)
        setProgress(0)

        const total = rawData.length
        let success = 0
        let errors = 0

        for (let i = 0; i < total; i++) {
            const row = rawData[i]
            const payload: any = {
                tipo_contato: 'proprietario', // Default
            }

            mapping.forEach(m => {
                payload[m.target] = row[m.source]
            })

            // 1. Salvar em Contatos
            const { data: contato, error: errC } = await supabase
                .from('contatos')
                .upsert(payload, { onConflict: 'telefone' }) // Simplificação: assume telefone como chave parcial ou apenas evita duplicados
                .select()
                .single()

            if (errC) {
                errors++
            } else if (selectedCampaign && contato) {
                // 2. Se tiver campanha, vincular
                await supabase.from('leads_campanha').insert({
                    campanha_id: parseInt(selectedCampaign),
                    contato_id: contato.id,
                    nome: contato.nome_completo,
                    telefone: contato.telefone,
                    status: 'Pendente'
                })
                success++
            } else {
                success++
            }

            setProgress(Math.round(((i + 1) / total) * 100))
        }

        setIsImporting(false)
        setStep(3)
        toast.success(`Importação concluída: ${success} sucessos, ${errors} erros.`)
    }

    return (
        <div style={{ maxWidth: 800, margin: '2rem auto', padding: '0 1.5rem' }}>
            <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)' }}>Importar Leads</h1>
                <p style={{ color: 'var(--text-muted)' }}>Suba planilhas Excel ou CSV e organize sua prospecção</p>
            </div>

            {/* Stepper */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
                {[1, 2, 3].map(s => (
                    <div key={s} style={{ 
                        flex: 1, height: 4, borderRadius: 2, 
                        background: step >= s ? 'var(--brand-500)' : 'var(--border)',
                        transition: 'background 0.3s ease'
                    }} />
                ))}
            </div>

            <div className="card" style={{ padding: '2rem' }}>
                {step === 1 && (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ 
                            border: '2px dashed var(--border)', borderRadius: '16px', 
                            padding: '3rem 1rem', cursor: 'pointer', position: 'relative',
                            transition: 'border-color 0.2s',
                        }}
                        onDragOver={e => e.preventDefault()}
                        onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--brand-500)'}
                        onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
                        >
                            <input 
                                type="file" 
                                accept=".xlsx, .xls, .csv" 
                                onChange={onFileChange}
                                style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }}
                            />
                            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📈</div>
                            <h3 style={{ fontWeight: 700, marginBottom: '0.5rem' }}>Escolha sua planilha</h3>
                            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Arraste o arquivo ou clique para selecionar (.xlsx ou .csv)</p>
                        </div>
                    </div>
                )}

                {step === 2 && (
                    <div style={{ animation: 'fadeSlideUp 0.4s ease' }}>
                        <h3 style={{ fontWeight: 700, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            ⚙️ Mapeamento de Colunas
                        </h3>
                        
                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                                Vincular a uma Campanha (Opcional)
                            </label>
                            <select 
                                className="form-select" 
                                value={selectedCampaign} 
                                onChange={e => setSelectedCampaign(e.target.value)}
                            >
                                <option value="">Não vincular a campanha agora</option>
                                {campanhas.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}
                            </select>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {headers.map(h => {
                                const m = mapping.find(item => item.source === h)
                                return (
                                    <div key={h} style={{ 
                                        display: 'flex', alignItems: 'center', gap: '1rem', 
                                        padding: '0.75rem', background: 'var(--bg-app)', borderRadius: '12px',
                                        border: '1px solid var(--border)'
                                    }}>
                                        <div style={{ flex: 1, fontSize: '0.85rem', fontWeight: 600 }}>{h}</div>
                                        <div style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>→</div>
                                        <div style={{ flex: 1.2 }}>
                                            <select 
                                                className="form-select"
                                                value={m?.target || ''}
                                                onChange={e => handleMappingChange(h, e.target.value)}
                                                style={{ padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
                                            >
                                                <option value="">Ignorar coluna</option>
                                                {TARGET_FIELDS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                                            </select>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>

                        <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem' }}>
                            <button className="btn" onClick={() => setStep(1)} style={{ flex: 1 }}>Voltar</button>
                            <button className="btn btn-primary" onClick={runImport} disabled={isImporting} style={{ flex: 2 }}>
                                {isImporting ? `Importando... ${progress}%` : `Importar ${rawData.length} Leads`}
                            </button>
                        </div>
                    </div>
                )}

                {step === 3 && (
                    <div style={{ textAlign: 'center', animation: 'fadeIn 0.5s ease' }}>
                        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎉</div>
                        <h2 style={{ fontWeight: 800, marginBottom: '0.5rem' }}>Sucesso!</h2>
                        <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
                            Seus contatos foram processados e já estão disponíveis na lista fria ou na campanha selecionada.
                        </p>
                        <button className="btn btn-primary" onClick={() => window.location.href = '/contatos'}>
                            Ver Lista de Contatos
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
