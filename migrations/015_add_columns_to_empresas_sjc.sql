-- Migração 015: Adicionar colunas faltantes para enriquecimento total
ALTER TABLE public.empresas_sjc 
ADD COLUMN IF NOT EXISTS identificador_matriz_filial TEXT,
ADD COLUMN IF NOT EXISTS data_situacao_cadastral TEXT,
ADD COLUMN IF NOT EXISTS motivo_situacao_cadastral TEXT,
ADD COLUMN IF NOT EXISTS data_inicio_atividade TEXT,
ADD COLUMN IF NOT EXISTS logradouro TEXT,
ADD COLUMN IF NOT EXISTS numero TEXT,
ADD COLUMN IF NOT EXISTS complemento TEXT,
ADD COLUMN IF NOT EXISTS codigo_municipio TEXT,
ADD COLUMN IF NOT EXISTS municipio_import TEXT,
ADD COLUMN IF NOT EXISTS ddd_fax TEXT,
ADD COLUMN IF NOT EXISTS qualificacao_do_responsavel TEXT,
ADD COLUMN IF NOT EXISTS capital_social NUMERIC,
ADD COLUMN IF NOT EXISTS porte TEXT,
ADD COLUMN IF NOT EXISTS opcao_pelo_simples TEXT,
ADD COLUMN IF NOT EXISTS data_opcao_pelo_simples TEXT,
ADD COLUMN IF NOT EXISTS data_exclusao_do_simples TEXT,
ADD COLUMN IF NOT EXISTS opcao_pelo_mei TEXT,
ADD COLUMN IF NOT EXISTS situacao_especial TEXT,
ADD COLUMN IF NOT EXISTS data_situacao_especial TEXT;

-- Comentários para documentação
COMMENT ON COLUMN public.empresas_sjc.capital_social IS 'Capital social nominal da empresa';
COMMENT ON COLUMN public.empresas_sjc.porte IS 'Porte da empresa (ME, EPP, DEMAIS)';
COMMENT ON COLUMN public.empresas_sjc.socios IS 'Lista de sócios extraída via OpenCNPJ';
