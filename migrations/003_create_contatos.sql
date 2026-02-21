-- ============================================================
-- Migration 003: Criação da tabela contatos
-- ============================================================

-- Enum de tipo de contato
CREATE TYPE tipo_contato_enum AS ENUM (
    'proprietario',
    'inquilino',
    'comprador',
    'parceiro',
    'outro'
);

CREATE TABLE IF NOT EXISTS public.contatos (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Dados pessoais
    nome_completo    TEXT NOT NULL,
    telefone         TEXT,
    whatsapp         TEXT,
    email            TEXT,
    tipo_contato     tipo_contato_enum NOT NULL DEFAULT 'outro',

    -- Endereço
    cep              TEXT,
    logradouro       TEXT,
    numero           TEXT,
    complemento      TEXT,
    bairro           TEXT,
    cidade           TEXT,
    estado           TEXT,

    -- Condomínio
    em_condominio    BOOLEAN NOT NULL DEFAULT FALSE,
    nome_condominio  TEXT,   -- visível apenas se em_condominio = true
    bloco            TEXT,   -- visível apenas se em_condominio = true
    apartamento      TEXT,   -- visível apenas se em_condominio = true

    -- Geocodificação
    latitude         NUMERIC(10, 7),
    longitude        NUMERIC(10, 7),

    -- Vínculo opcional com imóvel
    vinculo_imovel_id UUID REFERENCES public.imoveis(id) ON DELETE SET NULL,

    -- Extras
    notas            TEXT,
    criado_em        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_contatos_tipo ON public.contatos(tipo_contato);
CREATE INDEX IF NOT EXISTS idx_contatos_cidade ON public.contatos(cidade);
CREATE INDEX IF NOT EXISTS idx_contatos_vinculo ON public.contatos(vinculo_imovel_id);

-- Trigger para atualizado_em
CREATE TRIGGER trg_contatos_atualizado_em
    BEFORE UPDATE ON public.contatos
    FOR EACH ROW EXECUTE FUNCTION public.update_atualizado_em();
