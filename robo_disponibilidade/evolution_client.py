"""
evolution_client.py
───────────────────
Wrapper para a Evolution API v2.
Documentação: https://doc.evolution-api.com
"""

import os
import logging
import httpx
from pathlib import Path
from config_manager import config_manager

log = logging.getLogger(__name__)


def _normalizar_telefone(tel: str) -> str:
    """Retorna apenas dígitos, com DDI 55 no início."""
    digitos = "".join(c for c in tel if c.isdigit())
    # Remove zeros à esquerda (ex: 0012...)
    digitos = digitos.lstrip("0")
    # Garante DDI 55
    if not digitos.startswith("55"):
        digitos = "55" + digitos
    return digitos


class EvolutionClient:
    def __init__(self):
        config = config_manager.get_all()
        self.base_url = (config.get("EVOLUTION_API_URL") or os.getenv("EVOLUTION_API_URL", "")).rstrip("/")
        self.api_key  = config.get("EVOLUTION_API_KEY") or os.getenv("EVOLUTION_API_KEY", "")
        self.instance = config.get("EVOLUTION_INSTANCE") or os.getenv("EVOLUTION_INSTANCE", "n8n")
        self.headers  = {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }

    # ── Enviar mensagem de texto ──────────────────────────────────────
    def send_text(self, telefone: str, texto: str, delay_ms: int = 1500) -> dict:
        numero = _normalizar_telefone(telefone)
        url = f"{self.base_url}/message/sendText/{self.instance}"
        payload = {
            "number": numero,
            "text": texto,
            "delay": delay_ms,
        }
        log.info(f"[Evolution] Enviando para {numero}:\n{texto}\n{'─'*40}")
        resp = httpx.post(url, json=payload, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ── Enviar Mídia (Imagem, Vídeo, Documento) ──────────────────────
    def send_media(self, telefone: str, media_url: str, mediatype: str = 'image', caption: str = '', filename: str = 'arquivo') -> dict:
        """
        Envia mídia via Evolution API. 
        mediatype: 'image', 'video' ou 'document'
        """
        numero = _normalizar_telefone(telefone)
        url = f"{self.base_url}/message/sendMedia/{self.instance}"
        
        # Mapeamento simples de extensões se necessário
        if media_url.endswith('.pdf'):
            mediatype = 'document'
        
        payload = {
            "number": numero,
            "mediatype": mediatype,
            "media": media_url,
            "caption": caption,
            "fileName": filename
        }
        
        log.info(f"[Evolution] Enviando Mídia ({mediatype}) para {numero}. URL: {media_url}")
        resp = httpx.post(url, json=payload, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ── Configurar webhook na instância ──────────────────────────────
    def configurar_webhook(self, webhook_url: str) -> dict:
        """
        Registra a URL de webhook na instância da Evolution API (v2).
        """
        url = f"{self.base_url}/webhook/set/{self.instance}"
        payload = {
            "webhook": {
                "enabled": True,
                "url": webhook_url,
                "webhookByEvents": False,
                "webhookBase64": False,
                "events": ["MESSAGES_UPSERT"],
            }
        }
        log.info(f"[Evolution] Configurando webhook → {url}")
        resp = httpx.post(url, json=payload, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ── Verificar status da instância ────────────────────────────────
    def status_instancia(self) -> dict:
        url = f"{self.base_url}/instance/fetchInstances"
        resp = httpx.get(url, headers=self.headers, timeout=15)
        resp.raise_for_status()
        instancias = resp.json()
        # Filtra a instância configurada
        for inst in (instancias if isinstance(instancias, list) else []):
            if inst.get("instance", {}).get("instanceName") == self.instance:
                return inst
        return {}
