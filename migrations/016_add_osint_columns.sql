-- Adicionar colunas para inteligência investigativa (OSINT)
ALTER TABLE public.empresas_sjc 
ADD COLUMN IF NOT EXISTS qsa_completo JSONB,
ADD COLUMN IF NOT EXISTS responsavel_qualificacao TEXT;

COMMENT ON COLUMN public.empresas_sjc.qsa_completo IS 'Quadro de Sócios e Administradores em formato estruturado (Nome, CPF Mascarado, Qualificação)';
COMMENT ON COLUMN public.empresas_sjc.responsavel_qualificacao IS 'Qualificação do responsável legal da empresa';
