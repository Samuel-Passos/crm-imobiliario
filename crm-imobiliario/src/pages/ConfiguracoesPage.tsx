import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { supabase } from '../lib/supabase'
import './ConfiguracoesPage.css'

const ROBO_URL = 'http://localhost:8766'

interface Settings {
    [key: string]: string | number
}

type StatusMsg = { tipo: 'idle' | 'ok' | 'erro' | 'carregando'; msg: string }

export function ConfiguracoesPage() {
    const [settings, setSettings] = useState<Settings | null>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [activeTab, setActiveTab] = useState<'geral' | 'adb' | 'api' | 'infra' | 'scraper'>('geral')

    // ── Status em tempo real (USB e Wi-Fi separados) ──────────────────────
    const [usbDevice, setUsbDevice] = useState<{ serial: string; model: string } | null>(null)
    const [wifiDevices, setWifiDevices] = useState<{ ip_porta: string; model: string }[]>([])

    // ── States dos painéis ────────────────────────────────────────────────
    const [adbIp, setAdbIp] = useState('')
    const [adbPortaPareamento, setAdbPortaPareamento] = useState('')
    const [adbCodigo, setAdbCodigo] = useState('')
    const [adbPortaConexao, setAdbPortaConexao] = useState('')
    const [wifiStatus, setWifiStatus] = useState<StatusMsg>({ tipo: 'idle', msg: '' })
    const [usbStatus, setUsbStatus] = useState<StatusMsg>({ tipo: 'idle', msg: '' })
    const [serverOnline, setServerOnline] = useState(true)

    const [qrImageUrl, setQrImageUrl] = useState('')
    const [qrGerando, setQrGerando] = useState(false)
    const [qrVisivel, setQrVisivel] = useState(false)
    const [diagRunning, setDiagRunning] = useState(false)
    const [savedWifiHost, setSavedWifiHost] = useState('')
    const [scraperConfig, setScraperConfig] = useState<any>(null)

    useEffect(() => {
        carregarSettings()
        carregarScraperConfig()
        carregarWifiHost()
        const timer = setInterval(checkStatus, 3000)
        return () => clearInterval(timer)
    }, [])

    async function carregarWifiHost() {
        try {
            const res = await fetch(`${ROBO_URL}/adb/wifi-host`)
            const data = await res.json()
            if (data.ok && data.ip) {
                setAdbIp(data.ip)
                setAdbPortaConexao(data.porta)
                setSavedWifiHost(data.host)
            }
        } catch { /* silencioso */ }
    }

    async function checkStatus() {
        try {
            const res = await fetch(`${ROBO_URL}/status`)
            const data = await res.json()
            setUsbDevice(data.usb_device ?? null)
            setWifiDevices(data.wifi_devices ?? [])
            
            setServerOnline(prev => {
                if (!prev && res.ok) {
                    setUsbStatus({ tipo: 'idle', msg: '' })
                    setWifiStatus({ tipo: 'idle', msg: '' })
                }
                return res.ok
            })
        } catch {
            setUsbDevice(null)
            setWifiDevices([])
            setServerOnline(false)
            setUsbStatus({ tipo: 'erro', msg: '❌ Servidor offline. Inicie o robô no terminal.' })
            setWifiStatus({ tipo: 'erro', msg: '❌ Servidor offline. Inicie o robô no terminal.' })
        }
    }


    // Função de auxilio para o setRobotStatus que define o serverOnline
    function setRobotStatus(online: boolean) {
        setServerOnline(online)
    }


    async function carregarSettings() {
        try {
            const res = await fetch(`${ROBO_URL}/adb/settings`)
            const data = await res.json()
            if (data.ok) setSettings(data.settings)
            else toast.error('Erro ao carregar configurações.')
        } catch { toast.error('Servidor de configurações offline.') }
        finally { setLoading(false) }
    }

    async function salvarSettings() {
        if (!settings) return
        setSaving(true)
        const tid = toast.loading('Salvando alterações...')
        try {
            if (activeTab === 'scraper') await salvarScraperConfig()
            const res = await fetch(`${ROBO_URL}/adb/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ settings })
            })
            const data = await res.json()
            if (data.ok) toast.success('Configurações aplicadas! 🚀', { id: tid })
            else toast.error(data.mensagem || 'Erro ao salvar.', { id: tid })
        } catch { toast.error('Falha de conexão.', { id: tid }) }
        finally { setSaving(false) }
    }

    
    async function carregarScraperConfig() {
        try {
            const res = await fetch(`${ROBO_URL}/scraper/config`)
            const data = await res.json()
            if (data.ok && data.config) setScraperConfig(data.config)
        } catch (e) {
            console.error("Catch Scraper Config:", e)
        }
    }

    async function salvarScraperConfig() {
        if (!scraperConfig) return
        setSaving(true)
        const tid = toast.loading('Salvando Configurações do Scraper...')
        try {
            const res = await fetch(`${ROBO_URL}/scraper/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scraperConfig)
            })
            const data = await res.json()
            if (!data.ok) throw new Error("Erro no backend")
            toast.success('Configurações do Scraper aplicadas! 🚀', { id: tid })
        } catch { toast.error('Erro ao salvar.', { id: tid }) }
        finally { setSaving(false) }
    }
    
    const handleScraperChange = (key: string, value: any) => {
        setScraperConfig((prev: any) => prev ? { ...prev, [key]: value } : { url_coleta_padrao: '', limite_paginas_fase1: 100, limite_repetidos_fase1: 60, lote_fase2: 50, lote_fase2_5: 50, lote_geocoder: 20, lote_extracao: 5, lote_script1: 5, lote_script2: 5, lote_script3: 5, [key]: value })
    }

    const handleChange = (key: string, value: string | number) => {
        setSettings(prev => prev ? { ...prev, [key]: value } : null)
    }

    async function executarDiagnostico() {
        setDiagRunning(true)
        setUsbStatus({ tipo: 'carregando', msg: 'Verificando USB...' })
        setWifiStatus({ tipo: 'carregando', msg: 'Verificando Wi-Fi...' })
        try {
            const res = await fetch(`${ROBO_URL}/adb/diagnostico`)
            const data = await res.json()
            if (!data.ok) throw new Error(data.mensagem || 'Erro')
            const d = data.diagnostico
            if (d.usb.adb_autorizado) {
                setUsbStatus({ tipo: 'ok', msg: `✅ USB conectado — ${d.usb.dispositivo?.model || d.usb.dispositivo?.serial}` })
            } else if (d.usb.hardware_detectado) {
                setUsbStatus({ tipo: 'erro', msg: '⚠️ Cabo detectado, mas ADB não autorizado. Toque "OK" no popup do celular.' })
            } else {
                setUsbStatus({ tipo: 'erro', msg: '❌ Nenhum hardware Android detectado via USB.' })
            }
            if (d.wifi.conectado) {
                const ips = d.wifi.dispositivos.map((dev: any) => dev.ip_porta).join(', ')
                setWifiStatus({ tipo: 'ok', msg: `✅ Wi-Fi conectado — ${ips}` })
            } else {
                setWifiStatus({ tipo: 'idle', msg: 'Wi-Fi não conectado.' })
            }
            if (d.dica) toast(d.dica, { icon: '💡', duration: 6000 })
        } catch {
            setUsbStatus({ tipo: 'erro', msg: '❌ Erro ao executar diagnóstico.' })
            setWifiStatus({ tipo: 'erro', msg: '❌ Erro ao executar diagnóstico.' })
        } finally {
            setDiagRunning(false)
        }
    }

    const handleGerarQr = async () => {
        setQrGerando(true)
        setQrVisivel(false)
        setWifiStatus({ tipo: 'carregando', msg: 'Gerando QR code...' })
        try {
            const res = await fetch(`${ROBO_URL}/adb/gerar-qr`)
            const data = await res.json()
            if (data.ok) {
                setQrImageUrl(data.qr_image)
                setQrVisivel(true)
                setWifiStatus({ tipo: 'idle', msg: '' })
                toast.success('QR gerado! Aponte o celular.')
            } else {
                setWifiStatus({ tipo: 'erro', msg: `❌ ${data.mensagem}` })
                toast.error(data.mensagem)
            }
        } catch { setWifiStatus({ tipo: 'erro', msg: '❌ Servidor offline.' }) }
        finally { setQrGerando(false) }
    }

    async function checarUsb() {
        setUsbStatus({ tipo: 'carregando', msg: 'Verificando USB...' })
        try {
            const res = await fetch(`${ROBO_URL}/adb/diagnostico`)
            const data = await res.json()
            const d = data.diagnostico?.usb
            if (d?.adb_autorizado) {
                setUsbStatus({ tipo: 'ok', msg: `✅ ${d.dispositivo?.model || d.dispositivo?.serial} conectado via USB` })
            } else if (d?.hardware_detectado) {
                setUsbStatus({ tipo: 'erro', msg: '⚠️ Hardware detectado, mas ADB não autorizado. Toque OK no popup do celular.' })
            } else {
                setUsbStatus({ tipo: 'erro', msg: '❌ Nenhum hardware Android detectado. Verifique o cabo.' })
            }
        } catch { setUsbStatus({ tipo: 'erro', msg: '❌ Erro ao checar USB.' }) }
    }

    async function iniciarScrcpy() {
        try {
            const res = await fetch(`${ROBO_URL}/adb/scrcpy`, { method: 'POST' })
            const data = await res.json()
            if (data.ok) toast.success('Scrcpy iniciado!')
            else toast.error(data.mensagem)
        } catch { toast.error('Robô offline') }
    }

    async function conectarWifi() {
        if (!adbIp || !adbPortaConexao) { toast.error('Preencha o IP e a Porta'); return }
        setWifiStatus({ tipo: 'carregando', msg: 'Conectando...' })
        try {
            const res = await fetch(`${ROBO_URL}/adb/conectar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip_porta: `${adbIp}:${adbPortaConexao}` })
            })
            const data = await res.json()
            setWifiStatus(data.ok
                ? { tipo: 'ok', msg: `✅ Conectado em ${adbIp}:${adbPortaConexao}` }
                : { tipo: 'erro', msg: `❌ ${data.mensagem}` })
        } catch { setWifiStatus({ tipo: 'erro', msg: '❌ Erro de comunicação.' }) }
    }

    async function pararWifi() {
        if (wifiDevices.length === 0) { toast.error('Nenhum dispositivo Wi-Fi conectado.'); return }
        setWifiStatus({ tipo: 'carregando', msg: 'Desconectando...' })
        try {
            const ip = wifiDevices[0].ip_porta
            const res = await fetch(`${ROBO_URL}/adb/desconectar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip_porta: ip })
            })
            const data = await res.json()
            setWifiStatus(data.ok
                ? { tipo: 'idle', msg: '' }
                : { tipo: 'erro', msg: `❌ ${data.mensagem}` })
        } catch { setWifiStatus({ tipo: 'erro', msg: '❌ Erro ao desconectar.' }) }
    }

    async function handleParear() {

        setWifiStatus({ tipo: 'carregando', msg: 'Pareando...' })
        try {
            if (!adbIp || !adbPortaPareamento || !adbCodigo) { toast.error('Preencha IP, Porta e Código de Pareamento'); return }
            const res = await fetch(`${ROBO_URL}/adb/parear`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip_porta: `${adbIp}:${adbPortaPareamento}`, codigo: adbCodigo })
            })
            const data = await res.json()
            setWifiStatus(data.ok
                ? { tipo: 'ok', msg: '✅ Pareamento realizado!' }
                : { tipo: 'erro', msg: '❌ ' + data.mensagem })
        } catch { setWifiStatus({ tipo: 'erro', msg: '❌ Erro de comunicação.' }) }
    }

    const [testandoGemini, setTestandoGemini] = useState(false)

    async function handleTestGemini() {
        setTestandoGemini(true)
        const tid = toast.loading('Testando conexão com Gemini...')
        try {
            const res = await fetch(`${ROBO_URL}/extrator/test-gemini`, { method: 'POST' })
            const data = await res.json()
            if (data.ok) toast.success(data.mensagem, { id: tid, duration: 5000 })
            else toast.error(data.mensagem, { id: tid, duration: 5000 })
        } catch { toast.error('Servidor offline', { id: tid }) }
        finally { setTestandoGemini(false) }
    }

    if (loading) return (

        <div className="settings-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚙️</div>
                <div style={{ fontWeight: 800, color: '#535F70' }}>Carregando Central de Comando...</div>
            </div>
        </div>
    )

    return (
        <div className="settings-container">
            <div className="settings-wrapper">

                <header className="settings-header">
                    <div>
                        <h1>Central de Comando</h1>
                        <p>Gestão de automações, infraestrutura e conexões móveis.</p>
                    </div>
                    <button onClick={salvarSettings} className="m3-btn m3-btn-primary" disabled={saving}>
                        {saving ? 'Gravando...' : '💾 Salvar Sistema'}
                    </button>
                </header>

                <nav className="m3-tabs">
                    <Tab active={activeTab === 'geral'} onClick={() => setActiveTab('geral')} icon="🤖" label="Robô Geral" />
                    <Tab active={activeTab === 'adb'} onClick={() => setActiveTab('adb')} icon="📱" label="Celular (ADB)" />
                    <Tab active={activeTab === 'api'} onClick={() => setActiveTab('api')} icon="🔌" label="APIs & Chaves" />
                    <Tab active={activeTab === 'infra'} onClick={() => setActiveTab('infra')} icon="💾" label="Infraestrutura" />
                    <Tab active={activeTab === 'scraper'} onClick={() => setActiveTab('scraper')} icon="🕷️" label="Robô Scraper" />
                </nav>

                <main className="config-section">

                    {/* ── Robô Geral ── */}
                    {activeTab === 'geral' && (
                        <div className="config-group">
                            <div className="config-group-title">Automação de Disponibilidade</div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
                                <Field label="Nome do Remetente" value={settings?.REMETENTE_NOME} onChange={(v: any) => handleChange('REMETENTE_NOME', v)} />
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                                    <Field label="Delay entre Envios (s)" type="number" tooltip="Intervalo de segurança entre cada ação" value={settings?.DELAY_ENTRE_ENVIOS} onChange={(v: any) => handleChange('DELAY_ENTRE_ENVIOS', parseInt(v))} />
                                    <Field label="Limite Diário" type="number" value={settings?.LIMITE_DIARIO} onChange={(v: any) => handleChange('LIMITE_DIARIO', parseInt(v))} />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ── ADB ── */}
                    {activeTab === 'adb' && (
                        <>
                            {/* Diagnóstico */}
                            <div className="config-group">
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                                    <div>
                                        <div className="config-group-title" style={{ margin: 0 }}>🔍 Diagnóstico de Conexão</div>
                                        <p style={{ margin: '4px 0 0', fontSize: '0.82rem', color: '#535F70' }}>
                                            Analisa USB e Wi-Fi simultaneamente e exibe o status de cada método.
                                        </p>
                                    </div>
                                    <button className="m3-btn m3-btn-primary" onClick={executarDiagnostico} disabled={diagRunning}>
                                        {diagRunning ? '⏳ Analisando...' : '🔍 Diagnosticar Agora'}
                                    </button>
                                </div>
                            </div>

                            {/* Grade USB | Wi-Fi */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>

                                {/* ══ Painel USB ══ */}
                                <div className="config-group" style={{ margin: 0 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                                        <span style={{ fontSize: '1.5rem' }}>🔌</span>
                                        <div style={{ flex: 1 }}>
                                            <div className="config-group-title" style={{ margin: 0 }}>Cabo USB</div>
                                            <div style={{ fontSize: '0.75rem', color: '#535F70' }}>Conexão direta por cabo</div>
                                        </div>
                                        <AdbStatusBadge online={!!usbDevice} label={usbDevice ? 'CONECTADO' : 'DESCONECTADO'} />
                                    </div>

                                    {usbDevice && (
                                        <div style={{ background: '#E6F4EA', border: '1px solid #1E8E3E40', borderRadius: 10, padding: '0.75rem 1rem', marginBottom: '1rem', fontSize: '0.8rem' }}>
                                            <strong style={{ color: '#1E8E3E' }}>📱 {usbDevice.model}</strong>
                                            <div style={{ color: '#535F70', marginTop: 2 }}>Serial: {usbDevice.serial}</div>
                                        </div>
                                    )}

                                    <StatusBanner status={usbStatus} />

                                    <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                        <button className="m3-btn m3-btn-outline" style={{ borderColor: '#0056D240', color: '#0056D2' }} onClick={checarUsb}>
                                            🔎 Checar USB
                                        </button>
                                        <button className="m3-btn m3-btn-outline" style={{ borderColor: '#53607040', color: '#535F70' }} onClick={iniciarScrcpy}>
                                            📺 Visualizar Tela (scrcpy)
                                        </button>
                                    </div>

                                    <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#F0F4FF', borderRadius: 10, fontSize: '0.75rem', color: '#535F70', lineHeight: 1.6 }}>
                                        <strong style={{ color: '#1A1C1E' }}>Como usar:</strong><br />
                                        1. Conecte o cabo USB<br />
                                        2. Ative <strong>Depuração USB</strong> nas Opções do Desenvolvedor<br />
                                        3. Autorize o popup que aparece na tela do celular<br />
                                        4. Clique em <strong>Checar USB</strong>
                                    </div>
                                </div>

                                {/* ══ Painel Wi-Fi ══ */}
                                <div className="config-group" style={{ margin: 0 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                                        <span style={{ fontSize: '1.5rem' }}>📡</span>
                                        <div style={{ flex: 1 }}>
                                            <div className="config-group-title" style={{ margin: 0 }}>Wi-Fi (Sem Fio)</div>
                                            <div style={{ fontSize: '0.75rem', color: '#535F70' }}>Conexão via rede local</div>
                                        </div>
                                        <AdbStatusBadge online={wifiDevices.length > 0} label={wifiDevices.length > 0 ? 'CONECTADO' : 'DESCONECTADO'} />
                                    </div>

                                    {wifiDevices.length > 0 && (
                                        <div style={{ background: '#E6F4EA', border: '1px solid #1E8E3E40', borderRadius: 10, padding: '0.75rem 1rem', marginBottom: '1rem', fontSize: '0.8rem' }}>
                                            {wifiDevices.map(dev => (
                                                <div key={dev.ip_porta}>
                                                    <strong style={{ color: '#1E8E3E' }}>📱 {dev.model}</strong>
                                                    <div style={{ color: '#535F70', marginTop: 2 }}>IP: {dev.ip_porta}</div>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {/* Banner: Conexão salva — reconectar com 1 clique */}
                                    {savedWifiHost && wifiDevices.length === 0 && (
                                        <div style={{
                                            background: '#FFF8E1', border: '1px solid #F9A82540',
                                            borderRadius: 10, padding: '0.6rem 1rem', marginBottom: '0.75rem'
                                        }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.78rem' }}>
                                                <span>💾</span>
                                                <div style={{ flex: 1 }}>
                                                    <strong style={{ color: '#B45309' }}>Última conexão: {savedWifiHost}</strong>
                                                    <div style={{ color: '#92400E', marginTop: 1 }}>Se a porta mudou, use "Auto-descobrir"</div>
                                                </div>
                                            </div>
                                            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                                                <button
                                                    className="m3-btn m3-btn-outline"
                                                    style={{ borderColor: '#F9A82540', color: '#B45309', fontSize: '0.75rem', flex: 1 }}
                                                    onClick={async () => {
                                                        setWifiStatus({ tipo: 'carregando', msg: `Reconectando a ${savedWifiHost}...` })
                                                        try {
                                                            const res = await fetch(`${ROBO_URL}/adb/conectar`, {
                                                                method: 'POST',
                                                                headers: { 'Content-Type': 'application/json' },
                                                                body: JSON.stringify({ ip_porta: savedWifiHost })
                                                            })
                                                            const data = await res.json()
                                                            setWifiStatus(data.ok
                                                                ? { tipo: 'ok', msg: `✅ Reconectado a ${savedWifiHost}` }
                                                                : { tipo: 'erro', msg: `❌ ${data.mensagem}` })
                                                        } catch { setWifiStatus({ tipo: 'erro', msg: '❌ Erro de comunicação.' }) }
                                                    }}
                                                >
                                                    ⚡ Reconectar
                                                </button>
                                                <button
                                                    className="m3-btn m3-btn-outline"
                                                    style={{ borderColor: '#0056D240', color: '#0056D2', fontSize: '0.75rem', flex: 1 }}
                                                    onClick={async () => {
                                                        setWifiStatus({ tipo: 'carregando', msg: '🔍 Varrendo portas ADB (37000-45000)...' })
                                                        try {
                                                            const ip = savedWifiHost.split(':')[0]
                                                            const res = await fetch(`${ROBO_URL}/adb/descobrir-wifi`, {
                                                                method: 'POST',
                                                                headers: { 'Content-Type': 'application/json' },
                                                                body: JSON.stringify({ ip })
                                                            })
                                                            const data = await res.json()
                                                            if (data.ok) {
                                                                setSavedWifiHost(data.host)
                                                                setAdbIp(data.ip)
                                                                setAdbPortaConexao(data.porta)
                                                                setWifiStatus({ tipo: 'ok', msg: `✅ Nova porta encontrada e conectada: ${data.host}` })
                                                                toast.success(`Porta descoberta: ${data.host}`)
                                                            } else {
                                                                setWifiStatus({ tipo: 'erro', msg: `❌ ${data.mensagem}` })
                                                            }
                                                        } catch { setWifiStatus({ tipo: 'erro', msg: '❌ Erro na varredura de portas.' }) }
                                                    }}
                                                >
                                                    🔎 Auto-descobrir porta
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    <StatusBanner status={wifiStatus} />

                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', margin: '1rem 0' }}>
                                        <Field label="IP do Celular" placeholder="192.168.1.96" value={adbIp} onChange={setAdbIp} />
                                        <Field label="Porta Conexão" placeholder="5555" value={adbPortaConexao} onChange={setAdbPortaConexao} />
                                    </div>

                                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                                        <button className="m3-btn m3-btn-outline" style={{ borderColor: '#0056D240', color: '#0056D2', flex: 1 }} onClick={conectarWifi}>
                                            📡 Conectar Wi-Fi
                                        </button>
                                        {wifiDevices.length > 0 && (
                                            <button className="m3-btn m3-btn-outline" style={{ borderColor: '#D9302540', color: '#D93025' }} onClick={pararWifi}>
                                                ✂️ Desconectar
                                            </button>
                                        )}
                                    </div>

                                    {/* Primeiro uso - pareamento */}
                                    <div style={{ borderTop: '1px solid #E0E4EC', paddingTop: '0.75rem', marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                        <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#535F70', letterSpacing: '0.05em' }}>PRIMEIRO USO — PAREAR</div>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                                            <Field label="Porta Pareamento" placeholder="37123" value={adbPortaPareamento} onChange={setAdbPortaPareamento} />
                                            <Field label="Código" placeholder="123456" value={adbCodigo} onChange={(v: string) => setAdbCodigo(v.replace(/\D/g, ''))} />
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                                            <button className="m3-btn m3-btn-outline" style={{ borderColor: '#006D3A40', color: '#006D3A', fontSize: '0.78rem' }} onClick={handleParear}>

                                                🔗 Parear (Código)
                                            </button>
                                            <button className="m3-btn m3-btn-outline" style={{ borderColor: '#006D3A40', color: '#006D3A', fontSize: '0.78rem' }} onClick={qrVisivel ? () => setQrVisivel(false) : handleGerarQr} disabled={qrGerando}>
                                                🔳 {qrGerando ? 'Gerando...' : qrVisivel ? 'Fechar QR' : 'Parear via QR'}
                                            </button>
                                        </div>
                                    </div>

                                    {qrVisivel && qrImageUrl && (
                                        <div className="qr-container" style={{ marginTop: '1rem' }}>
                                            <img src={qrImageUrl} style={{ width: 180, height: 180, borderRadius: '8px' }} alt="QR ADB" />
                                            <p style={{ color: '#535F70', fontSize: '0.75rem', marginTop: '0.5rem', fontWeight: 600 }}>
                                                Celular → Depuração sem fio → Emparelhar com QR Code
                                            </p>
                                        </div>
                                    )}

                                    <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#F0F4FF', borderRadius: 10, fontSize: '0.75rem', color: '#535F70', lineHeight: 1.6 }}>
                                        <strong style={{ color: '#1A1C1E' }}>Como usar (Android 11+):</strong><br />
                                        1. Ative <strong>Depuração Sem Fio</strong> nas Opções do Desenvolvedor<br />
                                        2. Anote o IP e a <strong>Porta de Conexão</strong><br />
                                        3. 1º uso: vá em <em>Parear dispositivo</em> para código ou QR<br />
                                        4. Clique em <strong>Conectar Wi-Fi</strong>
                                    </div>
                                </div>
                            </div>

                            {/* Coordenadas */}
                            <div className="config-group">
                                <div className="config-group-title">Mapeamento de Coordenadas (Clicks)</div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
                                    <div style={{ padding: '1rem', background: '#F8FAFD', borderRadius: '12px' }}>
                                        <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#1A1C1E', marginBottom: '1rem' }}>💬 WhatsApp & SMS</div>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                            <Field label="X (Botão Enviar)" value={settings?.ADB_TAP_X} onChange={(v: any) => handleChange('ADB_TAP_X', v)} />
                                            <Field label="Y (Botão Enviar)" value={settings?.ADB_TAP_Y} onChange={(v: any) => handleChange('ADB_TAP_Y', v)} />
                                        </div>
                                    </div>
                                    <div style={{ padding: '1rem', background: '#F8FAFD', borderRadius: '12px' }}>
                                        <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#1A1C1E', marginBottom: '1rem' }}>📞 Chamadas de Voz</div>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                            <Field label="X (Telefone)" value={settings?.ADB_WHATSAPP_CALL_X} onChange={(v: any) => handleChange('ADB_WHATSAPP_CALL_X', v)} />
                                            <Field label="Y (Telefone)" value={settings?.ADB_WHATSAPP_CALL_Y} onChange={(v: any) => handleChange('ADB_WHATSAPP_CALL_Y', v)} />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Timings */}
                            <div className="config-group">
                                <div className="config-group-title">Timings & Lotes</div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                                    <Field label="Abertura App (s)" type="number" value={settings?.ADB_DELAY_ABERTURA} onChange={(v: any) => handleChange('ADB_DELAY_ABERTURA', parseInt(v))} />
                                    <Field label="Duração Chamada (s)" type="number" value={settings?.ADB_DELAY_ABERTURA_CALL} onChange={(v: any) => handleChange('ADB_DELAY_ABERTURA_CALL', parseInt(v))} />
                                    <Field label="SMS Limite Diário" type="number" value={settings?.SMS_LIMIT_DAILY} onChange={(v: any) => handleChange('SMS_LIMIT_DAILY', parseInt(v))} />
                                    <Field label="SMS Lote" type="number" value={settings?.SMS_BATCH_SIZE} onChange={(v: any) => handleChange('SMS_BATCH_SIZE', parseInt(v))} />
                                </div>
                            </div>
                        </>
                    )}

                    
                    {/* ── Robô Scraper ── */}
                    {activeTab === 'scraper' && (
                        <>
                            <div className="config-group">
                                <div className="config-group-title">Base de Coleta (OLX)</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                    <Field label="URL Padrão de Extração" value={scraperConfig?.url_coleta_padrao || ''} onChange={(v: any) => handleScraperChange('url_coleta_padrao', v)} placeholder="Cole o link da OLX..." />
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem' }}>
                                        <Field label="Limite de Páginas (Fase 1)" type="number" value={scraperConfig?.limite_paginas_fase1 || 0} onChange={(v: any) => handleScraperChange('limite_paginas_fase1', parseInt(v) || 0)} />
                                        <Field label="Limite Anúncios Repetidos (Fase 1)" type="number" value={scraperConfig?.limite_repetidos_fase1 || 0} onChange={(v: any) => handleScraperChange('limite_repetidos_fase1', parseInt(v) || 0)} />
                                        <Field label="Lote Extração (Fase 2)" type="number" value={scraperConfig?.lote_fase2 || 0} onChange={(v: any) => handleScraperChange('lote_fase2', parseInt(v) || 0)} />
                                        <Field label="Lote Filtro (Fase 2.5)" type="number" value={scraperConfig?.lote_fase2_5 || 0} onChange={(v: any) => handleScraperChange('lote_fase2_5', parseInt(v) || 0)} />
                                    </div>
                                </div>
                            </div>
                            
                            <div className="config-group">
                                <div className="config-group-title">Limites das Automações</div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                                    <Field label="Lote Google Maps" type="number" value={scraperConfig?.lote_geocoder || 0} onChange={(v: any) => handleScraperChange('lote_geocoder', parseInt(v) || 0)} />
                                    <Field label="Lote Extrator Telefone" type="number" value={scraperConfig?.lote_extracao || 0} onChange={(v: any) => handleScraperChange('lote_extracao', parseInt(v) || 0)} />
                                </div>
                            </div>
                            
                            <div className="config-group">
                                <div className="config-group-title">Funil do Chat OLX</div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                                    <Field label="Envios Script 1" type="number" value={scraperConfig?.lote_script1 || 0} onChange={(v: any) => handleScraperChange('lote_script1', parseInt(v) || 0)} />
                                    <Field label="Envios Script 2" type="number" value={scraperConfig?.lote_script2 || 0} onChange={(v: any) => handleScraperChange('lote_script2', parseInt(v) || 0)} />
                                    <Field label="Envios Script 3" type="number" value={scraperConfig?.lote_script3 || 0} onChange={(v: any) => handleScraperChange('lote_script3', parseInt(v) || 0)} />
                                </div>
                            </div>
                        </>
                    )}

                    {/* ── APIs ── */}
                    {activeTab === 'api' && (
                        <>
                            <div className="config-group">
                                <div className="config-group-title">
                                    <span style={{ marginRight: '8px' }}>🪄</span> Google Gemini (IA Pro)
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                    <Field label="Gemini API Key" type="password" value={settings?.GEMINI_API_KEY} onChange={(v: any) => handleChange('GEMINI_API_KEY', v)} placeholder="Cole sua chave do Google AI Studio..." />
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                                        <Field label="Modelo Padrão" value={settings?.GEMINI_MODEL} onChange={(v: any) => handleChange('GEMINI_MODEL', v)} placeholder="gemini-1.5-pro" />
                                        <Field label="Base URL" value={settings?.GEMINI_BASE_URL} onChange={(v: any) => handleChange('GEMINI_BASE_URL', v)} placeholder="https://generativelanguage.googleapis.com/v1beta" />
                                    </div>
                                    <div style={{ padding: '0.75rem', background: '#F0F4FF', borderRadius: 10, fontSize: '0.75rem', color: '#535F70', lineHeight: 1.6 }}>
                                        <strong style={{ color: '#1A1C1E' }}>Como obter a chave:</strong><br />
                                        1. Acesse o <a href="https://aistudio.google.com/" target="_blank" rel="noreferrer" style={{ fontWeight: 800, color: '#0056D2' }}>Google AI Studio</a><br />
                                        2. Gere sua API Key e cole no campo acima.<br />
                                        3. Esta chave será usada para análise inteligente de dossiês e automação de scripts.
                                    </div>
                                    <button 
                                        onClick={handleTestGemini} 
                                        disabled={testandoGemini || !serverOnline} 
                                        className="m3-btn m3-btn-outline" 
                                        style={{ borderColor: '#006D3A40', color: '#006D3A', alignSelf: 'flex-start' }}
                                    >
                                        {testandoGemini ? '⏳ Testando...' : '⚡ Testar Conexão com Gemini'}
                                    </button>
                                </div>
                            </div>


                            <div className="config-group">
                                <div className="config-group-title">Inteligência Artificial (Groq - Legado)</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                    <Field label="API Key" type="password" value={settings?.GROQ_API_KEY} onChange={(v: any) => handleChange('GROQ_API_KEY', v)} />
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                                        <Field label="Modelo" value={settings?.GROQ_MODEL} onChange={(v: any) => handleChange('GROQ_MODEL', v)} />
                                        <Field label="Base URL" value={settings?.GROQ_BASE_URL} onChange={(v: any) => handleChange('GROQ_BASE_URL', v)} />
                                    </div>
                                </div>
                            </div>

                            <div className="config-group">
                                <div className="config-group-title">WhatsApp API (Evolution)</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                    <Field label="Instância" value={settings?.EVOLUTION_INSTANCE} onChange={(v: any) => handleChange('EVOLUTION_INSTANCE', v)} />
                                    <Field label="API Key" type="password" value={settings?.EVOLUTION_API_KEY} onChange={(v: any) => handleChange('EVOLUTION_API_KEY', v)} />
                                    <Field label="URL da API" value={settings?.EVOLUTION_API_URL} onChange={(v: any) => handleChange('EVOLUTION_API_URL', v)} />
                                </div>
                            </div>
                        </>
                    )}

                    {/* ── Infra ── */}
                    {activeTab === 'infra' && (
                        <div className="config-group">
                            <div className="config-group-title">Core & Database (Supabase)</div>
                            <div style={{ background: '#FCE8E6', padding: '1rem', borderRadius: '12px', border: '1px solid #D93025', marginBottom: '1.5rem' }}>
                                <p style={{ margin: 0, fontSize: '0.85rem', color: '#D93025', fontWeight: 800 }}>⚠️ AVISO: Alterar estas chaves pode comprometer a conexão central do CRM.</p>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                <Field label="Supabase URL" value={settings?.SUPABASE_URL} onChange={(v: any) => handleChange('SUPABASE_URL', v)} />
                                <Field label="Service Role Key" type="password" value={settings?.SUPABASE_KEY} onChange={(v: any) => handleChange('SUPABASE_KEY', v)} />
                            </div>
                        </div>
                    )}

                </main>
            </div>
        </div>
    )
}

function Tab({ active, onClick, icon, label }: any) {
    return (
        <button onClick={onClick} className={`m3-tab-btn ${active ? 'active' : ''}`}>
            <span>{icon}</span> {label}
        </button>
    )
}

function AdbStatusBadge({ online, label }: { online: boolean; label: string }) {
    return (
        <div style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '3px 10px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 800,
            background: online ? '#E6F4EA' : '#FCE8E6',
            color: online ? '#1E8E3E' : '#D93025',
            border: `1px solid ${online ? '#1E8E3E' : '#D93025'}40`,
            whiteSpace: 'nowrap'
        }}>
            <span style={{
                width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
                background: online ? '#1E8E3E' : '#D93025',
                boxShadow: online ? '0 0 6px #1E8E3E' : 'none'
            }} />
            {label}
        </div>
    )
}

function StatusBanner({ status }: { status: StatusMsg }) {
    if (status.tipo === 'idle' && !status.msg) return null
    const bg: Record<string, string> = { ok: '#E6F4EA', erro: '#FCE8E6', carregando: '#E8F0FE', idle: '#F1F3F4' }
    const color: Record<string, string> = { ok: '#1E8E3E', erro: '#D93025', carregando: '#1967D2', idle: '#535F70' }
    return (
        <div style={{
            background: bg[status.tipo], color: color[status.tipo],
            padding: '0.6rem 1rem', borderRadius: 10, fontSize: '0.8rem', fontWeight: 600,
            border: `1px solid ${color[status.tipo]}30`
        }}>
            {status.tipo === 'carregando' ? '⏳ ' : ''}{status.msg}
        </div>
    )
}

function Field({ label, value, onChange, type = 'text', tooltip, placeholder }: any) {
    const [show, setShow] = useState(false)
    const isPassword = type === 'password'
    const inputType = isPassword ? (show ? 'text' : 'password') : type

    return (
        <div className="m3-field">
            <label className="m3-label">
                {label} {tooltip && <span title={tooltip} style={{ cursor: 'help', opacity: 0.6 }}>ⓘ</span>}
            </label>
            <div className="m3-input-wrapper">
                {type === 'textarea' ? (
                    <textarea className="m3-input m3-textarea" placeholder={placeholder} value={value || ''} onChange={e => onChange(e.target.value)} />
                ) : (
                    <input type={inputType} className="m3-input" placeholder={placeholder} value={value || ''} onChange={e => onChange(e.target.value)} />
                )}
                {isPassword && (
                    <button type="button" onClick={() => setShow(!show)} style={{ position: 'absolute', right: '1rem', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', opacity: 0.7 }}>
                        {show ? '👁️' : '🙈'}
                    </button>
                )}
            </div>
        </div>
    )
}
