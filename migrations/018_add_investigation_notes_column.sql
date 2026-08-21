-- Migração 018: Adicionar coluna de notas de investigação para JUCESP e OSINT
ALTER TABLE public.empresas_sjc 
ADD COLUMN IF NOT EXISTS notas_investigacao TEXT;

-- Comentário para documentação
COMMENT ON COLUMN public.empresas_sjc.notas_investigacao IS 'Notas detalhadas extraídas via Robô JUCESP ou inseridas manualmente no dossiê do lead.';
