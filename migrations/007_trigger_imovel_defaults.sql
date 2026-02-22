-- ============================================================
-- Migration 007: Defaults automáticos em imoveis
-- kanban_coluna_id → Caixa de Entrada (UUID fixo)
-- kanban_ordem     → timestamp em segundos (ordem de chegada)
-- origem           → já definida com DEFAULT 'OLX' na migration 006
-- ============================================================

-- UUID da coluna "Caixa de Entrada" (obtido via SELECT na kanban_colunas)
-- 71723ac2-b725-4bf9-b215-6e7993d93673

ALTER TABLE public.imoveis
  ALTER COLUMN kanban_coluna_id
    SET DEFAULT '71723ac2-b725-4bf9-b215-6e7993d93673';

-- kanban_ordem usa EXTRACT(EPOCH) para preservar ordem de chegada
ALTER TABLE public.imoveis
  ALTER COLUMN kanban_ordem
    SET DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT;

