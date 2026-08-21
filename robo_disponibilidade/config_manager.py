import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv, set_key

log = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent / "user_config.json"
ENV_FILE = Path(__file__).parent / ".env"

class ConfigManager:
    def __init__(self):
        load_dotenv(ENV_FILE)
        self.defaults = {
            "DELAY_ENTRE_ENVIOS": 60,
            "LIMITE_DIARIO": 30,
            "REMETENTE_NOME": "Samuel",
            "ADB_DELAY_ABERTURA": 3,
            "ADB_TAP_X": "980",
            "ADB_TAP_Y": "2163",
            "ADB_WHATSAPP_CALL_X": "902",
            "ADB_WHATSAPP_CALL_Y": "160",
            "ADB_DELAY_ABERTURA_CALL": 4,
            "ADB_SMS_SEND_X": "980",
            "ADB_SMS_SEND_Y": "2163",
            "SMS_LIMIT_DAILY": 50,
            "SMS_BATCH_SIZE": 10,
            "SMS_DELAY_MIN": 60,
            "SMS_DELAY_MAX": 180,
            "EVOLUTION_API_URL": "",
            "EVOLUTION_API_KEY": "",
            "EVOLUTION_INSTANCE": "",
            "EVOLUTION_INSTANCE_TOKEN": "",
            "GROQ_API_KEY": "",
            "GROQ_BASE_URL": "https://api.groq.com/openai/v1",
            "GROQ_MODEL": "llama-3.3-70b-versatile",
            "SUPABASE_URL": "",
            "SUPABASE_KEY": "",
            "TEMPLATE_WHATSAPP_DISP": "Olá {proprietario}, tudo bem?\n\n{remetente} aqui.\n\nQuero saber se seu imóvel de referência {referencia} está disponível?\n\nCaso esteja, houve alguma mudança no valor informado?\n\n{link}",
            "TEMPLATE_SMS_CAMPANHA": "Ola {proprietario}, aqui e {remetente}. Seu imovel {referencia} ainda esta disponivel? Me avise se o preco mudou. Obrigado!",
            "TEMPLATE_EMAIL_ASSUNTO": "Atualização de Disponibilidade - Imóvel {referencia}",
            "TEMPLATE_EMAIL_CORPO": "Olá {proprietario},\n\nTudo bem?\n\nGostaríamos de confirmar se o seu imóvel ({referencia}) ainda está disponível para venda/locação.\n\nCaso sim, houve alteração no valor?\n\nAtenciosamente,\n{remetente}",
            "TEMPLATE_WHATSAPP_CAMPANHA": "Olá {nome}, tudo bem? Vi seu interesse em imóveis na região. Podemos conversar?",
            "TEMPLATE_EMAIL_CAMPANHA_ASSUNTO": "Oportunidade Imobiliária para {nome}",
            "TEMPLATE_EMAIL_CAMPANHA_CORPO": "Olá {nome},\n\nTudo bem?\n\nVi que você tem interesse em imóveis e gostaria de apresentar algumas oportunidades.\n\nAtenciosamente,\n{remetente}",
            "BRASILIO_TOKEN": "",
            "ADB_WIFI_HOST": "",
            "GEMINI_API_KEY": "",
            "GEMINI_MODEL": "gemini-1.5-pro",
            "GEMINI_BASE_URL": "https://generativelanguage.googleapis.com/v1beta"
        }


    def get_all(self):
        """Retorna todas as configurações, priorizando o JSON, depois o ENV, depois os defaults."""
        config = self.defaults.copy()
        
        # 1. Tenta carregar do ENV
        for key in config.keys():
            val = os.getenv(key)
            if val is not None:
                config[key] = val

        # 2. Tenta carregar do JSON (Sobrepõe o que estiver no ENV)
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    json_config = json.load(f)
                    config.update(json_config)
            except Exception as e:
                log.error(f"Erro ao ler user_config.json: {e}")

        return config

    def save(self, new_config: dict, allow_extra: bool = False):
        """Salva as configurações no user_config.json."""
        if allow_extra:
            to_save = new_config
        else:
            to_save = {k: v for k, v in new_config.items() if k in self.defaults}

        # Preservar entradas existentes que não foram enviadas
        existing = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    existing = json.load(f)
            except Exception:
                pass
        existing.update(to_save)

        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(existing, f, indent=4)

            for k, v in to_save.items():
                os.environ[k] = str(v)

            log.info("Configurações salvas com sucesso em user_config.json")
            return True
        except Exception as e:
            log.error(f"Erro ao salvar configurações: {e}")
            return False

    def save_key(self, key: str, value: str):
        """Salva uma única chave de configuração, preservando as demais."""
        return self.save({key: value}, allow_extra=True)

# Instância única para uso no sistema
config_manager = ConfigManager()
