import os
from dotenv import load_dotenv
from supabase import create_client

def run_filtro_mercado():
    print("Iniciando Fase 2.5 - Filtro de Anúncios de Mercado...")
    
    # Configura Supabase
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    # Configurações dinâmicas
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scraper"))
    try:
        from config_db import get_config
        _cfg = get_config()
        lote_2_5 = _cfg.get("lote_fase2_5", 50)
    except:
        lote_2_5 = 50
    
    # Pega os IDs da Caixa de Entrada e da nova coluna Anúncios de Mercado
    res_colunas = sup.table('kanban_colunas').select('id, nome').execute()
    
    coluna_caixa_entrada = None
    coluna_anuncios_mercado = None
    
    for c in res_colunas.data:
        if c['nome'] == 'Caixa de Entrada':
            coluna_caixa_entrada = c['id']
        elif c['nome'] == 'Anúncios de Mercado':
            coluna_anuncios_mercado = c['id']
            
    if not coluna_caixa_entrada or not coluna_anuncios_mercado:
        print("Erro: Colunas Kanban não encontradas no banco de dados.")
        return
        
    print(f"Buscando imóveis na Caixa de Entrada (Lote: {lote_2_5})...")
    
    # Busca apenas na Caixa de Entrada, agora incluindo a cidade
    res_imoveis = sup.table('imoveis').select('id, titulo, vendedor_nome, descricao, anuncio_profissional, cidade').eq('kanban_coluna_id', coluna_caixa_entrada).limit(lote_2_5).execute()
    imoveis = res_imoveis.data
    
    if not imoveis:
        print("Nenhum imóvel para filtrar na Caixa de Entrada.")
        return
        
    prof_keywords_nome = ['creci', 'imóvei', 'imovei', 'imobiliari', 'imobiliári', 'corretor', 'consultor', 'negocio', 'negócio']
    prof_keywords_desc = ['creci', 'código do anúncio']
    
    movidos = 0
    
    for im in imoveis:
        im_id = im['id']
        
        # Passo NOVO: Filtro de Cidade (Apenas São José dos Campos)
        cidade = (im.get('cidade') or '').strip().lower()
        # Aceita "são josé dos campos", "sao jose dos campos", etc.
        if "são josé dos campos" not in cidade and "sao jose dos campos" not in cidade:
            print(f"[{im_id}] Bloqueado: Cidade diferente de São José dos Campos ({cidade}). Movendo.")
            sup.table('imoveis').update({'kanban_coluna_id': coluna_anuncios_mercado}).eq('id', im_id).execute()
            movidos += 1
            continue
            
        print(f"[{im_id}] ✅ Cidade validada: {cidade.title()}")
        
        # Passo B (primeiro, conforme seu pedido): É profissional pela OLX?
        if im.get('anuncio_profissional') == True:
            print(f"[{im_id}] Marcado pela OLX como Profissional. Movendo para Anúncios de Mercado.")
            sup.table('imoveis').update({'kanban_coluna_id': coluna_anuncios_mercado}).eq('id', im_id).execute()
            movidos += 1
            continue
            
        # Passo A: Dedução
        nome = (im.get('vendedor_nome') or '').lower()
        desc = (im.get('descricao') or '').lower()
        is_pro = False
        
        for kw in prof_keywords_nome:
            if kw in nome:
                is_pro = True
                break
                
        if not is_pro:
            for kw in prof_keywords_desc:
                if kw in desc:
                    is_pro = True
                    break
                    
        if is_pro:
            print(f"[{im_id}] Deduzido como profissional por palavras-chave. Atualizando e movendo.")
            try:
                # Atualiza a coluna de dedução e move
                sup.table('imoveis').update({
                    'anuncio_profissional_deduzido': True,
                    'kanban_coluna_id': coluna_anuncios_mercado
                }).eq('id', im_id).execute()
                movidos += 1
            except Exception as e:
                print(f"Erro ao atualizar imovel {im_id}. Verifique se a coluna 'anuncio_profissional_deduzido' existe no banco.")

    print(f"Fase 2.5 Finalizada! {movidos} imóveis transferidos para o Kanban Anúncios de Mercado.")

if __name__ == "__main__":
    run_filtro_mercado()
