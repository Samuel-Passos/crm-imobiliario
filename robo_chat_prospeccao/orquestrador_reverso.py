import asyncio
import os
import sys
import argparse
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

# Adiciona o diretorio scraper ao path para importar tools
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scraper'))
from tools.chat_sender import send_chat_olx
from browser_manager_chat import start_chat_browser, close_chat_browser, get_chat_page

dotenv_path = os.path.join(os.path.dirname(__file__), "..", "scraper", ".env")
if not os.path.exists(dotenv_path):
    dotenv_path = os.path.join(os.path.dirname(__file__), "..", "olx_captacao", ".env")
load_dotenv(dotenv_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

KANBAN_IDS = {
    "SCRIPT_1": "934d8c3e-b887-482d-86ce-7fdeafe3101a",
    "SCRIPT_2": "3dd77415-d636-45c4-99e9-060cf2abc8e5",
    "SCRIPT_3": "b3f1f0b3-1a1b-4ab2-9907-c1bc51f8e1dc",
    "SEM_RESPOSTA": "b77b80a4-c122-4010-a795-3710c4f39d27",
    "EXTRACAO_TELEFONE": "9cfb9d98-89cb-4169-88e1-db399f3ce877",
    "CLIENTE_INTERAGIU": "47d38925-ac92-491e-bb69-0d38b23e4b80",
    "EXPIRADOS": "5f01efe9-6531-4259-9927-76c130e2851d",
}

async def extract_chat_state(page):
    state = await page.evaluate('''() => {
        const msgs = document.querySelectorAll('[data-testid="message-bubble"], [class*="message-bubble"], [class*="MessageBubble"]');
        if (msgs.length === 0) return {autor: 'desconhecido', texto: ''};
        
        const ultima = msgs[msgs.length - 1];
        const text = ultima.innerText.trim();
        const textLower = text.toLowerCase();
        
        if (textLower.includes("meu nome é samuel") || textLower === "oi" || textLower === "obrigado" || textLower.includes("corretor de imoveis")) {
            return {autor: 'usuario', texto: text};
        }
        
        const comp = window.getComputedStyle(ultima);
        const parentComp = window.getComputedStyle(ultima.parentElement);
        const html = ultima.outerHTML;
        
        if (comp.alignSelf === 'flex-end' || parentComp.justifyContent === 'flex-end') {
            return {autor: 'usuario', texto: text, html: html};
        } else if (comp.alignSelf === 'flex-start' || parentComp.justifyContent === 'flex-start') {
            return {autor: 'proprietario', texto: text, html: html};
        }

        const rect = ultima.getBoundingClientRect();
        const screenMid = window.innerWidth / 2;
        const msgMid = (rect.left + rect.right) / 2;
        
        if (msgMid > screenMid) {
            return {autor: 'usuario', texto: text, html: html};
        } else if (msgMid < screenMid) {
            return {autor: 'proprietario', texto: text, html: html};
        }
        
        return {autor: 'desconhecido', texto: text, html: html};
    }''')
    return state

async def envia_msg(page, texto: str, dry_run: bool):
    if dry_run:
        print(f"  [DRY-RUN] Simularia envio da mensagem: '{texto[:30]}...'")
        return

    xpath_input = '//*[@id="input-text-message"]'
    try:
        input_msg = page.locator(f"xpath={xpath_input}").first
        await input_msg.wait_for(state="visible", timeout=10000)
        
        await input_msg.fill(texto)
        await asyncio.sleep(0.5)
        await input_msg.press("Enter")
        await asyncio.sleep(1.0)
        print(f"  ✅ Mensagem enviada com sucesso!")
        return True
    except Exception as e:
        print(f"  ❌ Erro ao enviar mensagem: {e}")
        return False

async def processar_kanban(nome_kanban: str, col_id_atual: str, col_id_destino: str, template_tipo: str, 
                           templates_map: dict, page, dry_run: bool, limite_lote: int = None):
    print(f"\n" + "="*50)
    print(f"🔄 PROCESSANDO ONDA: {nome_kanban}")
    print("="*50)
    
    query = supabase.table("imoveis").select("id, list_id, titulo, url").eq("kanban_coluna_id", col_id_atual)
    if limite_lote:
        query = query.limit(limite_lote)
    res = query.execute()
    
    if not res.data:
        print(f"📭 Nenhum cartão encontrado no Kanban '{nome_kanban}'. Pulando para a próxima etapa.")
        return
        
    print(f"📋 Encontrados {len(res.data)} cartões na coluna.")
    
    template = templates_map.get(template_tipo)
    if not template:
        print(f"❌ Template '{template_tipo}' não encontrado no banco de dados! Abortando onda.")
        return
        
    corpo_msg = template.get("conteudo") or template.get("corpo", "")
    
    for imovel in res.data:
        imovel_id = imovel["id"]
        list_id = imovel["list_id"]
        titulo = imovel.get("titulo") or f"ID {imovel_id}"
        url = imovel.get("url")
        
        if not list_id:
            print(f"  ⚠️ Imóvel {imovel_id} sem list_id (OLX ID). Pulando.")
            continue
            
        print(f"\n🔎 Analisando: {titulo} (list_id {list_id})")
        
        sucesso_envio = False

        if nome_kanban == "Extração de Telefone":
            # Para a primeira mensagem, precisamos abrir a URL do anúncio e clicar no botão "Chat"
            if not url:
                print(f"  ❌ Sem URL do anúncio para primeira mensagem. Pulando.")
                continue
                
            print(f"  🌐 Iniciando fluxo de primeiro contato via URL do anúncio: {url}")
            if page and not dry_run:
                try:
                    res_envio = await send_chat_olx(url, corpo_msg, page)
                    if res_envio.get("enviado"):
                        print(f"  ✅ Primeiro contato enviado via botão do anúncio.")
                        sucesso_envio = True
                    else:
                        print(f"  ⚠️ Falha ao abrir chat ou anúncio indisponível. Motivo: {res_envio.get('erro', 'Desconhecido')}. Movendo para Expirados.")
                        supabase.table("imoveis").update({
                            "anuncio_expirado": True, 
                            "kanban_coluna_id": KANBAN_IDS["EXPIRADOS"]
                        }).eq("id", imovel_id).execute()
                except Exception as e:
                    print(f"  ❌ Erro na execução de send_chat_olx: {e}")
            else:
                print("  [DRY-RUN] Simulação: Primeiro contato enviado via botão do anúncio.")
                sucesso_envio = True
        else:
            # Para scripts seguintes, navegamos direto para o chat via list-id
            chat_url = f"https://chat.olx.com.br/?list-id={list_id}"
            print(f"  🌐 Navegando direto para o chat: {chat_url}")
            
            if page:
                try:
                    await page.goto(chat_url, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(4.0)
                except Exception as e:
                    print(f"  ❌ Erro ao abrir chat: {e}")
                    continue

                chat_state = await extract_chat_state(page)
                autor_ultima = chat_state["autor"]
                texto_ultima = chat_state["texto"]
                html_ultima = chat_state.get("html", "")
                print(f"  🗣️ Autor última msg: {autor_ultima} | Texto: '{texto_ultima[:30]}...'")
                print(f"  🔍 HTML da mensagem (DEBUG): {html_ultima[:200]}...") # Mostra o começo do HTML para análise
                
                if autor_ultima == "proprietario":
                    print("  🚨 CLIENTE INTERAGIU! Movendo para coluna 'Cliente Interagiu' e abortando scripts.")
                    if not dry_run:
                        supabase.table("imoveis").update({"kanban_coluna_id": KANBAN_IDS["CLIENTE_INTERAGIU"]}).eq("id", imovel_id).execute()
                    else:
                        print("  [DRY-RUN] Simulação: Moveu para Cliente Interagiu.")
                    continue
            
            # Se não interagiu, manda mensagem pelo histórico atual
            if nome_kanban == "Script 3":
                print(f"  -> Verificação final concluída. Movendo para 'Sem Resposta' sem enviar nova mensagem.")
                sucesso_envio = True
            else:
                print(f"  -> Preparando envio do template '{template_tipo}'")
                if page and not dry_run:
                    if await envia_msg(page, corpo_msg, dry_run):
                        sucesso_envio = True
                    else:
                        print(f"  ⚠️ Caixa de texto não abriu ou erro ao enviar. Movendo para Expirados.")
                        supabase.table("imoveis").update({
                            "anuncio_expirado": True, 
                            "kanban_coluna_id": KANBAN_IDS["EXPIRADOS"]
                        }).eq("id", imovel_id).execute()
                else:
                    print("  [DRY-RUN] Simulação: Mensagem de seguimento enviada.")
                    sucesso_envio = True

        if sucesso_envio:
            print(f"  ✅ Movendo Kanban para ID: {col_id_destino}")
            if not dry_run:
                try:
                    supabase.table("imoveis").update({"kanban_coluna_id": col_id_destino}).eq("id", imovel_id).execute()
                except Exception as e:
                    print(f"  ❌ Erro ao atualizar o banco: {e}")
            else:
                print("  [DRY-RUN] Simulação de mudança de coluna.")

async def onda_reversa(dry_run: bool = False, lote: int = 1):
    print("\n" + "#"*60)
    print("🌊 INICIANDO ORQUESTRADOR DE CHAT (ONDA REVERSA)")
    if dry_run:
         print("   ⚠️ MODO DRY-RUN: Nada será enviado ou alterado no banco!")
    print("#"*60 + "\n")
    
    resp_tmpl = supabase.table("templates_mensagem").select("*").order("ordem").execute()
    templates_list = resp_tmpl.data
    
    templates_map = {
        "passo_1": templates_list[0] if len(templates_list) > 0 else None,
        "passo_2": templates_list[1] if len(templates_list) > 1 else None,
        "passo_final": templates_list[2] if len(templates_list) > 2 else None,
    }
    
    key_msg1 = "passo_1"
    key_msg2 = "passo_2"
    key_msg3 = "passo_final"
    key_msg_final = "passo_final"
    
    page = None
    if not dry_run:
        await start_chat_browser()
        page = get_chat_page()
    else:
        try:
             await start_chat_browser()
             page = get_chat_page()
             print("   ✅ Browser iniciado no modo Dry-Run apenas para ler histórico.")
        except Exception as e:
             print("   ⚠️ Não foi possível iniciar browser no Dry-Run. Histórico será pulado.")
             page = None

    try:
        await processar_kanban("Script 3", KANBAN_IDS["SCRIPT_3"], KANBAN_IDS["SEM_RESPOSTA"], key_msg_final, templates_map, page, dry_run, limite_lote=lote)
        await processar_kanban("Script 2", KANBAN_IDS["SCRIPT_2"], KANBAN_IDS["SCRIPT_3"], key_msg3, templates_map, page, dry_run, limite_lote=lote)
        await processar_kanban("Script 1", KANBAN_IDS["SCRIPT_1"], KANBAN_IDS["SCRIPT_2"], key_msg2, templates_map, page, dry_run, limite_lote=lote)
        await processar_kanban("Extração de Telefone", KANBAN_IDS["EXTRACAO_TELEFONE"], KANBAN_IDS["SCRIPT_1"], key_msg1, templates_map, page, dry_run, limite_lote=lote)
    finally:
        if page:
             print("\nFechando navegador e limpando processos...")
             await close_chat_browser()
             
    print("\n✅ ONDA REVERSA FINALIZADA COM SUCESSO!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Simula sem enviar nem salvar")
    parser.add_argument("--lote", type=int, default=1, help="Lote maximo por coluna (default 1)")
    args = parser.parse_args()

    asyncio.run(onda_reversa(dry_run=args.dry_run, lote=args.lote))
