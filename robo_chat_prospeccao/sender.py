import asyncio
import os
import random
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

from browser_manager_chat import start_chat_browser, close_chat_browser, get_chat_page

dotenv_path = os.path.join(os.path.dirname(__file__), "..", "scraper", ".env")
load_dotenv(dotenv_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

KANBAN_SCRIPT1_ID = "934d8c3e-b887-482d-86ce-7fdeafe3101a"

async def envia_msg(page, texto: str):
    """ Cola o texto no input e manda Enter (muito mais rápido que digitar). """
    xpath_input = '//*[@id="input-text-message"]'
    input_msg = page.locator(f"xpath={xpath_input}").first
    await input_msg.wait_for(state="visible", timeout=10000)
    
    await input_msg.fill(texto)
    await asyncio.sleep(0.5)
    await input_msg.press("Enter")
    await asyncio.sleep(1.0)
    print(f"  ✅ Mensagem enviada com sucesso! ({len(texto)} chars)")

async def process_batch_chat_sending():
    """
    Novo Sender Isolado (Substitui o velho do orchestrator).
    Lê o limite, o delay, os templates e envia a primeira mensagem.
    Move o Kanban para Script 1.
    """
    print("="*50)
    print("📤 INICIANDO LOTE DE ENVIO DA 1ª MENSAGEM (SENDER ISOLADO)")
    print("="*50)

    try:
        # 1. Lê Configurações do Banco
        max_chats_dia = 40
        delay_chats = 60
        try:
            conf = supabase.table("configuracoes_ia").select("max_chats_dia, delay_entre_chats").limit(1).execute()
            if conf.data:
                max_chats_dia = conf.data[0].get("max_chats_dia", 40)
                delay_chats = conf.data[0].get("delay_entre_chats") or 60
        except Exception as e:
            print(f"  ⚠️ Erro ao ler configuracoes_ia: {e}. Usando max={max_chats_dia}, delay={delay_chats}s")

        print(f"  📊 Limite diário: {max_chats_dia} chats")
        print(f"  ⏳ Delay entre chats: {delay_chats} segundos")

        # 2. Verifica quantos já foram enviados hoje
        hoje = datetime.now(timezone.utc).date().isoformat()
        resp_hoje = supabase.table("prospecoes_chat").select("id", count="exact").gte("data_primeiro_envio", hoje).execute()
        chats_hoje = resp_hoje.count or 0
        print(f"  📊 Chats enviados hoje: {chats_hoje}/{max_chats_dia}")

        if chats_hoje >= max_chats_dia:
            print("  ⛔ Limite diário atingido. Abortando sender.")
            return

        # 3. Pega a Mensagem Inicial do Banco
        resp_tmpl = supabase.table("templates_mensagem").select("corpo").eq("tipo", "inicial").eq("ativo", True).order("criado_em", desc=False).limit(1).execute()
        if not resp_tmpl.data:
            print("  ❌ Nenhum template 'inicial' ativo! Cadastre na tela de Automações.")
            return
        mensagem_inicial = resp_tmpl.data[0]["corpo"]

        # 4. Busca Imóveis Elegíveis
        # Elegível = telefone já pesquisado E não tem registro em prospecoes_chat
        # Vamos usar a mesma lógica nativa do Supabase
        imoveis_raw = supabase.table("imoveis").select("id, url, list_id, titulo").eq("telefone_pesquisado", True).execute()
        
        # Filtra os que NÃO estão em prospecoes_chat
        prospecoes_ativas = supabase.table("prospecoes_chat").select("imovel_id").execute()
        set_prospecoes = {p["imovel_id"] for p in prospecoes_ativas.data}
        
        elegiveis = [im for im in imoveis_raw.data if im["id"] not in set_prospecoes and im.get("list_id")]
        
        print(f"  🎯 Imóveis elegíveis (telefone_pesquisado=True, sem prospeccao): {len(elegiveis)}")

        if not elegiveis:
            print("  ✅ Nenhum imóvel pendente de chat na fila. Finalizando.")
            return

        # 5. Inicia o Navegador (Workspace 3)
        await start_chat_browser()
        page = get_chat_page()

        count_ok = 0
        
        for imovel in elegiveis:
            if chats_hoje + count_ok >= max_chats_dia:
                print(f"  ⛔ Limite de {max_chats_dia} chats/dia atingido. Parando lote.")
                break

            imovel_id = imovel["id"]
            list_id = imovel["list_id"]
            print(f"\n  [{count_ok + 1}] Processando imovel_id={imovel_id} | list_id={list_id}")

            chat_url = f"https://chat.olx.com.br/?list-id={list_id}"
            
            try:
                # Acessa diretamente a URL do chat e manda a msg
                await page.goto(chat_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(4.0) # Espera renderizar o chat
                
                await envia_msg(page, mensagem_inicial)
                
                # Salva no banco de dados na nova estrutura!
                supabase.table("prospecoes_chat").upsert({
                    "imovel_id": imovel_id,
                    "status": "aguardando_resposta",
                    "etapa_atual": 0,
                    "ultima_mensagem_enviada": mensagem_inicial,
                    "data_primeiro_envio": datetime.now(timezone.utc).isoformat(),
                    "data_ultimo_envio": datetime.now(timezone.utc).isoformat()
                }).execute()
                
                # Move Kanban para "Script 1"
                supabase.table("imoveis").update({
                    "kanban_coluna_id": KANBAN_SCRIPT1_ID
                }).eq("id", imovel_id).execute()
                print(f"  ✅ Kanban atualizado -> Script 1")
                
                count_ok += 1
                
                # Espera o tempo configurado (ex: 60s) antes do próximo
                print(f"  ⏳ Aguardando {delay_chats}s (configurado no CRM) antes do próximo envio...")
                await asyncio.sleep(delay_chats)

            except Exception as e:
                print(f"  🚨 Falha no envio para imovel_id={imovel_id}: {e}")
                # Marca como erro para não tentar de novo infinitamente
                supabase.table("prospecoes_chat").upsert({
                    "imovel_id": imovel_id,
                    "status": "erro",
                    "etapa_atual": 0
                }).execute()

        print(f"\n✅ LOTE SENDER FINALIZADO! {count_ok} enviados.")

    except Exception as e:
        print(f"Erro fatal no sender: {e}")
        
if __name__ == "__main__":
    asyncio.run(process_batch_chat_sending())
