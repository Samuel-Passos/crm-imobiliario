import asyncio
import os
import sys
import datetime
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "olx_captacao"))
from supabase_client import supabase

sys.path.append(os.path.dirname(__file__))
from browser_manager_chat import start_chat_browser, close_chat_browser, get_chat_page

# Kanbans que devem ser monitorados pelo Scanner
KANBAN_IDS = {
    "SCRIPT_1": "38a9a6b4-4b53-41c1-8451-9ff81816bc82",
    "SCRIPT_2": "a40ab718-d7ee-4573-b3c6-993d052d0fa3",
    "SCRIPT_3": "7fb95393-2703-4ab2-b258-cf49fb67850a",
    "SEM_RESPOSTA": "8d3eab24-2c70-4f52-870a-ffbd6905c10a",
    "CLIENTE_INTERAGIU": "2edb516b-b3bb-4288-9fc3-a2f026a7605d"
}

async def scan_inbox(page, dry_run=False):
    print(f"[{datetime.datetime.now()}] 🔍 Iniciando Varredura do Inbox (Scanner)...")
    url = "https://chat.olx.com.br/"
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        # Espera dinâmica: aguarda até que o primeiro chat apareça (máx 15s)
        try:
            await page.wait_for_selector('a[data-testid="chat-list-item"]', timeout=15000)
        except Exception:
            print("⚠️ Timeout aguardando a lista de chats. Ou está vazia, ou a conexão está muito lenta.")
    except Exception as e:
        print(f"❌ Erro ao acessar o chat principal: {e}")
        return

    # Extrai os dados da barra lateral
    chats_recentes = await page.evaluate('''() => {
        const items = document.querySelectorAll('a[data-testid="chat-list-item"]');
        let results = [];
        for (let item of items) {
            let href = item.getAttribute("href") || "";
            let urlParams = new URLSearchParams(href.split('?')[1]);
            let listId = urlParams.get("list-id");
            
            if (listId) {
                // Se existe o label de status (Lida, Enviada), foi VOCÊ quem enviou a última mensagem.
                // Se NÃO existe, a última mensagem é do PROPRIETÁRIO.
                let statusLabel = item.querySelector('[data-testid="message-status-label"]');
                let ownerReplied = statusLabel === null;
                
                results.push({
                    list_id: listId,
                    owner_replied: ownerReplied,
                    texto: item.innerText.replace(/\\n/g, " | ")
                });
            }
        }
        return results;
    }''')
    
    if not chats_recentes:
        print("⚠️ Nenhum chat recente encontrado na tela.")
        return
        
    print(f"📋 Encontrados {len(chats_recentes)} chats recentes na tela principal.")
    
    # Prepara lista de IDs de Kanban permitidos
    colunas_permitidas = [
        KANBAN_IDS["SCRIPT_1"], 
        KANBAN_IDS["SCRIPT_2"], 
        KANBAN_IDS["SCRIPT_3"], 
        KANBAN_IDS["SEM_RESPOSTA"]
    ]
    
    # Processa cada chat retornado
    movidos = 0
    for chat in chats_recentes:
        list_id = chat["list_id"]
        
        # Só agimos se tivermos certeza que o proprietário respondeu (sem status de envio)
        if not chat["owner_replied"]:
            continue
            
        # Busca no banco de dados
        res = supabase.table("imoveis").select("id, kanban_coluna_id").eq("list_id", list_id).execute()
        if not res.data:
            continue
            
        imovel = res.data[0]
        id_banco = imovel["id"]
        coluna_atual = imovel["kanban_coluna_id"]
        
        # Verifica se está em uma das colunas que podem ser movidas
        if coluna_atual in colunas_permitidas:
            print(f"  🚨 [SCANNER] Resposta detectada no imóvel {list_id} (ID: {id_banco})!")
            print(f"      Trecho: {chat['texto'][:60]}...")
            if not dry_run:
                supabase.table("imoveis").update({"kanban_coluna_id": KANBAN_IDS["CLIENTE_INTERAGIU"]}).eq("id", id_banco).execute()
                print("      ✅ Movido para 'Cliente Interagiu'.")
            else:
                print("      [DRY-RUN] Simulação: Moveria para 'Cliente Interagiu'.")
            movidos += 1
            
    print(f"✅ Varredura concluída. {movidos} imóveis atualizados pelo Scanner.")

async def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("🛠️ MODO DRY-RUN: Nenhuma alteração será feita no Kanban.")
        
    await start_chat_browser()
    page = get_chat_page()
    
    if page:
        await scan_inbox(page, dry_run=dry_run)
        
    await close_chat_browser()

if __name__ == "__main__":
    asyncio.run(main())
