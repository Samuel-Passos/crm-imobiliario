"""
webhook_handler.py
──────────────────
Processa os webhooks recebidos da Evolution API (MESSAGES_UPSERT).
Encontra o imóvel correspondente, chama a IA para analisar a resposta
e toma a ação devida (atualizar banco e/ou enviar nova mensagem).

Estrutura real do payload da Evolution API v2:
{
  "event": "messages.upsert",
  "data": {
    "key": {
      "remoteJid": "5512981959588@s.whatsapp.net",
      "fromMe": false,
      "id": "..."
    },
    "pushName": "Nome do contato",
    "messageType": "conversation",
    "message": {
      "conversation": "texto da mensagem aqui"
    },
    "messageTimestamp": 1234567890
  }
}
"""

import os
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from evolution_client import EvolutionClient
from ia_analyzer import analisar_resposta
import templates

load_dotenv(Path(__file__).parent / ".env")
log = logging.getLogger(__name__)

supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", ""),
)
evo = EvolutionClient()
TABELA = "atualizacao_disponibilidade"

def _formatar_tel_banco(tel_evol: str) -> str:
    """Extrai apenas os números para buscar no banco.
    tel_evol costuma vir como '5512981959588@s.whatsapp.net'
    O banco guarda como '12981959588' (sem DDI 55).
    """
    num = tel_evol.split("@")[0]
    # Remove DDI 55 se presente, pois a planilha guarda só com DDD+número
    if num.startswith("55") and len(num) > 11:
        return num[2:]
    return num


async def processar_evento_mensagem(payload: dict):
    """
    Função principal que recebe o body do webhook da Evolution API v2.
    """
    try:
        data = payload.get("data", {})

        # ── Lê a chave da mensagem (key) ────────────────────────────────
        key = data.get("key", {})

        # Ignora mensagens enviadas pelo próprio bot (fromMe)
        if key.get("fromMe"):
            log.info("[Webhook] Ignorando mensagem fromMe.")
            return

        remetente_jid = key.get("remoteJid", "")
        if not remetente_jid:
            log.warning("[Webhook] remoteJid ausente no payload.")
            return

        # Ignora mensagens de grupo
        if "g.us" in remetente_jid:
            log.info("[Webhook] Ignorando mensagem de grupo.")
            return

        # ── Lê o tipo e texto da mensagem ────────────────────────────────
        msg_type = data.get("messageType", "")
        message  = data.get("message", {})

        # Só processa mensagens de texto
        if msg_type not in ("conversation", "extendedTextMessage"):
            log.info(f"[Webhook] Tipo de mensagem ignorado: {msg_type}")
            return

        texto = ""
        if msg_type == "conversation":
            texto = message.get("conversation", "")
        elif msg_type == "extendedTextMessage":
            texto = message.get("extendedTextMessage", {}).get("text", "")

        texto = texto.strip()
        if not texto:
            log.info("[Webhook] Mensagem sem texto — ignorando.")
            return

        telefone_banco = _formatar_tel_banco(remetente_jid)
        push_name = data.get("pushName", "")
        log.info(f"[Webhook] ✉️  De {push_name} ({telefone_banco}): {texto[:80]}")

        # ── Busca o imóvel aguardando resposta para este telefone ────────
        resultado = (
            supabase.table(TABELA)
            .select("*")
            .ilike("telefone", f"%{telefone_banco}%")
            .is_("resposta", "null")
            .not_.is_("ultimo_contato", "null")
            .order("ultimo_contato", desc=True)
            .limit(1)
            .execute()
        )

        if not resultado.data:
            log.info(f"[Webhook] Nenhum imóvel aguardando resposta para {telefone_banco}")
            return

        imovel = resultado.data[0]
        ref  = imovel["referencia"]
        prop = imovel.get("proprietario") or "Proprietário"

        # ── Analisa com a IA ─────────────────────────────────────────────
        log.info(f"[Webhook] Analisando resposta para imóvel {ref}...")
        analise       = analisar_resposta(texto, ref, prop)
        acao          = analise.get("acao")
        novo_preco    = analise.get("preco")
        msg_followup  = analise.get("mensagem_resposta")

        log.info(f"[Webhook] 🤖 Decisão da IA: {acao}")

        agora = datetime.now(timezone.utc).isoformat()

        # ── Executa a ação ───────────────────────────────────────────────
        if acao == "SIM":
            supabase.table(TABELA).update({
                "resposta":      "SIM",
                "data_resposta": agora,
            }).eq("referencia", ref).execute()
            evo.send_text(remetente_jid, templates.mensagem_confirmacao_sim(ref))
            log.info(f"[Webhook] ✅ {ref} marcado como DISPONÍVEL.")

        elif acao == "NOVO_PRECO":
            update_data = {"resposta": "SIM", "data_resposta": agora}
            if novo_preco:
                update_data["preco"] = novo_preco
            supabase.table(TABELA).update(update_data).eq("referencia", ref).execute()
            evo.send_text(remetente_jid, templates.mensagem_agradecimento_preco(ref, novo_preco or "informado"))
            log.info(f"[Webhook] ✅ {ref} marcado com NOVO PREÇO: {novo_preco}.")

        elif acao == "NÃO":
            supabase.table(TABELA).update({
                "resposta":      "NÃO",
                "data_resposta": agora,
            }).eq("referencia", ref).execute()
            evo.send_text(remetente_jid, templates.mensagem_confirmacao_nao(ref))
            log.info(f"[Webhook] ❌ {ref} marcado como INDISPONÍVEL.")

        elif acao == "CONTINUAR" and msg_followup:
            supabase.table(TABELA).update({
                "ultimo_contato": agora,
            }).eq("referencia", ref).execute()
            evo.send_text(remetente_jid, msg_followup)
            log.info(f"[Webhook] 🔄 {ref} — enviado follow-up.")

        else:
            log.warning(f"[Webhook] Ação desconhecida da IA: {acao}")

    except KeyError as e:
        log.error(f"[Webhook] Campo ausente no payload: {e}. Payload: {payload}")
    except Exception as e:
        log.error(f"[Webhook] Erro ao processar evento: {e}", exc_info=True)
