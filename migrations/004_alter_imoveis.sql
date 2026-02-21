-- ============================================================
-- Migration 004: Alterações na tabela imoveis
-- Adiciona campos para kanban, permuta, notas, geocodificação
-- e detalhamento de endereço (número, complemento, condomínio)
-- ============================================================
-- NOTA: latitude, longitude, andar, bairro, cep, cidade, estado,
-- rua já existem na tabela. Esta migration adiciona apenas o que falta.
-- ============================================================

-- Enum para permuta (seguro: ignora se já existir)
DO $$ BEGIN
  CREATE TYPE permuta_enum AS ENUM ('aceita', 'nao_aceita', 'nao_informado');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Novos campos na tabela imoveis
ALTER TABLE public.imoveis
    -- ── Kanban ──────────────────────────────────────────────
    ADD COLUMN IF NOT EXISTS kanban_coluna_id  UUID REFERENCES public.kanban_colunas(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS kanban_ordem       INTEGER DEFAULT 0,

    -- ── Permuta / Notas / Histórico ──────────────────────────
    ADD COLUMN IF NOT EXISTS aceita_permuta     permuta_enum NOT NULL DEFAULT 'nao_informado',
    ADD COLUMN IF NOT EXISTS notas_corretor     TEXT,
    ADD COLUMN IF NOT EXISTS historico_kanban   JSONB DEFAULT '[]'::jsonb,

    -- ── Endereço detalhado (complementa rua já existente) ────
    ADD COLUMN IF NOT EXISTS numero             TEXT,
    ADD COLUMN IF NOT EXISTS complemento        TEXT,

    -- ── Condomínio (visível apenas se em_condominio = true) ──
    ADD COLUMN IF NOT EXISTS em_condominio      BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS nome_condominio    TEXT,
    ADD COLUMN IF NOT EXISTS bloco              TEXT,
    ADD COLUMN IF NOT EXISTS numero_apartamento TEXT;

-- Índices
CREATE INDEX IF NOT EXISTS idx_imoveis_kanban_coluna ON public.imoveis(kanban_coluna_id);
CREATE INDEX IF NOT EXISTS idx_imoveis_kanban_ordem  ON public.imoveis(kanban_coluna_id, kanban_ordem);
CREATE INDEX IF NOT EXISTS idx_imoveis_permuta        ON public.imoveis(aceita_permuta);

-- ============================================================
-- Função: ao processar um imóvel (status = 'Processado' em
-- links_anuncios), inseri-lo automaticamente na coluna
-- "Caixa de Entrada" do kanban.
--
-- A ligação entre links_anuncios e imoveis é pelo list_id.
-- ============================================================
CREATE OR REPLACE FUNCTION public.auto_assign_kanban_caixa_entrada()
RETURNS TRIGGER AS $$
DECLARE
    v_coluna_id UUID;
    v_max_ordem INTEGER;
BEGIN
    -- Só age quando status muda para 'Processado'
    IF NEW.status = 'Processado' AND (OLD.status IS DISTINCT FROM 'Processado') THEN
        -- Busca a coluna Caixa de Entrada
        SELECT id INTO v_coluna_id
        FROM public.kanban_colunas
        WHERE nome = 'Caixa de Entrada'
        LIMIT 1;

        IF v_coluna_id IS NOT NULL THEN
            -- Busca a maior ordem atual na coluna
            SELECT COALESCE(MAX(kanban_ordem), 0) INTO v_max_ordem
            FROM public.imoveis
            WHERE kanban_coluna_id = v_coluna_id;

            -- Atribui o imóvel ao kanban via list_id (FK real entre as tabelas)
            UPDATE public.imoveis
            SET
                kanban_coluna_id  = v_coluna_id,
                kanban_ordem      = v_max_ordem + 1,
                historico_kanban  = historico_kanban || jsonb_build_object(
                    'coluna', 'Caixa de Entrada',
                    'data',   NOW()
                )
            WHERE list_id = NEW.list_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Ativa o trigger automático do Kanban
DROP TRIGGER IF EXISTS trg_auto_kanban ON public.links_anuncios;
CREATE TRIGGER trg_auto_kanban
    AFTER UPDATE ON public.links_anuncios
    FOR EACH ROW EXECUTE FUNCTION public.auto_assign_kanban_caixa_entrada();
