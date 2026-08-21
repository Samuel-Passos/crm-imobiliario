"""
templates.py
────────────
Templates de mensagem do robô de disponibilidade.
"""

import os
from config_manager import config_manager

def mensagem_inicial(
    proprietario: str,
    referencia: str,
    link_imovel: str | None = None,
) -> str:
    """
    Monta a mensagem inicial usando o template configurado.
    """
    config = config_manager.get_all()
    template = config.get("TEMPLATE_WHATSAPP_DISP", "")
    remetente = config.get("REMETENTE_NOME", "Samuel")

    if not template:
        # Fallback caso o template não esteja configurado
        template = "Olá {proprietario}, tudo bem?\n\n{remetente} aqui.\n\nQuero saber se seu imóvel de referência {referencia} está disponível?\n\nCaso esteja, houve alguma mudança no valor informado?\n\n{link}"

    # Prepara os dados — {link} é substituído pelo URL puro,
    # a formatação fica por conta do que foi configurado no template.
    nome_exibicao = proprietario if proprietario else 'Proprietário(a)'
    link_str = link_imovel if link_imovel else ""

    msg = template.replace("{proprietario}", nome_exibicao)
    msg = msg.replace("{referencia}", referencia)
    msg = msg.replace("{remetente}", remetente)
    msg = msg.replace("{link}", link_str)

    return msg

def mensagem_confirmacao_sim(referencia: str) -> str:
    return (
        f"Perfeito, obrigado pela confirmação! ✅\n\n"
        f"Atualizamos o imóvel *{referencia}* como *disponível* em nosso sistema.\n\n"
        f"Caso algo mude, pode me avisar a qualquer momento. 🙏"
    )

def mensagem_confirmacao_nao(referencia: str) -> str:
    return (
        f"Entendido! Obrigado pela atualização. 🙏\n\n"
        f"Atualizei o imóvel *{referencia}* como *indisponível* em nosso sistema.\n\n"
        f"Se precisar de algo no futuro, estamos à disposição!"
    )

def mensagem_agradecimento_preco(referencia: str, novo_preco: str) -> str:
    return (
        f"Anotado! Obrigado. ✅\n\n"
        f"Registrei o imóvel *{referencia}* como *disponível* com o valor atualizado: *{novo_preco}*.\n\n"
        f"Qualquer mudança, é só me avisar! 🙏"
    )
