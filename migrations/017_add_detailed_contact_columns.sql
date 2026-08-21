-- Migração 017: Adicionar colunas detalhadas de contato para enriquecimento multiponto
ALTER TABLE public.empresas_sjc 
ADD COLUMN IF NOT EXISTS tel_opencnpj TEXT,
ADD COLUMN IF NOT EXISTS email_opencnpj TEXT,
ADD COLUMN IF NOT EXISTS site_google TEXT;

-- Comentários para documentação
COMMENT ON COLUMN public.empresas_sjc.tel_opencnpj IS 'Telefone extraído via API MinhaReceita/OpenCNPJ';
COMMENT ON COLUMN public.empresas_sjc.email_opencnpj IS 'E-mail extraído via API MinhaReceita/OpenCNPJ';
COMMENT ON COLUMN public.empresas_sjc.site_google IS 'Website encontrado via busca no Google Maps';
