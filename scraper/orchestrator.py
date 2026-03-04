import sys
from pathlib import Path
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import json
import time

# Carrega ferramentas do scraper
from tools.search_tools import (
    buscar_imoveis_para_extrair_telefone,
)
from tools.phone_extractor import extract_phones_from_olx
import tools.browser_manager as browser_manager

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Sinais de controle global
STOP_SIGNAL = False
PAUSE_SIGNAL = False
IS_RUNNING = False

async def check_pause():
    """Aguarda enquanto o sinal de pausa estiver ativo."""
    while PAUSE_SIGNAL:
        await asyncio.sleep(1)

# ==========================================
# 1. FLUXO DE EXTRAÇÃO DE TELEFONES
# ==========================================
async def extract_phone_single_lead(imovel_id: int):
    """Extrai telefone de 1 único imóvel e atualiza o BD.
    Se a API foi bloqueada pelo Cloudflare, NÃO marca como processado
    para que o link fique na fila e seja tentado novamente.
    """
    print(f"\n[ORQUESTRADOR] Iniciando extração do imóvel {imovel_id}")
    
    # Busca a URL do banco
    res = supabase.table("imoveis").select("url").eq("id", imovel_id).execute()
    if not res.data:
        print(f"❌ Imóvel {imovel_id} não encontrado.")
        return {"bloqueado": False, "telefones": [], "erro": "Imovel nao encontrado"}
        
    url = res.data[0]["url"]
    
    # Pega o contexto global do browser
    page = browser_manager.get_page()
    lock = browser_manager.get_lock()
    if not page:
        print("❌ [ORQUESTRADOR] Página global do browser não encontrada!")
        return {"bloqueado": False, "telefones": [], "erro": "Browser não iniciado"}
        
    # Roda a ferramenta de IA/Browser
    async with lock:
        resultado = await extract_phones_from_olx(url, page)
    
    # Se foi bloqueado pelo Cloudflare, NÃO atualiza o banco
    # O link permanece com telefone_pesquisado=false e volta à fila
    if resultado.get("bloqueado", False):
        print(f"🚫 [ORQUESTRADOR] Imóvel {imovel_id} BLOQUEADO — não será marcado como processado.")
        return resultado
    
    # Atualiza o Banco
    telefones_array = resultado.get("telefones", [])
    
    # Atualiza o Banco imoveis
    update_data = {
        "telefone_pesquisado": True,
        "anuncio_expirado": resultado.get("expirado", False),
        "telefones_extraidos": telefones_array
    }
    
    # Integração Kanban: Move para "Expirados" se a URL retornar erro ou offline (404/Inativa).
    if resultado.get("expirado", False):
        update_data["kanban_coluna_id"] = "5f01efe9-6531-4259-9927-76c130e2851d"
    else:
        # Move para a coluna "Extração de Telefone" já que foi concluída a tentativa (passou pelo scraper e não é inativo)
        update_data["kanban_coluna_id"] = "9cfb9d98-89cb-4169-88e1-db399f3ce877"
    
    # Se achamos pelo menos 1 contato, salvamos o principal no campo 'telefone' para o Kanban renderizar fácil
    if telefones_array and len(telefones_array) > 0:
        primeiro_telefone = telefones_array[0].get("telefone")
        if primeiro_telefone:
            update_data["telefone"] = primeiro_telefone
    
    supabase.table("imoveis").update(update_data).eq("id", imovel_id).execute()
    
    # Atualiza a tabela links_anuncios se estiver expirado
    if resultado.get("expirado", False):
        supabase.table("links_anuncios").update({"status": "expirado"}).eq("url", url).execute()

    print(f"✅ Banco atualizado para imóvel {imovel_id}!")
    return resultado

async def process_batch_phone_extraction():
    """Busca em lote todos os pendentes e extrai os telefones 1 a 1."""
    imoveis = buscar_imoveis_para_extrair_telefone()
    total_leads = len(imoveis)
    print(f"\n[LOTE EXTRAÇÃO] {total_leads} imóveis aguardando varredura.")
    
    if total_leads == 0:
        return

    # Cria registro de estatística inicial
    res_stats = supabase.table("estatisticas_scraper").insert({
        "leads_processados": 0
    }).execute()
    stats_id = res_stats.data[0]["id"] if res_stats.data else None

    # Contadores locais
    count_proc = 0
    count_exp = 0
    count_sem = 0
    count_com = 0
    via_botao = 0
    via_desc = 0
    erros = 0
    bloqueios_consecutivos = 0  # Anti-bot: para após 3 bloqueios seguidos

    try:
        for imovel in imoveis:
            if STOP_SIGNAL:
                print("\n🛑 [LOTE EXTRAÇÃO] Parada solicitada pelo usuário.")
                break
            
            await check_pause()
            
            try:
                start_lead = time.time()
                resultado = await extract_phone_single_lead(imovel["id"])
                duration_lead = int(time.time() - start_lead)
                
                # ── Anti-bot: detecta bloqueio Cloudflare ────────────
                if resultado and resultado.get("bloqueado", False):
                    bloqueios_consecutivos += 1
                    print(f"  🚫 Bloqueio {bloqueios_consecutivos}/3 (imóvel {imovel['id']} ficará na fila)")
                    
                    if bloqueios_consecutivos >= 3:
                        print("\n🛑 [LOTE EXTRAÇÃO] SCRAPER PARADO: Cloudflare bloqueou 3 links consecutivos.")
                        print("   Links bloqueados permanecem na fila para próxima execução.")
                        
                        # Registra o bloqueio no log
                        if stats_id:
                            supabase.table("logs_detalhados_scraper").insert({
                                "estatistica_id": stats_id,
                                "imovel_id": imovel["id"],
                                "url": imovel.get("url"),
                                "com_telefone": False,
                                "origem_telefone": None,
                                "expirado": False,
                                "erro": "Cloudflare bloqueou 3x consecutivas — scraper parado",
                                "duracao_segundos": duration_lead
                            }).execute()
                        break  # PARA o ciclo
                    
                    # Registra log do bloqueio individual e continua
                    if stats_id:
                        supabase.table("logs_detalhados_scraper").insert({
                            "estatistica_id": stats_id,
                            "imovel_id": imovel["id"],
                            "url": imovel.get("url"),
                            "com_telefone": False,
                            "origem_telefone": None,
                            "expirado": False,
                            "erro": f"Cloudflare bloqueou (tentativa {bloqueios_consecutivos}/3)",
                            "duracao_segundos": duration_lead
                        }).execute()
                    continue  # Pula para próximo link
                
                # Sucesso (sem bloqueio) — zera o contador
                bloqueios_consecutivos = 0
                count_proc += 1
                
                has_error = bool(resultado.get("erro"))
                is_exp = bool(resultado.get("expirado"))
                tels = resultado.get("telefones", [])
                has_tel = len(tels) > 0
                
                origem = None
                if has_tel:
                    origens_list = [t.get("origem") for t in tels]
                    if "botão" in origens_list or "botao" in origens_list:
                        via_botao += 1
                        origem = "botao"
                    if "descrição" in origens_list or "descricao" in origens_list:
                        via_desc += 1
                        origem = "descricao" if not origem else "ambos"

                if has_error:
                    erros += 1
                elif is_exp:
                    count_exp += 1
                elif not has_tel:
                    count_sem += 1
                else:
                    count_com += 1
                
                # Insere LOG DETALHADO
                if stats_id:
                    supabase.table("logs_detalhados_scraper").insert({
                        "estatistica_id": stats_id,
                        "imovel_id": imovel["id"],
                        "url": imovel.get("url"),
                        "com_telefone": has_tel,
                        "origem_telefone": origem,
                        "expirado": is_exp,
                        "erro": resultado.get("erro") if has_error else None,
                        "duracao_segundos": duration_lead
                    }).execute()

                    # Atualiza resumo
                    supabase.table("estatisticas_scraper").update({
                        "leads_processados": count_proc,
                        "leads_expirados": count_exp,
                        "leads_sem_telefone": count_sem,
                        "leads_com_telefone": count_com,
                        "encontrados_via_botao": via_botao,
                        "encontrados_via_descricao": via_desc,
                        "erros": erros
                    }).eq("id", stats_id).execute()

            except Exception as e:
                print(f"❌ Erro crítico no loop de extração: {e}")
                erros += 1
            
            await asyncio.sleep(5)  # Pausa humana

    finally:
        # Finaliza o registro
        if stats_id:
            supabase.table("estatisticas_scraper").update({
                "data_fim": "now()"
            }).eq("id", stats_id).execute()


# Chat prospecting functionality removed – now handled by separate message_bot service
# ==========================================
# 3. ROTINA MESTRA (CRON)
# ==========================================
async def run_daily_scraper_cycle():
    """
    Acordado diariamente (ou manualmente pelo admin).
    """
    print("="*50)
    print("🚀 INICIANDO CICLO DIÁRIO DE SCRAPING E PROSPECÇÃO")
    print("="*50)
    
    global IS_RUNNING
    IS_RUNNING = True
    try:
        # 1. Busca novos dados (Telefones)
        await process_batch_phone_extraction()
        
        # (Chat prospecting moved to message_bot service)
    finally:
        IS_RUNNING = False
        print("\n🏁 CICLO FINALIZADO!")


if __name__ == "__main__":
    # Teste unitário direto
    asyncio.run(run_daily_scraper_cycle())
