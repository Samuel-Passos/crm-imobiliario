-- ============================================================
-- Migration 011: Adicionar URL do Chat
-- ============================================================

ALTER TABLE public.prospecoes_chat
    -- Coluna que guarda o link direto para a conversa, ex: https://chat.olx.com.br/c/123456...
    ADD COLUMN IF NOT EXISTS url_chat TEXT;

-- Opcional: comentário na coluna
COMMENT ON COLUMN public.prospecoes_chat.url_chat IS 'URL direta para a conversa no painel de chats da OLX, capturada após o primeiro envio';
