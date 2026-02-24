-- ============================================================
-- Migration 008: Campos de Prospecção na tabela imoveis
-- Prepara os imóveis para o fluxo de extração de telefones
-- ============================================================

ALTER TABLE public.imoveis
    -- Indica se o agente já abriu a página para buscar o telefone
    ADD COLUMN IF NOT EXISTS telefone_pesquisado BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Indica se a página retornou erro 404/expirado
    ADD COLUMN IF NOT EXISTS anuncio_expirado BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Armazena os números encontrados (seja no botão ou na descrição)
    -- Exemplo do JSON esperado: [{"nome": "Oseias", "telefone": "129999999", "origem": "descricao"}]
    ADD COLUMN IF NOT EXISTS telefones_extraidos JSONB DEFAULT '[]'::jsonb;

-- Índices para acelerar a busca no cron diário
CREATE INDEX IF NOT EXISTS idx_imoveis_prospeccao_pendente 
ON public.imoveis(telefone_pesquisado, anuncio_expirado) 
WHERE telefone_pesquisado = FALSE AND anuncio_expirado = FALSE;
