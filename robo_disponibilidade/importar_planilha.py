"""
=============================================================================
ETAPA 2 — Importação da Planilha para o Supabase
=============================================================================
Descrição:
  Lê a planilha .xlsx exportada do sistema da imobiliária e faz upsert
  na tabela `atualizacao_disponibilidade` no Supabase.

  Regras de upsert:
  - Se o imóvel (referencia) NÃO existe → INSERE com todos os campos.
  - Se o imóvel JÁ existe → ATUALIZA apenas os campos da planilha
    (referencia, proprietario, telefone, preco, status).
    As colunas de controle do robô (ultimo_contato, resposta,
    data_resposta, proximo_contato) são PRESERVADAS se já tiverem valor.

Uso:
  python importar_planilha.py --arquivo caminho/para/planilha.xlsx

  Ou coloque o nome do arquivo em PLANILHA_DEFAULT abaixo e rode sem args.
=============================================================================
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes e configuração padrão
# ---------------------------------------------------------------------------

# Nome padrão da planilha (pode ser sobrescrito via --arquivo)
PLANILHA_DEFAULT = "imoveis.xlsx"

# Nome da tabela no Supabase
TABELA = "atualizacao_disponibilidade"

# Mapeamento: coluna da planilha → coluna da tabela
MAPEAMENTO_COLUNAS = {
    "Referencia":              "referencia",
    "Proprietário":            "proprietario",
    "Celular do Proprietário": "telefone",
    "Preço":                   "preco",
    "Status":                  "status",
}

# Colunas de controle do robô que NÃO devem ser sobrescritas em updates
COLUNAS_CONTROLE = {
    "ultimo_contato",
    "resposta",
    "data_resposta",
    "proximo_contato",
}

# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def carregar_credenciais() -> tuple[str, str]:
    """
    Carrega SUPABASE_URL e SUPABASE_KEY do arquivo .env
    que fica na mesma pasta deste script.
    """
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        log.error(
            "SUPABASE_URL e/ou SUPABASE_KEY não encontradas no .env.\n"
            "Verifique o arquivo .env na pasta do script."
        )
        sys.exit(1)

    log.info("Credenciais do Supabase carregadas com sucesso.")
    return url, key


def ler_planilha(caminho: str) -> pd.DataFrame:
    """
    Lê a planilha .xlsx e retorna um DataFrame com as colunas
    mapeadas para o padrão do banco.
    """
    caminho = Path(caminho)
    if not caminho.exists():
        log.error(f"Arquivo não encontrado: {caminho}")
        sys.exit(1)

    log.info(f"Lendo planilha: {caminho}")
    df = pd.read_excel(caminho, dtype=str)  # dtype=str evita conversões automáticas

    # Verifica se as colunas obrigatórias existem
    colunas_faltando = set(MAPEAMENTO_COLUNAS.keys()) - set(df.columns)
    if colunas_faltando:
        log.error(
            f"Colunas ausentes na planilha: {colunas_faltando}\n"
            f"Colunas encontradas: {list(df.columns)}"
        )
        sys.exit(1)

    # Seleciona apenas as colunas mapeadas e renomeia
    df = df[list(MAPEAMENTO_COLUNAS.keys())].rename(columns=MAPEAMENTO_COLUNAS)

    # Limpa espaços em branco e substitui NaN/nan por None
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
    df = df.where(pd.notna(df), other=None)

    # Remove linhas sem referencia (obrigatória como chave primária)
    antes = len(df)
    df = df[df["referencia"].notna() & (df["referencia"] != "")]
    depois = len(df)
    if antes != depois:
        log.warning(f"{antes - depois} linha(s) ignorada(s) por não ter 'referencia' válida.")

    log.info(f"Total de registros lidos da planilha: {len(df)}")
    return df


def buscar_registros_existentes(supabase: Client) -> dict[str, dict]:
    """
    Busca todos os registros existentes na tabela.
    Retorna um dicionário { referencia: registro_completo }.
    
    Faz paginação para suportar tabelas grandes (limite padrão do Supabase = 1000).
    """
    log.info("Buscando registros existentes no Supabase...")
    existentes = {}
    pagina = 0
    tamanho_pagina = 1000

    while True:
        inicio = pagina * tamanho_pagina
        fim = inicio + tamanho_pagina - 1

        resultado = (
            supabase.table(TABELA)
            .select("referencia, ultimo_contato, resposta, data_resposta, proximo_contato")
            .range(inicio, fim)
            .execute()
        )

        dados = resultado.data
        if not dados:
            break

        for registro in dados:
            existentes[registro["referencia"]] = registro

        if len(dados) < tamanho_pagina:
            break  # última página

        pagina += 1

    log.info(f"Registros existentes no banco: {len(existentes)}")
    return existentes


def formatar_linha(linha: pd.Series, existente: dict | None) -> dict:
    """
    Converte uma linha do DataFrame em um dicionário pronto para upsert.

    Se o registro JÁ existe, mantém os valores de controle do robô
    que já estiverem preenchidos (não sobrescreve com NULL).
    """
    payload = linha.to_dict()

    if existente:
        # Preserva colunas de controle se já tiverem valor
        for col in COLUNAS_CONTROLE:
            valor_banco = existente.get(col)
            if valor_banco is not None:
                payload[col] = valor_banco  # mantém o valor existente
            # Se for None no banco, omite do payload para não enviar NULL desnecessário

    return payload


def importar(supabase: Client, df: pd.DataFrame, existentes: dict) -> dict:
    """
    Faz o upsert de cada registro e retorna um resumo das operações.
    """
    resumo = {"inseridos": 0, "atualizados": 0, "ignorados": 0, "erros": 0}

    for _, linha in df.iterrows():
        referencia = linha["referencia"]
        existente = existentes.get(referencia)

        payload = formatar_linha(linha, existente)

        try:
            # upsert: on_conflict="referencia" garante insert ou update pela PK
            supabase.table(TABELA).upsert(
                payload,
                on_conflict="referencia"
            ).execute()

            if existente:
                resumo["atualizados"] += 1
                log.debug(f"[ATUALIZADO] {referencia}")
            else:
                resumo["inseridos"] += 1
                log.debug(f"[INSERIDO]   {referencia}")

        except Exception as e:
            resumo["erros"] += 1
            log.error(f"[ERRO] Referência {referencia}: {e}")

    return resumo


def imprimir_resumo(resumo: dict, total: int) -> None:
    """Imprime o resumo final da importação."""
    largura = 52
    linha = "=" * largura
    print(f"\n{linha}")
    print("  RESUMO DA IMPORTAÇÃO — ETAPA 2")
    print(linha)
    print(f"  Total lido da planilha : {total:>6}")
    print(f"  Registros inseridos    : {resumo['inseridos']:>6}  ✅")
    print(f"  Registros atualizados  : {resumo['atualizados']:>6}  🔄")
    print(f"  Ignorados (sem ref.)   : {resumo['ignorados']:>6}  ⚠️")
    print(f"  Erros                  : {resumo['erros']:>6}  ❌")
    print(f"{linha}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Importa planilha .xlsx para a tabela atualizacao_disponibilidade no Supabase."
    )
    parser.add_argument(
        "--arquivo",
        default=PLANILHA_DEFAULT,
        help=f"Caminho para a planilha .xlsx (padrão: {PLANILHA_DEFAULT})",
    )
    args = parser.parse_args()

    print("\n🏠 Robô de Disponibilidade — Etapa 2: Importação de Planilha")
    print(f"   Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

    # 1. Credenciais
    url, key = carregar_credenciais()

    # 2. Conexão com o Supabase
    supabase: Client = create_client(url, key)
    log.info("Conectado ao Supabase.")

    # 3. Leitura da planilha
    df = ler_planilha(args.arquivo)
    total_lidos = len(df)

    # 4. Registros existentes no banco (para lógica de preservação)
    existentes = buscar_registros_existentes(supabase)

    # 5. Upsert
    log.info("Iniciando importação...")
    resumo = importar(supabase, df, existentes)

    # 6. Resumo final
    imprimir_resumo(resumo, total_lidos)


if __name__ == "__main__":
    main()
