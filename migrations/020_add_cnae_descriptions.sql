-- Migração 020: Suporte a detalhamento de CNAEs (Principal e Secundários)
ALTER TABLE public.empresas_sjc 
ADD COLUMN IF NOT EXISTS cnae_descricao TEXT,
ADD COLUMN IF NOT EXISTS cnaes_secundarios TEXT;

COMMENT ON COLUMN public.empresas_sjc.cnae_descricao IS 'Descrição por extenso do CNAE Principal';
COMMENT ON COLUMN public.empresas_sjc.cnaes_secundarios IS 'Lista de CNAEs secundários (Código - Descrição) separados por quebra de linha ou vírgula';
