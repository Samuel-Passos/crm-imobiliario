import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import List, Dict, Any
from datetime import datetime, timezone

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
# IMPORTANTE: Para o scraper, usamos a chave de SERVICE ROLE para ignorar o RLS e poder escrever à vontade
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("⚠️ Credenciais do Supabase ausentes no .env!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def buscar_imoveis_para_extrair_telefone() -> List[Dict[str, Any]]:
    """
    Busca imóveis que:
    1. Ainda não tiveram tentativa de extração (telefone_pesquisado = false)
    2. Não estão expirados (anuncio_expirado = false)
    3. Estão na "Caixa de Entrada" OU foram recém "Processados" pelo scraper antigo
    
    Retorna apenas os IDs e URLs para não pesar a memória.
    """
    try:
        # Busca ID da coluna Kanban "Caixa de Entrada"
        res_coluna = supabase.table("kanban_colunas").select("id").eq("nome", "Caixa de Entrada").execute()
        if not res_coluna.data:
            print("⚠️ Coluna 'Caixa de Entrada' não encontrada no banco!")
            return []
            
        caixa_entrada_id = res_coluna.data[0]["id"]
        
        # Faz a query na tabela imoveis
        # Nota: O filtro "OU status_processado em links_anuncios" exigiria um JOIN mais complexo,
        # mas como criamos uma Trigger (migration 004) que joga todo "Processado" automaticamente 
        # para a Caixa de Entrada, só precisamos olhar para o kanban_coluna_id! 💡
        # Prioridade 1: Os que TEM botão de telefone (telefone_existe = True). 
        # Prioridade 2: Os mais recentes inseridos no BD.
        imoveis = supabase.table("imoveis") \
            .select("id, titulo, url, telefone_existe") \
            .eq("telefone_pesquisado", False) \
            .eq("anuncio_expirado", False) \
            .eq("kanban_coluna_id", caixa_entrada_id) \
            .order("telefone_existe", desc=True, nullsfirst=False) \
            .order("id", desc=True) \
            .execute()
            
        return imoveis.data
        
    except Exception as e:
        print(f"🚨 Erro ao buscar imóveis para extração: {e}")
        return []

def buscar_imoveis_para_prospeccao_inicial() -> List[Dict[str, Any]]:
    """
    Busca imóveis que JÁ FORAM pesquisados, têm telefones extraídos 
    e AINDA NÃO têm registro de prospecção iniciada.
    """
    try:
        # Primeiro, pegamos todos os imóveis pesquisados e que tenham telefones
        # Usamos uma query de jsonb_array_length > 0 para garantir que há contatos
        imoveis = supabase.table("imoveis") \
            .select("id, url, telefones_extraidos") \
            .eq("telefone_pesquisado", True) \
            .eq("anuncio_expirado", False) \
            .filter("telefones_extraidos", "neq", "[]") \
            .execute()
            
        if not imoveis.data:
            return []
            
        resultados = []
        for imovel in imoveis.data:
            # Verifica se já existe prospecção ativa para este imóvel
            prospeccao = supabase.table("prospecoes_chat") \
                .select("id") \
                .eq("imovel_id", imovel["id"]) \
                .execute()
                
            if not prospeccao.data:
                # Se não tem prospecção, é um lead quente!
                resultados.append(imovel)
                
        return resultados
        
    except Exception as e:
        print(f"🚨 Erro ao buscar leads novos: {e}")
        return []

def buscar_prospeccoes_pendentes_dia() -> List[Dict[str, Any]]:
    """
    Busca as prospecções que aguardam resposta, cuja última mensagem 
    foi enviada ANTES DE HOJE (precisam de follow-up ou check de resposta).
    """
    try:
        hoje = datetime.now(timezone.utc).date()
        
        prospeccoes = supabase.table("prospecoes_chat") \
            .select("*, imoveis(url)") \
            .eq("status", "aguardando_resposta") \
            .execute()
            
        # Filtra via Python os que foram enviados antes de hoje (para agir 1 dia depois)
        # Se quiser mais rápido/agressivo, pode mudar a lógica de tempo
        pendentes_hoje = []
        for p in prospeccoes.data:
            data_envio_iso = p.get("data_ultimo_envio")
            if not data_envio_iso: continue
            
            # Formato ISO 8601: "2024-03-20T14:30:00+00:00"
            dt_envio = datetime.fromisoformat(data_envio_iso.replace('Z', '+00:00'))
            if dt_envio.date() < hoje:
                pendentes_hoje.append(p)
                
        return pendentes_hoje
        
    except Exception as e:
        print(f"🚨 Erro ao buscar follow-ups: {e}")
        return []

if __name__ == "__main__":
    print("\n🔍 Testando busca de imóveis sem telefone...")
    res = buscar_imoveis_para_extrair_telefone()
    print(f"Encontrados: {len(res)}")
    print(res[:2])
