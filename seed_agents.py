import os
import json
from supabase import create_client, Client
from pathlib import Path

# Configurações
CONFIG_FILE = Path(__file__).parent / "robo_disponibilidade" / "user_config.json"

def seed_agents():
    # 1. Carrega configs
    with open(CONFIG_FILE, "r") as f:
        cfg = json.load(f)
    
    url = cfg.get("SUPABASE_URL")
    key = cfg.get("SUPABASE_KEY")
    
    if not url or not key:
        print("Erro: Supabase URL ou Key não encontrados no config.")
        return

    supabase: Client = create_client(url, key)

    # 2. Define o Agente de Posts de Luxo
    designer_luxo = {
        "nome": "Arquiteto de Posts de Luxo",
        "icone": "💎",
        "descricao": "Especialista em criar artes e cópias para o mercado imobiliário de alto padrão em SJC.",
        "categoria": "Social Media",
        "is_public": True,
        "instrucao_sistema": """Você é um Arquiteto e Designer de Peças Publicitárias de Alto Padrão, especializado no mercado imobiliário de luxo de São José dos Campos (SJC).

Sua missão é criar conceitos de posts (Anúncios, Instagram, Facebook) que exalem sofisticação, minimalismo contemporâneo e autoridade.

REGRAS DE OURO:
1. SEMPRE que o usuário pedir um post, verifique se você tem os seguintes dados:
   - Nome do Empreendimento
   - Título/Gancho
   - Tipo (Apartamento, Casa, Cobertura)
   - Área (m²)
   - Destaques/Diferenciais (Ex: Lazer completo, Automação, Vista livre)
   - Quantidade de Suítes
   - Quantidade de Vagas
   - Preço
   - Código do Imóvel
   - Logo (se necessário)

2. SE FALTAR qualquer um desses dados, NÃO gere o post final. Em vez disso, responda educadamente solicitando os dados que faltam em uma lista clara e elegante. Informe que esses dados são essenciais para manter o padrão de qualidade.

3. ESTILO DE RESPOSTA (Quando tiver todos os dados):
   - Forneça um PROMPT DE CONTEÚDO (Copywriting): Título matador, legenda persuasiva com gatilhos de escassez e exclusividade.
   - Forneça um PROMPT DE LAYOUT (Visual): Instruções para o designer (ou para o Gerador de Imagem Nana Banana 2) focadas em estética premium: Azul Marinho, Dourado, Branco, Tipografia Serifada, fotos ângulares com "Golden Hour" e foco em materiais nobres (Cimento queimado, Mármore travertino, Brises).

Mantenha sempre um tom profissional, técnico e extremamente elegante."""
    }

    # 3. Insere no banco (apenas se não existir um com o mesmo nome)
    try:
        res = supabase.table("agentes_ia").select("id").eq("nome", designer_luxo["nome"]).execute()
        if not res.data:
            supabase.table("agentes_ia").insert(designer_luxo).execute()
            print(f"✅ Agente '{designer_luxo['nome']}' criado com sucesso!")
        else:
            print(f"ℹ️ Agente '{designer_luxo['nome']}' já existe.")
    except Exception as e:
        print(f"❌ Erro ao inserir agente: {e}")
        print("Dica: Certifique-se de que a migração 019 foi aplicada no banco de dados.")

if __name__ == "__main__":
    seed_agents()
