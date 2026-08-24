import asyncio
import re
import random
from typing import Dict, Any

# ─── Seletores do Botão "Chat" no anúncio ────────────────────────────────────
# A OLX renderiza o chat como um painel lateral que abre ao clicar no botão Chat.
# Listados em ordem de prioridade (mais específico → mais genérico).
SELETORES_BTN_CHAT = [
    '#price-box-button-chat',
]

# ─── Seletores do campo textarea (onde digitamos a mensagem) ─────────────────
SELETORES_TEXTAREA = [
    '#input-text-message',
    'textarea[placeholder*="mensagem" i]',
    'textarea[placeholder*="message" i]',
    'textarea[name="message"]',
    '[data-ds-component="DS-TextArea"] textarea',
    'textarea',
]

# ─── Seletores do botão Enviar ───────────────────────────────────────────────
SELETORES_BTN_ENVIAR = [
    'button[type="submit"][aria-label*="enviar" i]',
    'button[aria-label*="enviar" i]',
    'button[aria-label*="send" i]',
    'button[type="submit"]',
    'button:has-text("Enviar")',
]

# ─── Palavras-chave que indicam anúncio expirado ─────────────────────────────
KEYWORDS_EXPIRADO = [
    "anúncio finalizado", "ops!", "não encontrado",
    "anúncio desativado", "página não encontrada"
]


async def _digitar_humano(page, seletor_str: str, texto: str):
    loc = page.locator(seletor_str).first
    # Conforme solicitado, copiar e colar em vez de digitar letra por letra
    await loc.fill(texto)
    await asyncio.sleep(0.5)


async def _encontrar_elemento(page, seletores: list[str], timeout_ms: int = 8000) -> tuple[Any, str] | tuple[None, None]:
    """
    Testa todos os seletores simultaneamente (em paralelo).
    Retorna o primeiro que ficar visível.
    """
    async def _testar(sel):
        loc = page.locator(sel).first
        await loc.wait_for(state="visible", timeout=timeout_ms)
        return loc, sel

    tasks = [asyncio.create_task(_testar(sel)) for sel in seletores]
    try:
        while tasks:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for t in done:
                try:
                    res = t.result()
                    if res:
                        # Achamos! Cancela as outras e retorna
                        for p in pending:
                            p.cancel()
                        return res
                except Exception:
                    # Esta tarefa falhou, ignoramos
                    pass
            # Atualiza as tarefas para continuar esperando as que faltam
            tasks = list(pending)
    except Exception:
        pass
        
    return None, None


async def send_chat_olx(url: str, mensagem: str, page) -> Dict[str, Any]:
    """
    Acessa a URL do anúncio OLX usando a aba persistente já autenticada (Workspace 2),
    abre o painel de chat lateral, digita a mensagem e envia.

    Usa a mesma estratégia do phone_extractor.py:
      - page.goto(url) na aba fixa global
      - Seletores manuais (sem LLM / sem browser-use) para máxima compatibilidade com anti-bot
      - Digitação humana caractere a caractere
      - Delays aleatórios anti-ban
    """
    dados: Dict[str, Any] = {
        "enviado": False,
        "expirado": False,
        "chat_indisponivel": False,
        "erro": None,
    }

    print(f"💬 [CHAT] Iniciando envio para: {url}")

    try:
        # ── 1. Navega para o anúncio ──────────────────────────────────────────
        print("  -> Navegando para o anúncio...")
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"  🚨 Falha no carregamento inicial da página: {e}")
            dados["erro"] = f"Erro de timeout ou rede: {e}"
            return dados

        # Delay humano para o React renderizar
        try:
            await page.wait_for_selector("h1", timeout=10000)
        except Exception:
            pass
        await asyncio.sleep(random.uniform(1.5, 3.0))

        # ── 2. Verifica Cloudflare / expirado ────────────────────────────────
        title = await page.title()
        content = await page.content()

        if any(kw in title.lower() for kw in ["attention required", "cloudflare", "access denied"]):
            print("  🚫 BLOQUEIO Cloudflare detectado.")
            dados["erro"] = "cloudflare"
            return dados

        if any(kw in title.lower() or kw in content.lower() for kw in KEYWORDS_EXPIRADO):
            print("  ⚠️ Anúncio expirado ou indisponível.")
            dados["expirado"] = True
            return dados

        # ── 3. Pular botão Chat e ir direto para a URL do Chat (como os Scripts 1, 2, 3) ──
        import re
        m = re.search(r'-(\d+)$', url)
        chat_page = page
        
        if m:
            list_id = m.group(1)
            chat_url = f"https://chat.olx.com.br/?list-id={list_id}"
            print(f"  🌐 Navegando direto para o chat do anúncio: {chat_url}")
            try:
                await chat_page.goto(chat_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(4.0) # Tempo para o React renderizar o histórico
            except Exception as e:
                print(f"  🚨 Falha na navegação direta: {e}")
                dados["erro"] = f"erro_navegacao_direta: {e}"
                return dados
        else:
            print("  🚨 URL não contém ID do anúncio no final.")
            dados["erro"] = "url_sem_list_id"
            return dados

        await asyncio.sleep(random.uniform(1.0, 2.0))

        # ── 4. Localiza o campo de texto ─────────────────────────────────────
        print("  -> Procurando campo de texto...")
        textarea, sel_ta = await _encontrar_elemento(
            chat_page, SELETORES_TEXTAREA, timeout_ms=20000
        )

        if not textarea:
            print("  ❌ Campo de texto do chat não encontrado.")
            dados["erro"] = "textarea_nao_encontrado"
            return dados

        print(f"  ✅ Textarea encontrado via: {sel_ta}")

        # ── 5. Digita a mensagem humanamente ──────────────────────────────────
        print(f"  -> Digitando mensagem ({len(mensagem)} chars)...")
        await _digitar_humano(chat_page, sel_ta or "textarea", mensagem)
        print("  ✅ Mensagem digitada.")

        # ── 6. Procura e clica no botão Enviar ───────────────────────────────
        print("  -> Procurando botão Enviar...")
        btn_enviar, sel_env = await _encontrar_elemento(
            chat_page, SELETORES_BTN_ENVIAR, timeout_ms=5000
        )

        if not btn_enviar:
            # Fallback: tenta Enter no textarea
            print("  ⚠️ Botão Enviar não encontrado. Tentando Enter...")
            ta_loc = chat_page.locator(sel_ta).first
            await ta_loc.press("Enter")
        else:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await btn_enviar.click()
            print(f"  ✅ Botão Enviar clicado via: {sel_env}")

        # ── 7. Aguarda confirmação visual ────────────────────────────────────
        # A OLX normalmente mostra a mensagem enviada no histórico do chat.
        # Aguardamos um tempo razoável e assumimos sucesso se não houve erro.
        await asyncio.sleep(random.uniform(2.5, 4.0))

        # Verificação extra: tenta detectar se a msg apareceu no histórico
        try:
            # Tenta encontrar a mensagem enviada no DOM do chat
            # Faz busca por texto parcial da mensagem (primeiras 30 chars)
            trecho = re.escape(mensagem[:30])
            confirmacao = chat_page.locator(f'text="{mensagem[:30]}"').first
            if await confirmacao.count() > 0:
                print("  ✅ Mensagem confirmada no histórico do chat.")
            else:
                print("  ℹ️ Confirmação visual não detectada, mas assumindo envio OK.")
        except Exception:
            pass

        if chat_page != page:
            await chat_page.close()

        dados["enviado"] = True
        print(f"  ✅ [CHAT] Envio concluído para {url}")

    except Exception as e:
        print(f"  🚨 [CHAT] Erro inesperado: {e}")
        dados["erro"] = str(e)

    return dados


if __name__ == "__main__":
    """Teste local (requer page real do Playwright)."""
    print("Execute via orchestrator ou main.py, não diretamente.")
