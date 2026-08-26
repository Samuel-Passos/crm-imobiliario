# Graph Report - Scraper_antigravity  (2026-08-26)

## Corpus Check
- 295 files · ~304,356 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1407 nodes · 1942 edges · 203 communities (172 shown, 31 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 49 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fedc762a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- geocoder_maps_scraper.py
- server.py
- extract_dump.py
- devDependencies
- start_chat_browser
- dependencies
- App.tsx
- pipeline.py
- fase2_extrai_dados.py
- compilerOptions
- post
- What You Must Do When Invoked
- supabase.ts
- browser_manager.py
- compilerOptions
- dispatcher.py
- scraper/main.py
- AdbClient
- orchestrator.py
- RoboDisponibilidadePage.tsx
- fase1_coleta_links.py
- parser_olx.py
- ContatosPage.tsx
- importar_planilha.py
- Sócios de Empresas Brasileiras
- get
- useDeviceType.ts
- OLX Captação — Módulo de Scraping Imobiliário
- CreativeEngine
- scraper_creci.py
- MapaImoveisPage.tsx
- ConfiguracoesPage
- extract_phones_from_olx
- config_db.py
- ImovelModal.tsx
- send_chat_isolado
- extract_phones_from_olx
- webhook_handler.py
- DashboardPage.tsx
- extract_phones_from_olx
- extract_phones_from_olx
- buscar_link_imovel
- Visão Geral dos Serviços
- monitor_server.py
- CampanhasPage
- ExtratorCnpjPage
- ImovelModal
- KanbanPage.tsx
- TemplatesPage.tsx
- AutomacoesPage
- LeadDetailsPage
- graphify reference: extra exports and benchmark
- varredura_expirados_extracao.py
- LeadDetailsPage.tsx
- KanbanCard.tsx
- gerente_geral.py
- LauncherHandler
- read_latest_chat_reply
- send_chat_message_olx
- ConfigManager
- Robô de Disponibilidade — CRM Imobiliário SJC
- geocode_single_google
- start_all.sh
- extract_one_phone
- ConfiguracoesPage.tsx
- ContatosPage
- rodar_automacao_jucesp
- Migrations — CRM Imobiliário
- CaptadorAPIHandler
- graphify reference: query, path, explain
- fase3_baixar_fotos_aceitou.py
- complementar_com_schema
- start_robo.sh
- run.sh
- DesignerPage.tsx
- extract_holding.py
- import-postgresql.sh
- start_crm_launcher.sh
- React + TypeScript + Vite
- test_anon.js
- fetch_dump.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- scratch_test_anon.js
- KanbanPage
- PesquisaPage
- tsconfig.json
- api_designer_file_delete
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- supabase_client.py
- limpador_expirados.py
- start.sh
- natureza_juridica.py
- AGENTS.md
- ciclo.sh
- rodar_creci_scraper.sh
- GEMINI.md
- extraction-spec.md
- pause_cycle
- resume_cycle
- stop_geocoder
- migrate_geocode_columns.py
- teste_2_cartoes.sh
- teste_completo.sh
- teste_rapido.sh
- teste_rapido_real.sh
- olx-captacao
- scraper

## God Nodes (most connected - your core abstractions)
1. `supabase` - 21 edges
2. `compilerOptions` - 20 edges
3. `compilerOptions` - 18 edges
4. `AdbClient` - 18 edges
5. `ConfiguracoesPage()` - 16 edges
6. `useAuth()` - 15 edges
7. `ImovelModal()` - 15 edges
8. `geocodificar_imovel_maps_scraper()` - 15 edges
9. `start_chat_browser()` - 14 edges
10. `extrair_dados_do_datalayer()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `extrair_detalhes()` --calls--> `solve_recaptcha()`  [INFERRED]
  creci_scraper/scraper_creci.py → scraper/solve_captcha.py
- `extrator_enriquecer_individual()` --calls--> `enriquecer_cnpj_individual()`  [INFERRED]
  robo_disponibilidade/server.py → extrator_cnpj/pipeline.py
- `test_10_leads()` --calls--> `enriquecer_cnpj_individual()`  [INFERRED]
  scratch/test_phones.py → extrator_cnpj/pipeline.py
- `extrator_enriquecer_receitaws()` --calls--> `enriquecer_receitaws_individual()`  [INFERRED]
  robo_disponibilidade/server.py → extrator_cnpj/pipeline.py
- `coletar_links()` --calls--> `get_config()`  [INFERRED]
  olx_captacao/fase1_coleta_links.py → scraper/config_db.py

## Import Cycles
- None detected.

## Communities (203 total, 31 thin omitted)

### Community 0 - "geocoder_maps_scraper.py"
Cohesion: 0.06
Nodes (50): geocodificar_imovel_google(), main(), _nivel_precisao(), _normalizar(), geocoder_google.py ────────────────── Segundo motor de geocodificação usando a…, Processa imóveis sem coordenadas (latitude IS NULL) usando a Google Maps API.…, Remove acentos para comparação., Verifica se o resultado retornado pertence à cidade esperada, consultando os… (+42 more)

### Community 1 - "server.py"
Cohesion: 0.09
Nodes (43): Request, adb_conectar(), adb_descobrir_wifi(), adb_desconectar(), adb_dial(), adb_parear(), adb_save_settings(), adb_sms_send() (+35 more)

### Community 2 - "extract_dump.py"
Cohesion: 0.08
Nodes (29): CNAESpider, get_text(), Yield the subclass item (last mile of the recursive strategy), Return text from "text()" XPath result as a string, removing whitespaces >>>…, Recursively get data/make requests for all parser hierarchical levels, clear_company_name(), clear_email(), extract_files() (+21 more)

### Community 3 - "devDependencies"
Cohesion: 0.05
Nodes (36): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals, @types/leaflet, @types/node (+28 more)

### Community 4 - "start_chat_browser"
Cohesion: 0.12
Nodes (28): close_chat_browser(), get_chat_page(), BrowserContext, Inicia o Playwright, o Chromium (ancorado no Workspace 3), carrega os cookies,…, start_chat_browser(), main(), envia_msg(), extract_chat_state() (+20 more)

### Community 5 - "dependencies"
Cohesion: 0.06
Nodes (33): dependencies, @dnd-kit/core, @dnd-kit/sortable, @dnd-kit/utilities, jsqr, leaflet, leaflet.markercluster, lucide-react (+25 more)

### Community 6 - "App.tsx"
Cohesion: 0.12
Nodes (20): App(), PrivateRoute(), PrivateRouteProps, AuthContext, AuthContextType, AuthProvider(), Profile, Role (+12 more)

### Community 7 - "pipeline.py"
Cohesion: 0.12
Nodes (23): Executa o enriquecimento direto (sem proxy) com limite de 3 req/min (delay de…, run_motor_direto(), _buscar_google_places(), _consultar_cnpj_api(), enriquecer_cnpj_individual(), enriquecer_receitaws_individual(), get_stats(), main() (+15 more)

### Community 8 - "fase2_extrai_dados.py"
Cohesion: 0.13
Nodes (27): _atualizar_status_link(), _buscar_links_pendentes(), _configurar_browser(), _configurar_pagina(), _detectar_bloqueio_ou_expirado(), extrair_dados(), _extrair_dados_da_pagina(), processar_e_salvar_unico() (+19 more)

### Community 9 - "compilerOptions"
Cohesion: 0.07
Nodes (26): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection, moduleResolution (+18 more)

### Community 10 - "post"
Cohesion: 0.11
Nodes (27): extract_phone_batch(), BackgroundTasks, post, Processa um lote de imóveis pendentes, usando a página persistente do Workspace…, Dispara o script de geocodificação para preencher coordenadas faltantes., Reprocessa imóveis já geocodificados com estratégia imprecisa (Centro do…, Segundo motor: usa a Google Maps Geocoding API para geocodificar imóveis que…, Reprocessa imóveis com geocode_needs_review=True usando a Google Maps API.… (+19 more)

### Community 11 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 12 - "supabase.ts"
Cohesion: 0.10
Nodes (12): supabase, supabaseAnonKey, supabaseUrl, ForgotPasswordPage(), ConfiguracaoIA, TemplateMensagem, Campanha, Lead (+4 more)

### Community 13 - "browser_manager.py"
Cohesion: 0.16
Nodes (18): dump_html(), Lock, main(), close_browser(), get_context(), get_lock(), get_page(), _get_random_fingerprint() (+10 more)

### Community 14 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, moduleResolution, noEmit (+14 more)

### Community 15 - "dispatcher.py"
Cohesion: 0.12
Nodes (11): dispatcher.py ───────────── Lê os imóveis pendentes do Supabase e envia a…, rodar_dispatcher(), EvolutionClient, _normalizar_telefone(), evolution_client.py ─────────────────── Wrapper para a Evolution API v2.…, Retorna apenas dígitos, com DDI 55 no início., Envia mídia via Evolution API. mediatype: 'image', 'video' ou 'document', Registra a URL de webhook na instância da Evolution API (v2). (+3 more)

### Community 16 - "scraper/main.py"
Cohesion: 0.13
Nodes (20): get_chat_status(), get_execution_status(), get_geocode_status(), get_scanner_status(), get_scraper_config(), health_check(), lifespan(), FastAPI (+12 more)

### Community 17 - "AdbClient"
Cohesion: 0.15
Nodes (11): CompletedProcess, AdbClient, Envia mensagem via SMS (Mensagens do sistema) via ADB. Fluxo: Abre a intent de…, Verifica se há pelo menos um dispositivo conectado e online., Abre o discador do Android com o número pré-preenchido. Usa action.DIAL (não…, Retorna o serial do melhor dispositivo disponível. Prioridade: Wi-Fi (IP:porta)…, Abre o chat do WhatsApp e, se houver coordenadas, clica no botão de chamada.…, Executa um comando ADB no dispositivo selecionado automaticamente. (+3 more)

### Community 18 - "orchestrator.py"
Cohesion: 0.13
Nodes (19): check_pause(), extract_phone_single_lead(), process_batch_chat_sending(), process_batch_phone_extraction(), Busca em lote todos os pendentes e extrai os telefones 1 a 1., Aguarda enquanto o sinal de pausa estiver ativo., Extrai telefone de 1 único imóvel e atualiza o BD. Se a API foi bloqueada pelo…, [DESATIVADO] Envio movido para robo_chat_prospeccao/sender.py (+11 more)

### Community 19 - "RoboDisponibilidadePage.tsx"
Cohesion: 0.12
Nodes (9): COLUNAS_OBRIGATORIAS, formatarData(), formatarDataHora(), Imovel, MAPEAMENTO, RoboDisponibilidadePage(), iniciarDisparo(), pararDisparo() (+1 more)

### Community 20 - "fase1_coleta_links.py"
Cohesion: 0.14
Nodes (19): coletar_links(), _configurar_browser(), _configurar_pagina(), _extrair_links_da_pagina(), Browser, Page, fase1_coleta_links.py --------------------- Fase 1 do scraper OLX: navega pelas…, Cria browser com Chromium do sistema. (+11 more)

### Community 21 - "parser_olx.py"
Cohesion: 0.15
Nodes (19): extrair_dados_do_datalayer(), _formatar_preco_str(), _inferir_label_preco(), _inferir_tipo_negocio(), _parse_ad_id(), _parse_bigint_or_none(), _parse_int(), _parse_preco() (+11 more)

### Community 22 - "ContatosPage.tsx"
Cohesion: 0.20
Nodes (13): ContatoModal(), handleSalvar(), obterCoordenadas(), Props, TIPOS, ContatosMapa(), DefaultIcon, Props (+5 more)

### Community 23 - "importar_planilha.py"
Cohesion: 0.16
Nodes (17): Client, DataFrame, buscar_registros_existentes(), carregar_credenciais(), formatar_linha(), importar(), imprimir_resumo(), ler_planilha() (+9 more)

### Community 24 - "Sócios de Empresas Brasileiras"
Cohesion: 0.11
Nodes (16): História do dataset socios-brasil, Agilizando o Download, Dados, Dados auxiliares, Entrada, Executando, Importando em Bancos de Dados, Instalando as Dependências (+8 more)

### Community 25 - "get"
Cohesion: 0.12
Nodes (17): adb_diagnostico(), adb_gerar_qr(), adb_get_settings(), adb_get_wifi_host(), api_designer_agent_files(), extrator_logs(), extrator_status(), get_status() (+9 more)

### Community 26 - "useDeviceType.ts"
Cohesion: 0.22
Nodes (12): AppLayout(), BottomNav(), navItems, navItems, Sidebar(), BREAKPOINTS, DeviceType, getDeviceType() (+4 more)

### Community 27 - "OLX Captação — Módulo de Scraping Imobiliário"
Cohesion: 0.12
Nodes (15): Ativar o ambiente virtual, Como funciona o anti-bot, Configurações (.env), Estrutura, Execução completa (Fase 1 + Fase 2), Fase 1 — Coleta de links, Fase 2 — Extração de dados, Fluxo completo (+7 more)

### Community 28 - "CreativeEngine"
Cohesion: 0.16
Nodes (10): base64_to_bytes(), CreativeEngine, Simplifica a chamada para análise de imagem mantendo o grounding., Geração via Pollinations.ai (Flux) executada internamente como uma Tool., Inicializa ou retorna o modelo solicitado, com ferramentas (tools) nativas., Gera textos e processa chamadas de ferramentas (Function Calling)., api_designer_chat(), Interface unificada para o Designer IA (Gemini 1.5 Pro + Nano Banana). Suporta… (+2 more)

### Community 29 - "scraper_creci.py"
Cohesion: 0.31
Nodes (13): add_log_progress(), collect_all_registers(), _extract_last_page(), _extract_registers(), extrair_detalhes(), get_progress(), log(), main() (+5 more)

### Community 30 - "MapaImoveisPage.tsx"
Cohesion: 0.14
Nodes (7): CATEGORY_ICONS, DefaultIcon, MapPoint, MapView(), MapViewProps, MapaImoveisPage(), MultiSelectDropdown()

### Community 31 - "ConfiguracoesPage"
Cohesion: 0.14
Nodes (3): ConfiguracoesPage(), salvarScraperConfig(), salvarSettings()

### Community 32 - "extract_phones_from_olx"
Cohesion: 0.18
Nodes (14): _aguardar_numero_revelar(), extract_phones_from_olx(), _extrair_numeros(), _extrair_numeros_e_nomes(), _fechar_modal_se_aberto(), _is_xpath(), Any, Detecta o modal da OLX que aparece após clicar no botão de telefone. PRIMEIRO… (+6 more)

### Community 33 - "config_db.py"
Cohesion: 0.14
Nodes (4): run_filtro_mercado(), get_scraper_config(), get_config(), Retorna as configurações do scraper armazenadas no banco de dados. Caso haja…

### Community 34 - "ImovelModal.tsx"
Cohesion: 0.17
Nodes (7): DefaultIcon, LocationPicker(), LocationPickerProps, Aba, chipStyle, PERMUTA_OPTS, readonlyStyle

### Community 35 - "send_chat_isolado"
Cohesion: 0.21
Nodes (11): _digitar_humano(), Any, BrowserContext, Page, Clica no elemento e digita simulando digitação humana (delay entre teclas). Usa…, 1. Abre aba no anúncio. 2. Localiza o botão //*[@id="price-box-button-chat"].…, send_chat_isolado(), _criar_contexto_isolado() (+3 more)

### Community 36 - "extract_phones_from_olx"
Cohesion: 0.22
Nodes (12): _aguardar_numero_revelar(), extract_phones_from_olx(), _extrair_numeros(), _fechar_modal_se_aberto(), _is_xpath(), Any, Acessa a URL do anúncio OLX usando Playwright + cookies do Samuel. Fluxo com…, Extrai e normaliza números de telefone de um texto. (+4 more)

### Community 37 - "webhook_handler.py"
Cohesion: 0.24
Nodes (10): Groq, analisar_resposta(), _get_client(), ia_analyzer.py ────────────── Usa o Groq LLM para interpretar a resposta do…, Analisa a resposta do proprietário usando o Groq. Retorna dict com chaves:…, _formatar_tel_banco(), processar_evento_mensagem(), webhook_handler.py ────────────────── Processa os webhooks recebidos da… (+2 more)

### Community 38 - "DashboardPage.tsx"
Cohesion: 0.18
Nodes (8): CampaignStats, DashboardPage(), ImovelStats, KanbanStats, LinkStats, ScraperLog, ScraperRun, TipoItem

### Community 39 - "extract_phones_from_olx"
Cohesion: 0.25
Nodes (10): _aguardar_numero_revelar(), extract_phones_from_olx(), _extrair_numeros(), _fechar_modal_se_aberto(), Any, Extrai e normaliza números de telefone de um texto., Aguarda o span mudar de máscara para número real e retorna o texto., Detecta e fecha o modal da OLX que aparece após clicar no botão de telefone.… (+2 more)

### Community 40 - "extract_phones_from_olx"
Cohesion: 0.25
Nodes (10): _aguardar_numero_revelar(), extract_phones_from_olx(), _extrair_numeros(), _fechar_modal_se_aberto(), Any, Acessa a URL do anúncio OLX usando Playwright + cookies do Samuel. Fluxo com…, Extrai e normaliza números de telefone de um texto., Aguarda o span mudar de máscara para número real e retorna o texto. (+2 more)

### Community 41 - "buscar_link_imovel"
Cohesion: 0.24
Nodes (10): _buscar_async(), buscar_link_imovel(), _buscar_via_playwright(), _buscar_via_url_direta(), buscar_link_imovel.py ───────────────────── Busca a URL pública do imóvel no…, Versão síncrona com cache automático. A mesma referência não é buscada duas…, Tenta construir a URL de busca diretamente e verificar se redireciona para a…, Abre o site com Playwright, interage com o campo de busca por referência e… (+2 more)

### Community 42 - "Visão Geral dos Serviços"
Cohesion: 0.20
Nodes (9): 1. Scraper Backend (Porta 8765), 2. CRM Frontend (Porta 5173), 3. API Captador OLX (Porta 8768), 4. Robô de Disponibilidade (Porta 8766), 5. Monitor de Chat / Prospecção, Arquitetura do Sistema: CRM Imobiliário & Scraper, Ferramentas e Integrações Externas, Regras e Fluxo de Desenvolvimento (+1 more)

### Community 43 - "monitor_server.py"
Cohesion: 0.27
Nodes (9): dashboard(), get_registros(), get_stats(), get_status(), get, Monitor Server — CRECI-SP Scraper ==================================== Servidor…, Retorna o estado atual do scraper., Retorna os registros do CSV (paginado). (+1 more)

### Community 44 - "CampanhasPage"
Cohesion: 0.31
Nodes (6): CampanhasPage(), carregarCampanhas(), handleCriarCampanha(), handleDeletarCampanha(), handleUpdateCampanha(), processarPlanilha()

### Community 45 - "ExtratorCnpjPage"
Cohesion: 0.27
Nodes (5): ExtratorCnpjPage(), carregarDados(), handleEnriquecerIndividual(), handleEnriquecerReceitaWS(), handleSaveDatabase()

### Community 46 - "ImovelModal"
Cohesion: 0.22
Nodes (5): ImovelModal(), handleSalvar(), obterCoordenadas(), telephoneLink(), timeAgo()

### Community 47 - "KanbanPage.tsx"
Cohesion: 0.33
Nodes (7): KanbanFilters(), KanbanFiltersProps, DroppableColuna, SortableCard, CorretorInfo, FiltrosKanban, KanbanColuna

### Community 48 - "TemplatesPage.tsx"
Cohesion: 0.20
Nodes (3): Settings, supabase, TemplatesPage()

### Community 49 - "AutomacoesPage"
Cohesion: 0.28
Nodes (4): AutomacoesPage(), carregarDados(), handleDeleteTemplate(), handleSaveTemplate()

### Community 50 - "LeadDetailsPage"
Cohesion: 0.31
Nodes (5): LeadDetailsPage(), carregarDadosLead(), handleEnriquecerIndividual(), handleEnriquecerReceitaWS(), handleSaveDatabase()

### Community 51 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 52 - "varredura_expirados_extracao.py"
Cohesion: 0.44
Nodes (8): _configurar_browser(), _configurar_pagina(), _detectar_bloqueio_ou_expirado(), formatar_tempo(), Browser, Page, varrer_expirados(), verificar_anuncio()

### Community 54 - "KanbanCard.tsx"
Cohesion: 0.43
Nodes (6): Props, formatPreco(), KanbanCard, KanbanCardProps, getChatUrl(), ImovelKanban

### Community 55 - "gerente_geral.py"
Cohesion: 0.36
Nodes (7): executar_extracao_telefone(), executar_geocodificador(), executar_script(), Executa um script de forma isolada e aguarda ele terminar., O Geocodificador do Google Maps é uma função dentro de um script, então o…, Aciona a extração de telefone em lote via endpoint do servidor, reaproveitando…, run_gerente_geral()

### Community 57 - "read_latest_chat_reply"
Cohesion: 0.29
Nodes (6): CustomChatGroq, Any, ChatGroq, Acessa o anúncio, abre o painel lateral de chat e extrai A ÚLTIMA MENSAGEM…, read_latest_chat_reply(), teste_local()

### Community 58 - "send_chat_message_olx"
Cohesion: 0.29
Nodes (6): CustomChatGroq, Any, ChatGroq, Usa o Browser Use para acessar a URL do anúncio OLX, abrir o chat lateral e…, send_chat_message_olx(), teste_local()

### Community 59 - "ConfigManager"
Cohesion: 0.29
Nodes (4): ConfigManager, Salva uma única chave de configuração, preservando as demais., Retorna todas as configurações, priorizando o JSON, depois o ENV, depois os…, Salva as configurações no user_config.json.

### Community 60 - "Robô de Disponibilidade — CRM Imobiliário SJC"
Cohesion: 0.25
Nodes (7): Configuração, Estrutura, Etapas do Robô, Exemplo de saída, Lógica de Preservação de Dados, Robô de Disponibilidade — CRM Imobiliário SJC, Uso — Etapa 2

### Community 61 - "geocode_single_google"
Cohesion: 0.25
Nodes (8): geocode_one_google(), Geocodifica via Google Maps um único imóvel (revisão pontual)., Novo motor: Reprocessa TODOS os anúncios ativos e não-expirados via Google Maps., run_geocoder_google_full(), geocode_full_google(), geocode_single_google(), Geocodifica via Google Maps Scraper um único imóvel e atualiza o BD. Chamado…, Varre o banco de dados e reprocessa via Google Maps todos os anúncios: 1.…

### Community 62 - "start_all.sh"
Cohesion: 0.32
Nodes (6): check_service(), iniciar_tunnel_bg(), NVM_DIR, PATH, PYTHONPATH, start_all.sh script

### Community 63 - "extract_one_phone"
Cohesion: 0.29
Nodes (7): BaseModel, extract_one_phone(), ImovelRequest, O usuário abriu o Imóvel no CRM e clicou em "Extrair Telefones Agora"., [TESTE] Roda a extração de telefones diretamente em uma URL OLX, sem passar…, test_url(), UrlRequest

### Community 66 - "rodar_automacao_jucesp"
Cohesion: 0.38
Nodes (6): extrair_texto_pdf(), Lê o PDF e retorna o texto extraído., Salva os dados extraídos no campo notas_investigacao do Supabase., Fluxo: Abre JUCESP -> Espera Login -> Busca CNPJ -> Baixa PDF -> Processa., rodar_automacao_jucesp(), salvar_no_supabase()

### Community 67 - "Migrations — CRM Imobiliário"
Cohesion: 0.29
Nodes (6): ⚠️ Ajuste necessário no trigger da Migration 004, ⚠️ Atenção antes de rodar a Migration 004, Como executar no Supabase, Migrations — CRM Imobiliário, Ordem de Execução, Verificação pós-migration

### Community 69 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 70 - "fase3_baixar_fotos_aceitou.py"
Cohesion: 0.53
Nodes (5): baixar_e_fazer_upload(), main(), obter_id_coluna_aceitou(), processar_imoveis_aceitos(), Baixa a imagem da OLX e faz upload para o Supabase Storage. Retorna a URL…

### Community 71 - "complementar_com_schema"
Cohesion: 0.33
Nodes (6): complementar_com_schema(), _extrair_rua_do_html(), _extrair_schema_org(), Complementa os dados já extraídos do dataLayer com informações do schema.org…, Extrai o JSON-LD de schema.org do HTML., Busca o endereço diretamente no INITIAL_STATE do HTML (mesmo que escapado).…

### Community 72 - "start_robo.sh"
Cohesion: 0.47
Nodes (4): iniciar_servidor(), iniciar_tunnel(), PYTHONPATH, start_robo.sh script

### Community 73 - "run.sh"
Cohesion: 0.60
Nodes (5): download_data(), extract_cnae(), extract_data(), extract_holding(), run.sh script

### Community 74 - "DesignerPage.tsx"
Cohesion: 0.40
Nodes (3): Agente, DesignerPage(), Message

### Community 75 - "extract_holding.py"
Cohesion: 0.70
Nodes (4): convert_empresa(), convert_socio(), filter_csv(), main()

### Community 76 - "import-postgresql.sh"
Cohesion: 0.80
Nodes (4): execute_sql_files(), import_cnae_tables(), import_table(), import-postgresql.sh script

### Community 77 - "start_crm_launcher.sh"
Cohesion: 0.40
Nodes (3): NVM_DIR, PATH, start_crm_launcher.sh script

### Community 78 - "React + TypeScript + Vite"
Cohesion: 0.50
Nodes (3): Expanding the ESLint configuration, React Compiler, React + TypeScript + Vite

### Community 80 - "fetch_dump.py"
Cohesion: 1.00
Nodes (3): download_file(), main(), update_crm_status()

### Community 81 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 82 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 83 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 88 - "api_designer_file_delete"
Cohesion: 0.67
Nodes (3): delete, api_designer_file_delete(), Exclui um arquivo de referência.

## Knowledge Gaps
- **237 isolated node(s):** `ciclo.sh script`, `rodar_creci_scraper.sh script`, `name`, `private`, `version` (+232 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_config()` connect `config_db.py` to `scraper/main.py`, `geocoder_maps_scraper.py`, `fase1_coleta_links.py`, `start_chat_browser`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `get_scraper_config()` connect `config_db.py` to `server.py`, `get`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `extrator_enriquecer_individual()` connect `server.py` to `pipeline.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **What connects `ciclo.sh script`, `rodar_creci_scraper.sh script`, `name` to the rest of the system?**
  _237 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `geocoder_maps_scraper.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05868118572292801 - nodes in this community are weakly interconnected._
- **Should `server.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Should `extract_dump.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07557354925775979 - nodes in this community are weakly interconnected._