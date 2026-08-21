"""
ia_analyzer.py
──────────────
Usa o Groq LLM para interpretar a resposta do proprietário
e classificar a disponibilidade do imóvel.

Retorna um dict com:
  - acao: "SIM" | "NÃO" | "NOVO_PRECO" | "CONTINUAR"
  - preco: str | None  (novo preço informado pelo proprietário)
  - mensagem_resposta: str | None  (mensagem de follow-up se precisar)
"""

import os
import json
import re
import logging
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
from config_manager import config_manager

log = logging.getLogger(__name__)

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        config = config_manager.get_all()
        _client = Groq(
            api_key=config.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"),
            base_url=config.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        )
    return _client


SYSTEM_PROMPT = """Você é um assistente especializado em interpretar respostas de proprietários de imóveis.

Sua tarefa: analisar a mensagem do proprietário e classificar a situação do imóvel.

Retorne SOMENTE um JSON válido, sem texto adicional, no formato abaixo:
{
  "acao": "SIM" | "NÃO" | "NOVO_PRECO" | "CONTINUAR",
  "preco": "valor mencionado ou null",
  "mensagem_resposta": "mensagem de follow-up para o proprietário ou null"
}

Regras de classificação:
- "SIM"         → proprietário confirmou que o imóvel está disponível (sem mencionar novo preço)
- "NÃO"         → imóvel foi vendido, alugado, retirado do mercado ou proprietário disse que não está disponível
- "NOVO_PRECO"  → confirmou disponível E informou um novo valor (ex: "sim, mas o preço mudou para 450mil")
- "CONTINUAR"   → resposta vaga, inconclusiva, fora de contexto ou que requer mais informação

Para "CONTINUAR": escreva em mensagem_resposta uma pergunta gentil e direta para obter a confirmação.
Para "SIM", "NÃO" e "NOVO_PRECO": mensagem_resposta deve ser null (a mensagem de resposta é gerada pelo sistema).

Seja tolerante com erros de escrita, abreviações e linguagem informal.
Exemplos de SIM: "tá disponível", "sim sr", "pode anunciar", "continua sim", "disponível"
Exemplos de NÃO: "vendeu", "já aluguei", "não tô mais vendendo", "retirei do mercado"
Exemplos de NOVO_PRECO: "sim, mas agora é 500k", "tá disponível, mudou pra 350.000"
"""


def analisar_resposta(
    mensagem_proprietario: str,
    referencia: str,
    proprietario: str,
) -> dict:
    """
    Analisa a resposta do proprietário usando o Groq.
    Retorna dict com chaves: acao, preco, mensagem_resposta.
    """
    prompt_usuario = (
        f"Proprietário: {proprietario}\n"
        f"Referência do imóvel: {referencia}\n"
        f"Mensagem do proprietário: \"{mensagem_proprietario}\""
    )

    try:
        client = _get_client()
        config = config_manager.get_all()
        response = client.chat.completions.create(
            model=config.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt_usuario},
            ],
            temperature=0.1,
            max_tokens=256,
        )

        content = response.choices[0].message.content.strip()
        log.debug(f"[IA] Resposta raw: {content}")

        # Extrai JSON (às vezes o modelo envolve em markdown)
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            resultado = json.loads(match.group())
        else:
            resultado = json.loads(content)

        # Valida campos obrigatórios
        if "acao" not in resultado:
            raise ValueError("Campo 'acao' ausente na resposta da IA")

        return resultado

    except Exception as e:
        log.error(f"[IA] Erro ao analisar resposta: {e}")
        # Fallback seguro: pede confirmação ao proprietário
        return {
            "acao": "CONTINUAR",
            "preco": None,
            "mensagem_resposta": (
                f"Olá! Desculpe, não entendi muito bem. 😅\n\n"
                f"Poderia confirmar: o imóvel de referência *{referencia}* "
                f"ainda está disponível? Responda *SIM* ou *NÃO*. Obrigado! 🙏"
            ),
        }


# ── Teste rápido ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "sim, continua disponível mas o preço mudou pra 480mil"
    resultado = analisar_resposta(msg, "SAMAP26", "Guilherme Oliveira")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
