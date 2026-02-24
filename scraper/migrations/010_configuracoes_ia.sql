-- ============================================================
-- Migration 010: Configurações Globais da IA
-- Parâmetros que guiam o comportamento do Agente na hora de prospectar
-- ============================================================

CREATE TABLE IF NOT EXISTS public.configuracoes_ia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_personalidade TEXT NOT NULL DEFAULT 'Aja como um corretor imobiliário experiente, educado e direto ao ponto. Sua linguagem deve ser natural, curta e focada em descobrir se o imóvel ainda está disponível para parceria ou venda.',
    requer_aprovacao_mensagens BOOLEAN NOT NULL DEFAULT false,
    max_chats_dia INTEGER NOT NULL DEFAULT 50,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigger para atualizar data
CREATE OR REPLACE FUNCTION public.update_config_ia_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_config_ia_atualizado_em ON public.configuracoes_ia;
CREATE TRIGGER trg_config_ia_atualizado_em
    BEFORE UPDATE ON public.configuracoes_ia
    FOR EACH ROW EXECUTE FUNCTION public.update_config_ia_atualizado_em();

-- Insere um registro único caso a tabela esteja vazia
INSERT INTO public.configuracoes_ia (prompt_personalidade, requer_aprovacao_mensagens, max_chats_dia)
SELECT 'Aja como um corretor imobiliário experiente, educado e direto ao ponto. Sua linguagem deve ser natural, curta e focada em descobrir se o imóvel ainda está disponível para parceria ou venda.', false, 50
WHERE NOT EXISTS (SELECT 1 FROM public.configuracoes_ia);
