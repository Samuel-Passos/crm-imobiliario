-- Migração 021: Correção de colunas faltantes e endereçamento
ALTER TABLE public.empresas_sjc 
ADD COLUMN IF NOT EXISTS responsavel_qualificacao TEXT;

-- Garantir que temos todas as partes do endereço
ALTER TABLE public.empresas_sjc 
ADD COLUMN IF NOT EXISTS logradouro TEXT,
ADD COLUMN IF NOT EXISTS numero TEXT,
ADD COLUMN IF NOT EXISTS bairro TEXT;
