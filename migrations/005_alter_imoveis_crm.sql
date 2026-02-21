-- Migration 005: Campos de confirmação CRM + corretor responsável
-- Execute no Supabase SQL Editor

ALTER TABLE public.imoveis
  -- Proprietário (vendedor_nome já existe no banco)
  ADD COLUMN IF NOT EXISTS vendedor_email         TEXT,
  ADD COLUMN IF NOT EXISTS autorizado             BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS comissao_pct           NUMERIC(5,2),

  -- Área (area_m2 já existe, adicionamos as novas)
  ADD COLUMN IF NOT EXISTS area_terreno_m2        NUMERIC(10,2),
  ADD COLUMN IF NOT EXISTS area_construida_m2     NUMERIC(10,2),

  -- Cômodos (suites já existe no banco)
  ADD COLUMN IF NOT EXISTS salas                  INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS tem_cozinha            BOOLEAN DEFAULT TRUE,

  -- Textos (descricao já existe no banco)
  ADD COLUMN IF NOT EXISTS outras_caracteristicas TEXT,

  -- Corretor responsável
  ADD COLUMN IF NOT EXISTS corretor_id            UUID REFERENCES public.profiles(id) ON DELETE SET NULL;

-- Índice para filtrar por corretor
CREATE INDEX IF NOT EXISTS idx_imoveis_corretor ON public.imoveis(corretor_id);
