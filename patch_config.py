import re

file_path = "crm-imobiliario/src/pages/ConfiguracoesPage.tsx"
with open(file_path, "r") as f:
    content = f.read()

# 1. Imports
content = content.replace("import toast from 'react-hot-toast'", "import toast from 'react-hot-toast'\nimport { supabase } from '../../lib/supabase'")

# 2. State for tab
content = content.replace(
    "const [activeTab, setActiveTab] = useState<'geral' | 'adb' | 'api' | 'infra'>('geral')",
    "const [activeTab, setActiveTab] = useState<'geral' | 'adb' | 'api' | 'infra' | 'scraper'>('geral')"
)

# 3. State for scraper config & 4. useEffect
content = content.replace(
    "const [savedWifiHost, setSavedWifiHost] = useState('')",
    "const [savedWifiHost, setSavedWifiHost] = useState('')\n    const [scraperConfig, setScraperConfig] = useState<any>(null)"
)
content = content.replace(
    "carregarSettings()",
    "carregarSettings()\n        carregarScraperConfig()"
)

# 5 & 6. Functions for scraper config
scraper_funcs = """
    async function carregarScraperConfig() {
        try {
            const { data, error } = await supabase.from('configuracoes_scraper').select('*').eq('id', 1).single()
            if (!error && data) setScraperConfig(data)
        } catch {}
    }

    async function salvarScraperConfig() {
        if (!scraperConfig) return
        setSaving(true)
        const tid = toast.loading('Salvando Configurações do Scraper...')
        try {
            const { error } = await supabase.from('configuracoes_scraper').update(scraperConfig).eq('id', 1)
            if (error) throw error
            toast.success('Configurações do Scraper aplicadas! 🚀', { id: tid })
        } catch { toast.error('Erro ao salvar.', { id: tid }) }
        finally { setSaving(false) }
    }
    
    const handleScraperChange = (key: string, value: string | number) => {
        setScraperConfig((prev: any) => prev ? { ...prev, [key]: value } : null)
    }
"""
content = content.replace(
    "const handleChange = (key: string, value: string | number) => {",
    scraper_funcs + "\n    const handleChange = (key: string, value: string | number) => {"
)

# 7. Button action - wait, the global save button calls `salvarSettings`.
# We should make it call both if the tab is scraper, or just both!
content = content.replace(
    "const res = await fetch(`${ROBO_URL}/adb/settings`, {",
    "if (activeTab === 'scraper') await salvarScraperConfig()\n            const res = await fetch(`${ROBO_URL}/adb/settings`, {"
)

# 8. Tab bar
content = content.replace(
    '<Tab active={activeTab === \'infra\'} onClick={() => setActiveTab(\'infra\')} icon="💾" label="Infraestrutura" />',
    '<Tab active={activeTab === \'infra\'} onClick={() => setActiveTab(\'infra\')} icon="💾" label="Infraestrutura" />\n                    <Tab active={activeTab === \'scraper\'} onClick={() => setActiveTab(\'scraper\')} icon="🕷️" label="Robô Scraper" />'
)

# 9. UI Section
scraper_ui = """
                    {/* ── Robô Scraper ── */}
                    {activeTab === 'scraper' && scraperConfig && (
                        <>
                            <div className="config-group">
                                <div className="config-group-title">Base de Coleta (OLX)</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                    <Field label="URL Padrão de Extração" value={scraperConfig.url_coleta_padrao} onChange={(v: any) => handleScraperChange('url_coleta_padrao', v)} placeholder="Cole o link da OLX..." />
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                                        <Field label="Limite de Páginas (Fase 1)" type="number" value={scraperConfig.limite_paginas_fase1} onChange={(v: any) => handleScraperChange('limite_paginas_fase1', parseInt(v) || 0)} />
                                        <Field label="Lote de Extração (Fase 2)" type="number" value={scraperConfig.lote_fase2} onChange={(v: any) => handleScraperChange('lote_fase2', parseInt(v) || 0)} />
                                    </div>
                                </div>
                            </div>
                            
                            <div className="config-group">
                                <div className="config-group-title">Limites das Automações</div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                                    <Field label="Lote Google Maps" type="number" value={scraperConfig.lote_geocoder} onChange={(v: any) => handleScraperChange('lote_geocoder', parseInt(v) || 0)} />
                                    <Field label="Lote Extrator Whatsapp" type="number" value={scraperConfig.lote_extracao} onChange={(v: any) => handleScraperChange('lote_extracao', parseInt(v) || 0)} />
                                </div>
                            </div>
                            
                            <div className="config-group">
                                <div className="config-group-title">Funil do Chat OLX</div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                                    <Field label="Envios Script 1" type="number" value={scraperConfig.lote_script1} onChange={(v: any) => handleScraperChange('lote_script1', parseInt(v) || 0)} />
                                    <Field label="Envios Script 2" type="number" value={scraperConfig.lote_script2} onChange={(v: any) => handleScraperChange('lote_script2', parseInt(v) || 0)} />
                                    <Field label="Envios Script 3" type="number" value={scraperConfig.lote_script3} onChange={(v: any) => handleScraperChange('lote_script3', parseInt(v) || 0)} />
                                </div>
                            </div>
                        </>
                    )}
"""
content = content.replace(
    "{/* ── APIs ── */}",
    scraper_ui + "\n                    {/* ── APIs ── */}"
)

with open(file_path, "w") as f:
    f.write(content)

print("Patch aplicado com sucesso!")
