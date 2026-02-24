-- ============================================================
-- Migration 009: Tabelas de Controle de Prospecção
-- Gerencia o estado das sequências de mensagens no chat
-- ============================================================

-- Tabela de Templates Configuráveis
CREATE TABLE IF NOT EXISTS public.templates_mensagem (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ordem INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('inicial', 'followup_sem_resposta', 'followup_com_resposta')),
    conteudo TEXT NOT NULL,
    dias_aguardar INTEGER DEFAULT 1,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insere templates padrão iniciais
INSERT INTO public.templates_mensagem (ordem, tipo, conteudo, dias_aguardar)
SELECT * FROM (VALUES
    (1, 'inicial', 'Olá! Tenho interesse no seu imóvel. Ainda está disponível? Gostaria de saber mais detalhes.', 1),
    (2, 'followup_sem_resposta', 'Olá, tudo bem? Apenas passando pra verificar se conseguiu ver minha mensagem anterior. Ainda tem interesse em negociar o imóvel?', 2),
    (3, 'followup_sem_resposta', 'Tentando um último contato! Caso resolva negociar o imóvel, estou à disposição.', 0)
) AS defaults(ordem, tipo, conteudo, dias_aguardar)
WHERE NOT EXISTS (SELECT 1 FROM public.templates_mensagem);


-- Tabela de Controle de Prospecção por Imóvel
CREATE TABLE IF NOT EXISTS public.prospecoes_chat (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    imovel_id BIGINT NOT NULL REFERENCES public.imoveis(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'aguardando_resposta', 'respondeu', 'encerrado')),
    etapa_atual INTEGER NOT NULL DEFAULT 0,
    ultima_mensagem_enviada TEXT,
    data_ultimo_envio TIMESTAMPTZ,
    ultima_resposta_proprietario TEXT,
    data_ultima_resposta TIMESTAMPTZ,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(imovel_id) -- Garante apenas uma prospecção ativa por imóvel
);

-- Trigger para atualizar data
CREATE OR REPLACE FUNCTION public.update_prospecoes_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prospecoes_atualizado_em ON public.prospecoes_chat;
CREATE TRIGGER trg_prospecoes_atualizado_em
    BEFORE UPDATE ON public.prospecoes_chat
    FOR EACH ROW EXECUTE FUNCTION public.update_prospecoes_atualizado_em();

-- Índices úteis
CREATE INDEX IF NOT EXISTS idx_prospecoes_pendentes 
ON public.prospecoes_chat(status, data_ultimo_envio);
