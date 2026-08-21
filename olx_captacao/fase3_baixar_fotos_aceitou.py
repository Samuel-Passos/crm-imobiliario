#!/usr/bin/env python3
# =============================================================================
# fase3_baixar_fotos_aceitou.py
# Robô em background que baixa e hospeda fotos de imóveis na fase 'Aceitou'
# =============================================================================

import time
import httpx
import traceback
from supabase_client import supabase

BUCKET_NAME = "imoveis_fotos"

def obter_id_coluna_aceitou():
    try:
        res = supabase.table("kanban_colunas").select("id").eq("nome", "Aceitou").execute()
        if res.data:
            return res.data[0]["id"]
    except Exception as e:
        print(f"Erro ao buscar coluna Aceitou: {e}")
    return None

def baixar_e_fazer_upload(list_id: str, url_olx: str, index: int) -> str:
    """Baixa a imagem da OLX e faz upload para o Supabase Storage. Retorna a URL pública."""
    try:
        # Limpar possiveis querystrings que reduzem a qualidade
        url_limpa = url_olx.split('?')[0] if '?' in url_olx else url_olx
        
        with httpx.Client() as client:
            resposta = client.get(url_limpa, timeout=15.0)
            resposta.raise_for_status()
        
        caminho_storage = f"{list_id}/foto_{index}.jpg"
        
        # Tenta fazer upload (se falhar porque já existe, pegamos a URL pública de qualquer forma ou damos update)
        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                file=resposta.content,
                path=caminho_storage,
                file_options={"content-type": "image/jpeg", "x-upsert": "true"}
            )
        except Exception as upload_err:
            print(f"  Aviso no upload (talvez já exista): {upload_err}")
            
        url_publica = supabase.storage.from_(BUCKET_NAME).get_public_url(caminho_storage)
        return url_publica
        
    except Exception as e:
        print(f"  ❌ Erro ao baixar/upload foto {index} do list_id {list_id}: {e}")
        return url_olx # Fallback: retorna a URL original se falhar

def processar_imoveis_aceitos(coluna_id: str):
    try:
        res = (
            supabase.table("imoveis")
            .select("id, list_id, fotos, foto_capa, titulo")
            .eq("kanban_coluna_id", coluna_id)
            .eq("fotos_baixadas", False)
            .execute()
        )
        
        imoveis = res.data or []
        
        for imovel in imoveis:
            list_id = imovel["list_id"]
            titulo_alt = imovel.get("titulo", "Imóvel")
            fotos_originais = imovel.get("fotos", [])
            
            print(f"🔄 Processando imóvel {list_id} ({len(fotos_originais)} fotos)...")
            
            if not isinstance(fotos_originais, list) or len(fotos_originais) == 0:
                print(f"  Nenhuma foto encontrada para {list_id}. Marcando como baixado.")
                supabase.table("imoveis").update({"fotos_baixadas": True}).eq("id", imovel["id"]).execute()
                continue
                
            novas_fotos = []
            nova_foto_capa = None
            
            for idx, foto_dict in enumerate(fotos_originais):
                url_original = foto_dict.get("url") or foto_dict.get("original")
                if not url_original:
                    continue
                    
                print(f"  ⬇️  Baixando foto {idx+1}/{len(fotos_originais)}...")
                url_storage = baixar_e_fazer_upload(list_id, url_original, idx)
                
                novas_fotos.append({
                    "url": url_storage,
                    "alt": titulo_alt
                })
                
                if idx == 0:
                    nova_foto_capa = url_storage
                    
            print(f"  ✅ Upload concluído. Atualizando banco de dados...")
            
            # Atualizar no banco
            supabase.table("imoveis").update({
                "fotos_originais_olx": fotos_originais,
                "fotos": novas_fotos,
                "foto_capa": nova_foto_capa,
                "fotos_baixadas": True
            }).eq("id", imovel["id"]).execute()
            
            print(f"  ✅ Imóvel {list_id} atualizado com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro na rotina de processamento: {e}")
        traceback.print_exc()

def main():
    print("🤖 Robô de Download de Fotos iniciado. Aguardando imóveis na coluna 'Aceitou'...")
    coluna_aceitou_id = None
    
    while True:
        try:
            if not coluna_aceitou_id:
                coluna_aceitou_id = obter_id_coluna_aceitou()
            
            if coluna_aceitou_id:
                processar_imoveis_aceitos(coluna_aceitou_id)
            else:
                print("⚠️ Coluna 'Aceitou' não encontrada no Kanban. Tentando novamente em 30s...")
                
        except Exception as e:
            print(f"Erro no loop principal: {e}")
            
        time.sleep(15) # Verifica a cada 15 segundos

if __name__ == "__main__":
    main()
