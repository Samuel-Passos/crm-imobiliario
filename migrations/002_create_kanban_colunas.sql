-- ============================================================
-- Migration 002: Criação da tabela kanban_colunas
-- ============================================================

CREATE TABLE IF NOT EXISTS public.kanban_colunas (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome      TEXT NOT NULL,
    ordem     INTEGER NOT NULL DEFAULT 0,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice por ordem para renderização do kanban
CREATE INDEX IF NOT EXISTS idx_kanban_colunas_ordem ON public.kanban_colunas(ordem);

-- ============================================================
-- Colunas padrão (inserção inicial)
-- Só insere se a tabela estiver vazia
-- ============================================================
INSERT INTO public.kanban_colunas (nome, ordem)
SELECT nome, ordem FROM (VALUES
    ('Caixa de Entrada',       1),
    ('Script 1',               2),
    ('Script 2',               3),
    ('Script 3',               4),
    ('Script Descarte',        5),
    ('Sem Resposta',           6),
    ('Recusou',                7),
    ('Desistiu',               8),
    ('Já Cadastrado',          9),
    ('Vendido',               10),
    ('Expirados',             11),
    ('Aceitou',               12),
    ('Qualificação do Cadastro', 13)
) AS defaults(nome, ordem)
WHERE NOT EXISTS (SELECT 1 FROM public.kanban_colunas);
