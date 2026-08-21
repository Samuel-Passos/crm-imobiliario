-- Migração 014: Criar tabela empresas_sjc para o Extrator de CNPJ

CREATE TABLE IF NOT EXISTS public.empresas_sjc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cnpj TEXT UNIQUE NOT NULL,
    cnpj_basico TEXT,
    razao_social TEXT,
    nome_fantasia TEXT,
    cnae TEXT,
    natureza_juridica TEXT,
    endereco TEXT,
    bairro TEXT,
    municipio TEXT DEFAULT 'SAO JOSE DOS CAMPOS',
    uf TEXT DEFAULT 'SP',
    cep TEXT,
    ddd1 TEXT,
    tel1 TEXT,
    ddd2 TEXT,
    tel2 TEXT,
    telefone_completo_1 TEXT,
    telefone_completo_2 TEXT,
    email TEXT,
    email_site TEXT,
    socios TEXT,
    tel_maps TEXT,
    site TEXT,
    whatsapp TEXT,
    instagram TEXT,
    facebook TEXT,
    score INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pendente',
    atualizado_em TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Índices para busca rápida
CREATE INDEX IF NOT EXISTS idx_empresas_sjc_cnae ON public.empresas_sjc(cnae);
CREATE INDEX IF NOT EXISTS idx_empresas_sjc_status ON public.empresas_sjc(status);
CREATE INDEX IF NOT EXISTS idx_empresas_sjc_whatsapp ON public.empresas_sjc(whatsapp);

-- Habilitar RLS
ALTER TABLE public.empresas_sjc ENABLE ROW LEVEL SECURITY;

-- Políticas simples (acesso total para usuários autenticados por enquanto)
CREATE POLICY "Acesso total para todos" ON public.empresas_sjc
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Comentário da tabela
COMMENT ON TABLE public.empresas_sjc IS 'Tabela para armazenar dados de empresas extraídos via API CNPJ e enriquecidos com Google Maps/Scraping.';
