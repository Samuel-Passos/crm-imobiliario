import asyncio
import os
import json
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

from browser_manager_chat import start_chat_browser, close_chat_browser, get_chat_page

dotenv_path = os.path.join(os.path.dirname(__file__), "..", "scraper", ".env")
load_dotenv(dotenv_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

KANBAN_INTERAGIU_ID = "47d38925-ac92-491e-bb69-0d38b23e4b80"
KANBAN_SCRIPT1_ID = "934d8c3e-b887-482d-86ce-7fdeafe3101a"
KANBAN_SCRIPT2_ID = "3dd77415-d636-45c4-99e9-060cf2abc8e5"
KANBAN_SCRIPT3_ID = "b3f1f0b3-1a1b-4ab2-9907-c1bc51f8e1dc"

async def extract_chat_state(page):
    """
    Injeta JS para tentar deduzir quem mandou a última mensagem e pegar o texto.
    Retorna: {'autor': 'usuario'|'proprietario'|'desconhecido', 'texto': '...'}
    """
    state = await page.evaluate('''() => {
        const msgs = document.querySelectorAll('[data-testid="message-bubble"], [class*="message-bubble"], [class*="MessageBubble"]');
        if (msgs.length === 0) return {autor: 'desconhecido', texto: ''};
        
        const ultima = msgs[msgs.length - 1];
        const text = ultima.innerText.trim();
        const textLower = text.toLowerCase();
        
        // Se a mensagem for exatamente nossa
        if (textLower.includes("meu nome é samuel") || textLower === "oi" || textLower === "obrigado" || textLower.includes("corretor de imoveis autônomo")) {
            return {autor: 'usuario', texto: text};
        }
        
        // Se a cor do balão ou alinhamento da div pai indicar
        const rect = ultima.getBoundingClientRect();
        const screenMid = window.innerWidth / 2;
        if (rect.right > screenMid * 1.5) {
            return {autor: 'usuario', texto: text};
        } else if (rect.left < screenMid * 0.5) {
            return {autor: 'proprietario', texto: text};
        }
        
        return {autor: 'desconhecido', texto: text};
    }''')
    return state

async def envia_msg(page, texto: str):
    """ Cola o texto no input e manda Enter. """
    xpath_input = '//*[@id="input-text-message"]'
    input_msg = page.locator(f"xpath={xpath_input}").first
    await input_msg.wait_for(state="visible", timeout=10000)
    
    await input_msg.fill(texto)
    await asyncio.sleep(0.5)
    await input_msg.press("Enter")
    await asyncio.sleep(1.0)
    print(f"  ✅ Mensagem '{texto[:10]}...' enviada com sucesso!")

async def monitorar():
    print("="*50)
    print("🔄 INICIANDO VARREDURA DO MONITOR DE CHAT")
    print("="*50)
    
    # Busca prospecções ativas (aguardando_resposta e etapa_atual < 2)
    res = supabase.table("prospecoes_chat").select("imovel_id, status, etapa_atual, data_ultimo_envio").eq("status", "aguardando_resposta").execute()
    
    if not res.data:
        print("📭 Nenhuma prospecção ativa encontrada.")
        return

    # Busca imoveis correspondentes para confirmar Kanban e pegar list_id
    imoveis_ids = [d["imovel_id"] for d in res.data]
    imoveis_res = supabase.table("imoveis").select("id, list_id, kanban_coluna_id").in_("id", imoveis_ids).execute()
    
    # Monta dict para fácil acesso
    imoveis_map = {im["id"]: im for im in imoveis_res.data}
    
    # Inicia o browser no Workspace 3 se tiver algo para processar
    await start_chat_browser()
    page = get_chat_page()
    
    for row in res.data:
        imovel_id = row["imovel_id"]
        status = row["status"]
        etapa_atual = row.get("etapa_atual", 0)
        ultimo_envio_iso = row["data_ultimo_envio"]
        
        if imovel_id not in imoveis_map:
            continue
            
        imovel = imoveis_map[imovel_id]
        
        # Só processa se estiver em alguma coluna de Script
        if imovel["kanban_coluna_id"] not in [KANBAN_SCRIPT1_ID, KANBAN_SCRIPT2_ID, KANBAN_SCRIPT3_ID]:
            continue
            
        list_id = imovel["list_id"]
        if not list_id:
            continue
            
        print(f"\n🔎 Analisando imovel {imovel_id} (list_id {list_id})")
        
        # Calcular tempo desde o último envio
        if ultimo_envio_iso:
            try:
                # Tratar parseamento de ISO
                ultimo_envio = datetime.fromisoformat(ultimo_envio_iso.replace("Z", "+00:00"))
                minutos_passados = (datetime.now(timezone.utc) - ultimo_envio).total_seconds() / 60
            except:
                minutos_passados = 0
        else:
            minutos_passados = 0
            
        print(f"  ⏳ Tempo desde última msg: {minutos_passados:.1f} minutos | Status Drip: {status}")
        
        # Vai para a página
        chat_url = f"https://chat.olx.com.br/?list-id={list_id}"
        await page.goto(chat_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4.0)  # Aguarda carregar mensagens
        
        # Analisa quem mandou a última mensagem
        chat_state = await extract_chat_state(page)
        autor_ultima = chat_state["autor"]
        texto_ultima = chat_state["texto"]
        print(f"  🗣️ Autor da última msg (deduzido): {autor_ultima} | Texto: '{texto_ultima[:30]}...'")
        
        if autor_ultima == "proprietario":
            print("  🚨 CLIENTE RESPONDEU! Atualizando kanban...")
            # Atualiza banco
            supabase.table("imoveis").update({"kanban_coluna_id": KANBAN_INTERAGIU_ID}).eq("id", imovel_id).execute()
            supabase.table("prospecoes_chat").update({
                "status": "respondeu",
                "ultima_resposta_proprietario": texto_ultima,
                "data_ultima_resposta": datetime.now(timezone.utc).isoformat()
            }).eq("imovel_id", imovel_id).execute()
            continue
            
        # Buscar templates no banco de dados
        resp_tmpl = supabase.table("templates_mensagem").select("*").in_("tipo", ["followup_sem_resposta", "followup_com_resposta"]).eq("ativo", True).order("ordem", desc=False).execute()
        templates = resp_tmpl.data
        
        if not templates or len(templates) < 2:
            print("  ❌ Templates Drip (oi/obrigado) não encontrados ou incompletos no painel Automações!")
            continue
            
        MENSAGEM_1 = templates[0]["corpo"]
        delay_minutos_1 = templates[0].get("dias_aguardar") or 10
        
        MENSAGEM_2 = templates[1]["corpo"]
        delay_minutos_2 = templates[1].get("dias_aguardar") or 10

        if etapa_atual == 0: # Aguardando para mandar a segunda (Script 2)
            if minutos_passados >= delay_minutos_1:
                print(f"  -> Enviando drip 1 ({MENSAGEM_1[:15]}...)...")
                await envia_msg(page, MENSAGEM_1)
                supabase.table("prospecoes_chat").update({
                    "etapa_atual": 1,
                    "ultima_mensagem_enviada": MENSAGEM_1,
                    "data_ultimo_envio": datetime.now(timezone.utc).isoformat()
                }).eq("imovel_id", imovel_id).execute()
                # Atualizar Kanban para Script 2
                supabase.table("imoveis").update({"kanban_coluna_id": KANBAN_SCRIPT2_ID}).eq("id", imovel_id).execute()
                print("  ✅ Kanban atualizado -> Script 2")
            else:
                print(f"  -> Ainda não passou o tempo (Configurado: {delay_minutos_1}m / Passou: {minutos_passados:.1f}m). Pulando.")
                
        elif etapa_atual == 1: # Aguardando para mandar a terceira (Script 3)
            if minutos_passados >= delay_minutos_2:
                print(f"  -> Enviando drip 2 ({MENSAGEM_2[:15]}...)...")
                await envia_msg(page, MENSAGEM_2)
                supabase.table("prospecoes_chat").update({
                    "etapa_atual": 2,
                    "ultima_mensagem_enviada": MENSAGEM_2,
                    "data_ultimo_envio": datetime.now(timezone.utc).isoformat()
                }).eq("imovel_id", imovel_id).execute()
                # Atualizar Kanban para Script 3
                supabase.table("imoveis").update({"kanban_coluna_id": KANBAN_SCRIPT3_ID}).eq("id", imovel_id).execute()
                print("  ✅ Kanban atualizado -> Script 3")
            else:
                print(f"  -> Ainda não passou o tempo (Configurado: {delay_minutos_2}m / Passou: {minutos_passados:.1f}m). Pulando.")
                
        elif etapa_atual >= 2:
            print("  -> Drip completo (último followup já enviado). Aguardando resposta indefinidamente...")

    print("\n✅ Fim da varredura.")

if __name__ == "__main__":
    asyncio.run(monitorar())
    # Opcional: Descomente para fechar após a execução, mas o WS3 supõe janela aberta.
    # asyncio.run(close_chat_browser())
