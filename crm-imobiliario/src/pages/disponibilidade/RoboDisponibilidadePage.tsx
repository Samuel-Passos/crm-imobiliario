import { useState, useEffect, useRef, useCallback } from 'react'
import * as XLSX from 'xlsx'
import { supabase } from '../../lib/supabase'
import toast from 'react-hot-toast'

// ── Tipos ──────────────────────────────────────────────────────────────────
interface Imovel {
    referencia: string
    proprietario: string | null
    telefone: string | null
    preco: string | null
    status: string | null
    ultimo_contato: string | null
    resposta: 'SIM' | 'NÃO' | null
    data_resposta: string | null
    proximo_contato: string | null
}

// Mapeamento das colunas da planilha para as colunas do banco
const MAPEAMENTO: Record<string, keyof Imovel> = {
    'Referencia':              'referencia',
    'Proprietário':            'proprietario',
    'Celular do Proprietário': 'telefone',
    'Preço':                   'preco',
    'Status':                  'status',  // opcional — pode estar ausente na planilha
}
// Apenas estas colunas são exigidas na importação; as demais são opcionais
const COLUNAS_OBRIGATORIAS = ['Referencia', 'Proprietário', 'Celular do Proprietário', 'Preço']

// ── Utils ──────────────────────────────────────────────────────────────────
function formatarData(iso: string | null) {
    if (!iso) return '—'
    const d = new Date(iso)
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatarDataHora(iso: string | null) {
    if (!iso) return '—'
    const d = new Date(iso)
    return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// ── Componente Principal ───────────────────────────────────────────────────
export function RoboDisponibilidadePage() {
    const [imoveis, setImoveis] = useState<Imovel[]>([])
    const [loading, setLoading] = useState(true)
    const [busca, setBusca] = useState('')
    const [filtroResposta, setFiltroResposta] = useState<'todos' | 'SIM' | 'NÃO' | 'pendente'>('todos')
    const [importing, setImporting] = useState(false)
    const [importResult, setImportResult] = useState<{ inseridos: number; atualizados: number; erros: number } | null>(null)
    const [dragOver, setDragOver] = useState(false)
    const [disparando, setDisparando] = useState(false)
    const [motorEnvio, setMotorEnvio] = useState<'EVOLUTION' | 'ADB' | 'SMS'>('ADB')
    const fileRef = useRef<HTMLInputElement>(null)



    // ── Status do servidor (:8766) — polling a cada 8s ───────────────────
    const ROBO_URL = 'http://localhost:8766'
    const [serverOnline, setServerOnline] = useState<boolean | null>(null)
    const [roboExecutando, setRoboExecutando] = useState(false)

    useEffect(() => {
        verificarStatus()
        const intervalo = setInterval(verificarStatus, 8000)
        return () => clearInterval(intervalo)
    }, [])

    async function verificarStatus() {
        try {
            const res = await fetch(`${ROBO_URL}/status`, { signal: AbortSignal.timeout(3000) })
            if (res.ok) {
                const data = await res.json()
                setServerOnline(true)
                setRoboExecutando(data.executando ?? false)
                return
            }
        } catch { /* timeout ou offline */ }
        setServerOnline(false)
        setRoboExecutando(false)
    }

    async function iniciarDisparo() {
        if (!serverOnline) {
            toast.error('O servidor está offline. Execute ./start_robo.sh primeiro.')
            return
        }
        setDisparando(true)
        const promessa = fetch(`${ROBO_URL}/disparo`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ motor: motorEnvio })
        })
            .then(res => {
                if (!res.ok) throw new Error('Falha ao conectar com o robô')
                return res.json()
            })
            .finally(() => verificarStatus())

        toast.promise(promessa, {
            loading: 'Iniciando robô...',
            success: 'Disparo iniciado! 🚀 Verifique o terminal para acompanhar os envios.',
            error: 'Erro ao iniciar. O servidor está ligado? (./start_robo.sh)'
        })
    }

    async function pararDisparo() {
        try {
            const res = await fetch(`${ROBO_URL}/parar`, { method: 'POST' })
            if (res.ok) {
                toast.success('🛑 Sinal de parada enviado! O robô vai parar no próximo envio.')
                setDisparando(false)
                verificarStatus()
            } else {
                toast.error('Erro ao tentar parar o robô.')
            }
        } catch {
            toast.error('Erro de conexão ao tentar parar o robô.')
        }
    }

    useEffect(() => { carregarImoveis() }, [])

    async function carregarImoveis() {
        setLoading(true)
        const { data, error } = await supabase
            .from('atualizacao_disponibilidade')
            .select('*')
            .order('referencia', { ascending: true })
        if (!error && data) setImoveis(data)
        setLoading(false)
    }

    // ── PASSO 2: Importar Planilha ─────────────────────────────────────────
    const processarArquivo = useCallback(async (file: File) => {
        if (!file.name.match(/\.xlsx?$/i)) {
            toast.error('Use um arquivo .xlsx ou .xls')
            return
        }

        setImporting(true)
        setImportResult(null)

        try {
            // Ler o arquivo como ArrayBuffer
            const buffer = await file.arrayBuffer()
            const wb = XLSX.read(buffer, { type: 'array' })
            const ws = wb.Sheets[wb.SheetNames[0]]
            const rows: Record<string, string>[] = XLSX.utils.sheet_to_json(ws, { defval: '' })

            if (rows.length === 0) {
                toast.error('Planilha vazia ou sem dados reconhecíveis.')
                return
            }

            // Verificar colunas obrigatórias
            const primLinha = rows[0]
            const faltando = COLUNAS_OBRIGATORIAS.filter(c => !(c in primLinha))
            if (faltando.length > 0) {
                toast.error(`Colunas ausentes na planilha:\n${faltando.join(', ')}`)
                return
            }

            // ── Deletar lista anterior completamente ─────────────────────────
            // Deleta todos os registros onde referencia não é nulo
            const { error: deleteError } = await supabase
                .from('atualizacao_disponibilidade')
                .delete()
                .not('referencia', 'is', null)
                
            if (deleteError) {
                toast.error('Erro ao limpar a lista anterior do banco.')
                console.error(deleteError)
                setImporting(false)
                return
            }

            // Montar payloads
            const payloads: Partial<Imovel>[] = []

            for (const row of rows) {
                const ref = String(row['Referencia'] || '').trim()
                if (!ref) continue // pula linhas sem referência

                const payload: Partial<Imovel> = {}

                // Mapeamento das colunas da planilha
                for (const [colPlanilha, colBanco] of Object.entries(MAPEAMENTO)) {
                    const val = String(row[colPlanilha] || '').trim()
                    ;(payload as any)[colBanco] = val || null
                }

                payloads.push(payload)
            }

            // Inserir em lotes de 100
            let inseridos = 0, erros = 0
            const LOTE = 100

            for (let i = 0; i < payloads.length; i += LOTE) {
                const lote = payloads.slice(i, i + LOTE)
                // Agora usamos insert ou upsert (upsert é seguro em caso de duplicatas na própria planilha)
                const { error } = await supabase
                    .from('atualizacao_disponibilidade')
                    .upsert(lote, { onConflict: 'referencia' })

                if (error) {
                    erros += lote.length
                    console.error('Erro de inserção:', error)
                } else {
                    inseridos += lote.length
                }
            }

            setImportResult({ inseridos, atualizados: 0, erros })
            if (erros === 0) toast.success(`Importação concluída! ✅`)
            else toast(`Importação com ${erros} erro(s).`)
            await carregarImoveis()

        } catch (e: any) {
            console.error(e)
            toast.error('Erro ao processar o arquivo.')
        } finally {
            setImporting(false)
            if (fileRef.current) fileRef.current.value = ''
        }
    }, [])

    function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0]
        if (file) processarArquivo(file)
    }

    function handleDrop(e: React.DragEvent) {
        e.preventDefault()
        setDragOver(false)
        const file = e.dataTransfer.files?.[0]
        if (file) processarArquivo(file)
    }

    // ── PASSO 3: Filtros para o histórico ─────────────────────────────────
    const imoveisFiltrados = imoveis.filter(im => {
        const textoBusca = busca.toLowerCase()
        const matchBusca = !busca ||
            im.referencia.toLowerCase().includes(textoBusca) ||
            (im.proprietario || '').toLowerCase().includes(textoBusca) ||
            (im.telefone || '').includes(busca)

        const matchResposta =
            filtroResposta === 'todos' ? true :
            filtroResposta === 'SIM'    ? im.resposta === 'SIM' :
            filtroResposta === 'NÃO'    ? im.resposta === 'NÃO' :
            !im.resposta // pendente

        return matchBusca && matchResposta
    })

    // ── Métricas ───────────────────────────────────────────────────────────
    const total        = imoveis.length
    const confirmados  = imoveis.filter(i => i.resposta === 'SIM').length
    const indispon     = imoveis.filter(i => i.resposta === 'NÃO').length
    const pendentes    = imoveis.filter(i => !i.resposta).length
    const contatados   = imoveis.filter(i => i.ultimo_contato).length
    const proxContatos = imoveis.filter(i => {
        if (!i.proximo_contato) return false
        return new Date(i.proximo_contato) <= new Date()
    }).length

    const pctConfirmados = total ? Math.round((confirmados / total) * 100) : 0

    // ── Render ─────────────────────────────────────────────────────────────
    return (
        <div style={{ padding: '2rem', maxWidth: '1300px', margin: '0 auto' }}>

            {/* ── Cabeçalho ─────────────────────────────────────────────── */}
            <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <div style={{
                        width: 44, height: 44, borderRadius: '10px',
                        background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '1.4rem', flexShrink: 0,
                        boxShadow: '0 4px 16px rgba(124, 58, 237, 0.4)'
                    }}>🤖</div>
                    <div>
                        <h1 style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                            Robô de Atualização de Disponibilidade
                        </h1>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                            Gerencie o envio automático de WhatsApp para atualização do status dos imóveis.
                        </p>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>

                    <select
                        value={motorEnvio}
                        onChange={(e) => setMotorEnvio(e.target.value as any)}
                        disabled={disparando || (serverOnline === true && roboExecutando)}
                        style={{
                            padding: '0.75rem 1rem',
                            borderRadius: '10px',
                            background: 'var(--bg-card)',
                            border: '1px solid var(--border)',
                            color: 'var(--text-primary)',
                            fontSize: '0.9rem',
                            fontWeight: 600,
                            outline: 'none',
                            cursor: (disparando || (serverOnline === true && roboExecutando)) ? 'not-allowed' : 'pointer',
                            opacity: (disparando || (serverOnline === true && roboExecutando)) ? 0.6 : 1,
                        }}
                    >
                        <option value="EVOLUTION">⚡ Evolution API (Oculto)</option>
                        <option value="ADB">📱 Celular WhatsApp (Físico)</option>
                        <option value="SMS">📨 Celular SMS (Físico)</option>
                    </select>

                    {/* Badge status do servidor */}
                    <span style={{
                        padding: '0.4rem 0.9rem', borderRadius: '999px',
                        fontSize: '0.78rem', fontWeight: 700, border: '1px solid',
                        ...(serverOnline === null
                            ? { background: 'rgba(148,163,184,0.1)', color: '#94a3b8', borderColor: '#94a3b844' }
                            : serverOnline && roboExecutando
                                ? { background: 'rgba(16,185,129,0.15)', color: '#10b981', borderColor: '#10b98144' }
                                : serverOnline
                                    ? { background: 'rgba(59,130,246,0.15)', color: '#3b82f6', borderColor: '#3b82f644' }
                                    : { background: 'rgba(239,68,68,0.1)', color: '#ef4444', borderColor: '#ef444444' })
                    }}>
                        {serverOnline === null ? '○ Verificando...' :
                         serverOnline && roboExecutando ? '● Disparando' :
                         serverOnline ? '● Servidor online' : '● Servidor offline'}
                    </span>

                    <button
                        onClick={pararDisparo}
                        disabled={!serverOnline || !roboExecutando}
                        style={{
                            background: 'rgba(239, 68, 68, 0.1)',
                            color: '#ef4444',
                            padding: '0.8rem 1.5rem',
                            borderRadius: '10px',
                            fontWeight: 700,
                            border: '1px solid rgba(239, 68, 68, 0.4)',
                            cursor: (!serverOnline || !roboExecutando) ? 'not-allowed' : 'pointer',
                            opacity: (!serverOnline || !roboExecutando) ? 0.5 : 1,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            fontSize: '0.95rem',
                            transition: 'all 0.2s ease'
                        }}
                    >
                        🛑 Parar
                    </button>
                    <button
                        onClick={iniciarDisparo}
                        disabled={!serverOnline || roboExecutando}
                        style={{
                            background: 'linear-gradient(135deg, #10b981, #059669)',
                            color: 'white',
                            padding: '0.8rem 1.5rem',
                            borderRadius: '10px',
                            fontWeight: 700,
                            border: 'none',
                            cursor: (!serverOnline || roboExecutando) ? 'not-allowed' : 'pointer',
                            opacity: (!serverOnline || roboExecutando) ? 0.5 : 1,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            fontSize: '0.95rem',
                            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
                            transition: 'all 0.2s ease'
                        }}
                    >
                        {disparando ? <div className="spinner" style={{ width: 16, height: 16, borderTopColor: '#fff' }} /> : '🚀'}
                        Ativar Disparo
                    </button>
                </div>
            </div>


            {/* ══════════════════════════════════════════════════════════════
                PASSO 2 — IMPORTAR PLANILHA
            ══════════════════════════════════════════════════════════════ */}
            <Section titulo="📥 Importar Planilha" cor="#2563eb">
                <div
                    onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    onClick={() => !importing && fileRef.current?.click()}
                    style={{
                        border: `2px dashed ${dragOver ? '#2563eb' : 'rgba(255,255,255,0.12)'}`,
                        borderRadius: '12px',
                        padding: '2rem',
                        textAlign: 'center',
                        cursor: importing ? 'not-allowed' : 'pointer',
                        background: dragOver ? 'rgba(37,99,235,0.07)' : 'var(--bg-input)',
                        transition: 'all 200ms ease',
                        marginBottom: importResult ? '1.25rem' : '0',
                    }}
                >
                    <input
                        ref={fileRef}
                        type="file"
                        accept=".xlsx,.xls"
                        style={{ display: 'none' }}
                        onChange={handleFileInput}
                    />
                    {importing ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                            <div className="spinner" style={{ width: 32, height: 32, borderTopColor: '#2563eb' }} />
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Processando planilha...</p>
                        </div>
                    ) : (
                        <>
                            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📂</div>
                            <p style={{ color: 'var(--text-primary)', fontWeight: 600, marginBottom: '0.3rem' }}>
                                Clique para selecionar ou arraste o arquivo aqui
                            </p>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                                Arquivo <strong>.xlsx</strong> exportado do sistema da imobiliária
                            </p>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: '0.5rem' }}>
                                Colunas obrigatórias: <em>Referencia · Proprietário · Celular do Proprietário · Preço</em>
                                <br />
                                <span style={{ opacity: 0.6 }}>Opcional: Status</span>
                            </p>
                        </>
                    )}
                </div>

                {/* Resultado da importação */}
                {importResult && (
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '0.75rem',
                        marginTop: '1rem',
                    }}>
                        <ResultCard emoji="✅" valor={importResult.inseridos}  label="Inseridos"   cor="#10b981" />
                        <ResultCard emoji="🔄" valor={importResult.atualizados} label="Atualizados" cor="#3b82f6" />
                        <ResultCard emoji="❌" valor={importResult.erros}       label="Erros"       cor="#ef4444" />
                    </div>
                )}
            </Section>

            {/* ══════════════════════════════════════════════════════════════
                PASSO 3 — INDICADORES
            ══════════════════════════════════════════════════════════════ */}
            <Section titulo="📊 Indicadores" cor="#7c3aed">
                {loading ? (
                    <LoadingRow />
                ) : (
                    <>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                            gap: '1rem',
                            marginBottom: '1.25rem',
                        }}>
                            <KpiCard emoji="🏠" valor={total}       label="Total cadastrado" cor="#94a3b8" />
                            <KpiCard emoji="📞" valor={contatados}   label="Contatados"       cor="#3b82f6" />
                            <KpiCard emoji="✅" valor={confirmados}  label="Disponíveis"      cor="#10b981" />
                            <KpiCard emoji="❌" valor={indispon}     label="Indisponíveis"    cor="#ef4444" />
                            <KpiCard emoji="⏳" valor={pendentes}    label="Aguardando resp." cor="#f59e0b" />
                            <KpiCard emoji="📅" valor={proxContatos} label="Contato pendente" cor="#a78bfa" />
                        </div>

                        {/* Barra de progresso de confirmados */}
                        {total > 0 && (
                            <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                        Taxa de resposta positiva
                                    </span>
                                    <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#10b981' }}>
                                        {pctConfirmados}%
                                    </span>
                                </div>
                                <div style={{ height: 8, background: 'rgba(255,255,255,0.07)', borderRadius: 99, overflow: 'hidden' }}>
                                    <div style={{
                                        height: '100%',
                                        width: `${pctConfirmados}%`,
                                        background: 'linear-gradient(90deg, #10b981, #34d399)',
                                        borderRadius: 99,
                                        transition: 'width 600ms ease'
                                    }} />
                                </div>
                                <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
                                    <LegendaItem cor="#10b981" label={`Disponíveis (${confirmados})`} />
                                    <LegendaItem cor="#ef4444" label={`Indisponíveis (${indispon})`} />
                                    <LegendaItem cor="#f59e0b" label={`Pendentes (${pendentes})`} />
                                </div>
                            </div>
                        )}
                    </>
                )}
            </Section>

            {/* ══════════════════════════════════════════════════════════════
                PASSO 4 — HISTÓRICO DE CONTATOS
            ══════════════════════════════════════════════════════════════ */}
            <Section titulo="📋 Histórico de Contatos" cor="#0891b2">
                {/* Filtros */}
                <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
                    <input
                        type="text"
                        placeholder="🔍  Buscar por referência, proprietário ou telefone..."
                        value={busca}
                        onChange={e => setBusca(e.target.value)}
                        style={{
                            flex: 1, minWidth: 220, padding: '0.6rem 1rem',
                            borderRadius: '8px', border: '1px solid var(--border)',
                            background: 'var(--bg-input)', color: 'var(--text-primary)',
                            fontSize: '0.88rem', outline: 'none',
                        }}
                    />
                    {(['todos', 'SIM', 'NÃO', 'pendente'] as const).map(f => (
                        <button
                            key={f}
                            onClick={() => setFiltroResposta(f)}
                            style={{
                                padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.82rem',
                                fontWeight: 600, cursor: 'pointer', border: 'none',
                                background: filtroResposta === f
                                    ? f === 'SIM' ? '#10b981' : f === 'NÃO' ? '#ef4444' : f === 'pendente' ? '#f59e0b' : '#3b82f6'
                                    : 'rgba(255,255,255,0.06)',
                                color: filtroResposta === f ? '#fff' : 'var(--text-muted)',
                                transition: 'all 180ms ease',
                            }}
                        >
                            {f === 'todos' ? 'Todos' : f === 'pendente' ? '⏳ Pendentes' : f === 'SIM' ? '✅ Disponível' : '❌ Indisponível'}
                            <span style={{ marginLeft: '0.4rem', opacity: 0.8 }}>
                                ({f === 'todos' ? total : f === 'SIM' ? confirmados : f === 'NÃO' ? indispon : pendentes})
                            </span>
                        </button>
                    ))}
                </div>

                {loading ? (
                    <LoadingRow />
                ) : imoveisFiltrados.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📭</div>
                        <p>{total === 0 ? 'Nenhum imóvel importado ainda. Importe uma planilha acima.' : 'Nenhum resultado para os filtros aplicados.'}</p>
                    </div>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table className="table" style={{ minWidth: 800 }}>
                            <thead>
                                <tr>
                                    <th>Referência</th>
                                    <th>Proprietário</th>
                                    <th>Telefone</th>
                                    <th>Preço</th>
                                    <th>Status Imóvel</th>
                                    <th>Último Contato</th>
                                    <th>Resposta</th>
                                    <th>Próx. Contato</th>
                                </tr>
                            </thead>
                            <tbody>
                                {imoveisFiltrados.map(im => (
                                    <tr key={im.referencia}>
                                        <td>
                                            <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                                                {im.referencia}
                                            </span>
                                        </td>
                                        <td style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
                                            {im.proprietario || <span style={{ color: 'var(--text-muted)' }}>—</span>}
                                        </td>
                                        <td>
                                            {im.telefone ? (
                                                <a
                                                    href={`https://wa.me/55${im.telefone.replace(/\D/g, '')}`}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    style={{ color: '#25d366', fontSize: '0.85rem', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                                                >
                                                    💬 {im.telefone}
                                                </a>
                                            ) : <span style={{ color: 'var(--text-muted)' }}>—</span>}
                                        </td>
                                        <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                            {im.preco || <span style={{ color: 'var(--text-muted)' }}>—</span>}
                                        </td>
                                        <td>
                                            <BadgeStatus status={im.status} />
                                        </td>
                                        <td style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                                            {formatarDataHora(im.ultimo_contato)}
                                        </td>
                                        <td>
                                            <BadgeResposta resposta={im.resposta} />
                                        </td>
                                        <td style={{ fontSize: '0.82rem', color: im.proximo_contato && new Date(im.proximo_contato) <= new Date() ? '#f59e0b' : 'var(--text-muted)' }}>
                                            {formatarData(im.proximo_contato)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        <div style={{ marginTop: '0.75rem', fontSize: '0.78rem', color: 'var(--text-muted)', textAlign: 'right' }}>
                            Exibindo {imoveisFiltrados.length} de {total} registros
                        </div>
                    </div>
                )}
            </Section>

        </div>
    )
}

// ── Sub-componentes ────────────────────────────────────────────────────────

function Section({ titulo, cor, children }: { titulo: string; cor: string; children: React.ReactNode }) {
    return (
        <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderTop: `3px solid ${cor}`,
            borderRadius: '14px',
            padding: '1.5rem',
            marginBottom: '1.5rem',
        }}>
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1.25rem' }}>
                {titulo}
            </h2>
            {children}
        </div>
    )
}

function KpiCard({ emoji, valor, label, cor }: { emoji: string; valor: number; label: string; cor: string }) {
    return (
        <div style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: '10px',
            padding: '1rem',
            textAlign: 'center',
            transition: 'transform 200ms ease',
        }}
            onMouseEnter={e => (e.currentTarget.style.transform = 'translateY(-2px)')}
            onMouseLeave={e => (e.currentTarget.style.transform = 'translateY(0)')}
        >
            <div style={{ fontSize: '1.5rem', marginBottom: '0.3rem' }}>{emoji}</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: cor, lineHeight: 1 }}>{valor}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.3rem', fontWeight: 500 }}>{label}</div>
        </div>
    )
}

function ResultCard({ emoji, valor, label, cor }: { emoji: string; valor: number; label: string; cor: string }) {
    return (
        <div style={{
            background: `${cor}12`,
            border: `1px solid ${cor}33`,
            borderRadius: '10px',
            padding: '0.85rem 1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
        }}>
            <span style={{ fontSize: '1.4rem' }}>{emoji}</span>
            <div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: cor }}>{valor}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{label}</div>
            </div>
        </div>
    )
}

function LegendaItem({ cor, label }: { cor: string; label: string }) {
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            <div style={{ width: 10, height: 10, borderRadius: 3, background: cor, flexShrink: 0 }} />
            {label}
        </div>
    )
}

function BadgeResposta({ resposta }: { resposta: string | null }) {
    if (!resposta)
        return <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>Aguardando</span>

    const cfg = resposta === 'SIM'
        ? { bg: 'rgba(16,185,129,0.15)', cor: '#10b981', label: '✅ Disponível' }
        : { bg: 'rgba(239,68,68,0.15)',  cor: '#ef4444', label: '❌ Indisponível' }

    return (
        <span style={{
            fontSize: '0.75rem', fontWeight: 700, padding: '0.2rem 0.6rem',
            borderRadius: 99, background: cfg.bg, color: cfg.cor,
        }}>
            {cfg.label}
        </span>
    )
}

function BadgeStatus({ status }: { status: string | null }) {
    if (!status) return <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>—</span>
    const disponivel = status.toLowerCase().includes('dispon')
    return (
        <span style={{
            fontSize: '0.75rem', fontWeight: 600, padding: '0.2rem 0.6rem',
            borderRadius: 99,
            background: disponivel ? 'rgba(16,185,129,0.1)' : 'rgba(148,163,184,0.1)',
            color: disponivel ? '#10b981' : 'var(--text-muted)',
        }}>
            {status}
        </span>
    )
}

function LoadingRow() {
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '1.5rem 0', color: 'var(--text-muted)' }}>
            <div className="spinner" />
            Carregando...
        </div>
    )
}
