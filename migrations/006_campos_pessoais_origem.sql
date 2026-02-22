-- ============================================================
-- Migration 006: Campos pessoais em contatos + origem em imoveis
-- ============================================================

-- 1. Novos campos pessoais na tabela contatos
ALTER TABLE public.contatos
  ADD COLUMN IF NOT EXISTS cpf              TEXT,
  ADD COLUMN IF NOT EXISTS rg               TEXT,
  ADD COLUMN IF NOT EXISTS data_nascimento  DATE,
  ADD COLUMN IF NOT EXISTS estado_civil     TEXT,   -- solteiro, casado, divorciado, viúvo, outro
  ADD COLUMN IF NOT EXISTS origem           TEXT;   -- OLX, Indicação, Site, etc.

-- 2. Coluna origem na tabela imoveis (valor padrão = 'OLX' pois vem do scraper)
ALTER TABLE public.imoveis
  ADD COLUMN IF NOT EXISTS origem TEXT NOT NULL DEFAULT 'OLX';

-- Índice para filtragem por origem
CREATE INDEX IF NOT EXISTS idx_contatos_origem ON public.contatos(origem);
CREATE INDEX IF NOT EXISTS idx_imoveis_origem  ON public.imoveis(origem);
