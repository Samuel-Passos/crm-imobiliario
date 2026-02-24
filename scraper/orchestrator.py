import sys
from pathlib import Path
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Carrega ferramentas do scraper
from tools.search_tools import (
    buscar_imoveis_para_extrair_telefone,
    buscar_imoveis_para_prospeccao_inicial,
    buscar_prospeccoes_pendentes_dia
)
from tools.phone_extractor import extract_phones_from_olx
from tools.chat_sender import send_chat_message_olx
from tools.chat_reader import read_latest_chat_reply

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# ==========================================
# 1. FLUXO DE EXTRAÇÃO DE TELEFONES
# ==========================================
async def extract_phone_single_lead(imovel_id: int):
    """Extrai telefone de 1 único imóvel e atualiza o BD."""
    print(f"\n[ORQUESTRADOR] Iniciando extração do imóvel {imovel_id}")
    
    # Busca a URL do banco
    res = supabase.table("imoveis").select("url").eq("id", imovel_id).execute()
    if not res.data:
        print(f"❌ Imóvel {imovel_id} não encontrado.")
        return
        
    url = res.data[0]["url"]
    
    # Roda a ferramenta de IA/Browser
    resultado = await extract_phones_from_olx(url)
    
    # Atualiza o Banco
    telefones_array = resultado.get("telefones", [])
    
    # Atualiza o Banco imoveis
    update_data = {
        "telefone_pesquisado": True,
        "anuncio_expirado": resultado.get("expirado", False),
        "telefones_extraidos": telefones_array
    }
    
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

async def process_batch_phone_extraction():
    """Busca em lote todos os pendentes e extrai os telefones 1 a 1."""
    imoveis = buscar_imoveis_para_extrair_telefone()
    print(f"\n[LOTE EXTRAÇÃO] {len(imoveis)} imóveis aguardando varredura.")
    
    # Roda sequencial p/ não sobrecarregar PC e contornar detecção de bot
    for imovel in imoveis:
        # AQUI - Importante capturar a data para tratar corretamente na query async
        await extract_phone_single_lead(imovel["id"])
        await asyncio.sleep(5)  # Pausa humana


# ==========================================
# 2. FLUXO DE PROSPECÇÃO (CHAT)
# ==========================================

async def get_config_and_templates():
    config = supabase.table("configuracoes_ia").select("*").single().execute().data
    templates = supabase.table("templates_mensagem").select("*").order("ordem").execute().data
    return config, templates

async def prospect_single_lead(imovel_id: int):
    """
    Inicia uma prospecção quente. Envia o primeiro contato (passo 1).
    Ainda usaremos a arquitetura de URL Direta, mas o primeiro acesso 
    TEM QUE SER na página do anúncio. 
    """
    print(f"\n[ORQUESTRADOR] Iniciando chat para imóvel {imovel_id}")
    
    # Configs
    config, templates = await get_config_and_templates()
    tema_inicial = next((t for t in templates if t["ordem"] == 1), None)
    
    if not tema_inicial:
        print("❌ Nenhum template ordem = 1 configurado!")
        return
        
    # No futuro, aqui teríamos uma chamada LM intermediária (LangChain)
    # que juntaria 'config.prompt_personalidade' + 'tema_inicial.conteudo' e geraria o texto exato.
    # Por hora, para garantir funcionamento de ponta a ponta, usaremos o conteúdo cru do template base.
    mensagem_final = tema_inicial["conteudo"]
    
    # Pega URL do imóvel
    res = supabase.table("imoveis").select("url").eq("id", imovel_id).execute()
    if not res.data: return
    url = res.data[0]["url"]
    
    # Roda envio (No frontend BrowserUse ele tem ir na pagina, achar chat e enviar)
    res_chat = await send_chat_message_olx(url, mensagem_final)
    
    if res_chat.get("sucesso"):
        # Se foi o 1º contato (ainda não tinha url_chat guardada), a URL do inbox não pegamos perfeitamente 
        # Daqui o Agent Browser Use futuramente pode capturar a document.location.href.
        # Por hora, apenas inserimos na tabela de controle
        supabase.table("prospecoes_chat").insert({
            "imovel_id": imovel_id,
            "status": "aguardando_resposta",
            "etapa_atual": 1,
            "ultima_mensagem_enviada": mensagem_final,
            "data_ultimo_envio": "now()"
        }).execute()
        print(f"✅ Inserida prospecção para {imovel_id} no banco.")
    else:
        print(f"❌ Erro ao enviar primeia mensagem: {res_chat.get('motivo')}")

async def process_batch_first_prospects():
    """Pega os imóveis com telefone, sem chat e manda o template 1"""
    leads = buscar_imoveis_para_prospeccao_inicial()
    print(f"\n[LOTE INIT CHAT] {len(leads)} novos leads prontos para prospecção.")
    
    for lead in leads:
        await prospect_single_lead(lead["id"])
        await asyncio.sleep(8)


async def process_batch_follow_ups():
    """Lê os chats esperando resposta e avança pro passo 2/3."""
    pendentes = buscar_prospeccoes_pendentes_dia()
    print(f"\n[LOTE FOLLOW-UP] {len(pendentes)} conversas pendentes para hoje.")
    
    config, templates = await get_config_and_templates()
    
    for prospeccao in pendentes:
        p_id = prospeccao["id"]
        imovel_url = prospeccao["imoveis"]["url"]
        
        # 1. Lê a resposta usando a URL original do imovel (se não tiver a url direta do chat)
        res_leitura = await read_latest_chat_reply(imovel_url)
        
        if res_leitura.get("respondeu"):
            texto = res_leitura.get("texto_resposta")
            # 2. Atualiza banco
            supabase.table("prospecoes_chat").update({
                "status": "respondeu",
                "ultima_resposta_proprietario": texto,
                "data_ultima_resposta": "now()"
            }).eq("id", p_id).execute()
            print(f"✅ Resposta lida! Parando sequência para bot/humano assumir.")
            
        else:
            # 3. Não respondeu: Envia próximo passo
            print("⏳ Sem resposta. Buscando próximo template...")
            etapa_seguinte = prospeccao["etapa_atual"] + 1
            template_prox = next((t for t in templates if t["ordem"] == etapa_seguinte), None)
            
            if not template_prox:
                print("🛑 Sequência terminou (sem mais templates). Encerrando conversa.")
                supabase.table("prospecoes_chat").update({"status": "encerrado"}).eq("id", p_id).execute()
                continue
                
            msg = template_prox["conteudo"]
            res_envio = await send_chat_message_olx(imovel_url, msg)
            
            if res_envio.get("sucesso"):
                supabase.table("prospecoes_chat").update({
                    "etapa_atual": etapa_seguinte,
                    "ultima_mensagem_enviada": msg,
                    "data_ultimo_envio": "now()"
                }).eq("id", p_id).execute()
        
        await asyncio.sleep(8)

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
    
    # 1. Busca novos dados (Telefones)
    await process_batch_phone_extraction()
    
    # 2. Inicia conversas novas
    await process_batch_first_prospects()
    
    # 3. Dá manutenção nas conversas ativas
    # await process_batch_follow_ups()  # TODO Habilitar após testes das 2 primeiras
    
    print("\n🏁 CICLO FINALIZADO!")

if __name__ == "__main__":
    # Teste unitário direto
    asyncio.run(run_daily_scraper_cycle())
