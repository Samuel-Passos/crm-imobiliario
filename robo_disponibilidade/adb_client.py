import os
import time
import urllib.parse
import subprocess
import logging
import shlex
from dotenv import load_dotenv
from pathlib import Path
from config_manager import config_manager

log = logging.getLogger(__name__)


class AdbClient:
    def __init__(self):
        log.info("AdbClient inicializado.")

    def _get_serial(self) -> str | None:
        """
        Retorna o serial do melhor dispositivo disponível.
        Prioridade: Wi-Fi (IP:porta) > USB (serial alfanumérico).
        Retorna None se nenhum dispositivo estiver conectado.
        """
        try:
            res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
            linhas = res.stdout.strip().split('\n')[1:]  # Ignora o cabeçalho
            dispositivos = [l.split()[0] for l in linhas if l.strip() and "device" in l and "offline" not in l]
            if not dispositivos:
                return None
            # Prefere dispositivo Wi-Fi (contém ':')
            wifi = [d for d in dispositivos if ':' in d]
            return wifi[0] if wifi else dispositivos[0]
        except Exception:
            return None

    def _adb(self, args: list, timeout: int = 15) -> subprocess.CompletedProcess:
        """Executa um comando ADB no dispositivo selecionado automaticamente."""
        serial = self._get_serial()
        cmd = ["adb"] + (['-s', serial] if serial else []) + args
        log.debug(f"[ADB] cmd: {' '.join(cmd)}")
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def send_text(self, phone: str, text: str):
        """
        Abre o WhatsApp no celular físico via ADB com mensagem pré-preenchida.
        O usuário só precisa tocar em Enviar (ou as coordenadas enviam automaticamente).
        """
        self.verificar_conexao()

        # ── 1. Formatar número ────────────────────────────────────────────────
        numero = ''.join(filter(str.isdigit, phone))
        if not numero.startswith("55"):
            numero = "55" + numero
        log.info(f"[ADB] Preparando envio para {numero}...")

        # ── 2. Codificar texto (safe='' garante que ' " & etc. virem %XX) ────
        text_encoded = urllib.parse.quote(text, safe='')

        # ── 3. Abrir conversa no WhatsApp via Intent ──────────────────────────
        # Usamos android.intent.action.VIEW com URI whatsapp://send para suportar
        # tanto WhatsApp normal (com.whatsapp) quanto Business (com.whatsapp.w4b).
        # A codificação garante que caracteres especiais funcionem no bash.
        intent_url = f"whatsapp://send?phone={numero}&text={text_encoded}"
        shell_cmd = f"am start -a android.intent.action.VIEW -d '{intent_url}'"

        log.info(f"[ADB] Disparando intent WhatsApp...")
        try:
            res = self._adb(["shell", shell_cmd], timeout=20)
            saida = (res.stdout + res.stderr).strip()
            log.info(f"[ADB] Resposta intent: {saida or '(sem saída)'}")

            # ADB pode retornar código 0 mas ainda indicar erro no texto
            if res.returncode != 0 or "error" in saida.lower():
                raise RuntimeError(f"Intent falhou: {saida}")

        except subprocess.TimeoutExpired:
            log.error("[ADB] Timeout ao abrir WhatsApp (>20s)")
            raise
        except Exception as e:
            log.error(f"[ADB] Erro na intent: {e}")
            raise

        # ── 4. Aguardar o WhatsApp abrir ──────────────────────────────────────
        config = config_manager.get_all()
        delay_abertura = int(config.get("ADB_DELAY_ABERTURA", 3))
        log.info(f"[ADB] Aguardando {delay_abertura}s para o app carregar...")
        time.sleep(delay_abertura)

        # ── 5. Tocar no botão Enviar ──────────────────────────────────────────
        tap_x = str(config.get("ADB_TAP_X", "")).strip()
        tap_y = str(config.get("ADB_TAP_Y", "")).strip()

        try:
            if tap_x and tap_y:
                log.info(f"[ADB] Tocando em ({tap_x}, {tap_y})...")
                res = self._adb(["shell", "input", "tap", tap_x, tap_y], timeout=10)
                saida_toque = (res.stdout + res.stderr).strip()
                
                if "SecurityException" in saida_toque or "INJECT_EVENTS" in saida_toque:
                    msg_erro = (
                        "Permissão negada pelo Android para simular toques. "
                        "Se você usa Xiaomi/POCO, vá nas Opções de Desenvolvedor "
                        "e ative a opção 'Depuração USB (Configurações de segurança)'."
                    )
                    log.error(f"[ADB] ERRO CRÍTICO DE PERMISSÃO: {msg_erro}")
                    raise RuntimeError(msg_erro)
                
                log.info(f"[ADB] Toque: {saida_toque or 'OK'}")
            else:
                log.info("[ADB] Sem coordenadas X/Y. Tentando TAB + ENTER...")
                self._adb(["shell", "input", "keyevent", "61"], timeout=5)   # TAB
                time.sleep(0.4)
                self._adb(["shell", "input", "keyevent", "66"], timeout=5)   # ENTER
        except subprocess.TimeoutExpired:
            log.error("[ADB] Timeout ao simular toque no Enviar")
            raise

        log.info(f"[ADB] ✅ Envio finalizado para {numero}.")

    def send_sms(self, phone: str, text: str):
        """
        Envia mensagem via SMS (Mensagens do sistema) via ADB.
        Fluxo: Abre a intent de SMS -> Aguarda -> Toca no botão Enviar.
        """
        self.verificar_conexao()
        
        # 1. Formatar número
        numero = ''.join(filter(str.isdigit, phone))
        log.info(f"[ADB] Preparando SMS para {numero}...")

        # 2. Abrir Intent de SMS
        # Usamos shlex.quote para garantir que a mensagem não quebre o terminal
        msg_quoted = shlex.quote(text)
        shell_cmd = f"am start -a android.intent.action.SENDTO -d sms:{numero} --es sms_body {msg_quoted}"
        
        try:
            res = self._adb(["shell", shell_cmd], timeout=15)
            log.info(f"[ADB] Resposta intent SMS: {(res.stdout + res.stderr).strip() or 'OK'}")
        except Exception as e:
            log.error(f"[ADB] Erro ao abrir intent SMS: {e}")
            raise

        # 3. Aguardar o app de SMS abrir
        config = config_manager.get_all()
        delay = int(config.get("ADB_DELAY_ABERTURA", 3))
        time.sleep(delay)

        # 4. Tocar no botão Enviar do SMS
        tap_x = str(config.get("ADB_SMS_SEND_X", "")).strip()
        tap_y = str(config.get("ADB_SMS_SEND_Y", "")).strip()

        try:
            if tap_x and tap_y:
                log.info(f"[ADB] Tocando em Enviar SMS ({tap_x}, {tap_y})...")
                self._adb(["shell", "input", "tap", tap_x, tap_y], timeout=10)
            else:
                log.warning("[ADB] Coordenadas ADB_SMS_SEND_X/Y não configuradas. Tentando Enter...")
                self._adb(["shell", "input", "keyevent", "66"], timeout=5) # Enter
        except Exception as e:
            log.error(f"[ADB] Erro ao tocar no enviar: {e}")
            raise

        log.info(f"[ADB] ✅ SMS disparado para {numero}.")

    def verificar_conexao(self):
        """Verifica se há pelo menos um dispositivo conectado e online."""
        try:
            res = self._adb(["devices"])
            linhas = res.stdout.strip().split('\n')
            # A primeira linha é "List of devices attached", as demais são os devices filtrados
            dispositivos = [l for l in linhas[1:] if "device" in l and "offline" not in l]
            if not dispositivos:
                raise RuntimeError("Nenhum dispositivo Android encontrado ou autorizado. Verifique a conexão Wi-Fi/USB.")
            return True
        except Exception as e:
            log.error(f"[ADB] Erro ao verificar conexão: {e}")
            raise

    def abrir_discador(self, phone: str):
        """
        Abre o discador do Android com o número pré-preenchido.
        Usa action.DIAL (não requer permissão CALL_PHONE, compatível com Android 12+).
        O usuário confirma a chamada na tela do celular.
        """
        self.verificar_conexao()
        
        numero = ''.join(filter(str.isdigit, phone))
        log.info(f"[ADB] Abrindo discador para {numero}...")

        # action.DIAL abre o discador com número pré-preenchido, sem precisar de
        # android.permission.CALL_PHONE (que é bloqueado pelo Android 12+ via ADB shell).
        shell_cmd = f"am start -a android.intent.action.DIAL -d tel:{numero}"
        try:
            res = self._adb(["shell", shell_cmd], timeout=10)
            saida = (res.stdout + res.stderr).strip()
            log.info(f"[ADB] Discador aberto: {saida or 'OK'}")
            if "exception" in saida.lower() or "error" in saida.lower():
                raise RuntimeError(f"Falha ao abrir discador: {saida}")
        except Exception as e:
            log.error(f"[ADB] Erro ao abrir discador: {e}")
            raise

    def whatsapp_call(self, phone: str):
        """
        Abre o chat do WhatsApp e, se houver coordenadas, clica no botão de chamada.
        Melhorias:
        - Tenta múltiplos esquemas de URL para o WhatsApp.
        - Delays ajustáveis via ENV.
        """
        self.verificar_conexao()
        numero = ''.join(filter(str.isdigit, phone))
        if not numero.startswith("55"):
            numero = "55" + numero
            
        log.info(f"[ADB] Abrindo chat do WhatsApp para chamada: {numero}")
        
        # 1. Abre o chat (Tentativa 1: deep link padrão)
        intent_url = f"whatsapp://send?phone={numero}"
        shell_cmd = f"am start -p com.whatsapp -a android.intent.action.VIEW -d '{intent_url}'"
        
        try:
            res = self._adb(["shell", shell_cmd], timeout=15)
            if "error" in (res.stdout + res.stderr).lower():
                # Tentativa 2: Link universal
                log.warning("[ADB] Falha no deep link WhatsApp. Tentando link wa.me...")
                intent_url_2 = f"https://wa.me/{numero}"
                shell_cmd_2 = f"am start -p com.whatsapp -a android.intent.action.VIEW -d '{intent_url_2}'"
                self._adb(["shell", shell_cmd_2], timeout=15)
        except Exception as e:
            log.error(f"[ADB] Erro ao abrir chat: {e}")
            raise
        
        # 2. Aguarda abertura (Aumentado para garantir carregamento da UI)
        config = config_manager.get_all()
        delay = int(config.get("ADB_DELAY_ABERTURA_CALL", 4))
        log.info(f"[ADB] Aguardando {delay}s para a conversa carregar...")
        time.sleep(delay)
        
        # 3. Tenta clicar no botão de chamada se coordenadas existirem
        call_x = str(config.get("ADB_WHATSAPP_CALL_X", "")).strip()
        call_y = str(config.get("ADB_WHATSAPP_CALL_Y", "")).strip()
        
        if call_x and call_y:
            log.info(f"[ADB] Clicando no botão de chamada em ({call_x}, {call_y})...")
            self._adb(["shell", "input", "tap", call_x, call_y], timeout=10)
            log.info("[ADB] ✅ Clique na chamada disparado.")
        else:
            log.warning("[ADB] Coordenadas de chamada (ADB_WHATSAPP_CALL_X/Y) não encontradas no .env. Apenas o chat foi aberto.")
            raise RuntimeError("Coordenadas de chamada não configuradas. Abra o chat e configure X/Y no .env.")
