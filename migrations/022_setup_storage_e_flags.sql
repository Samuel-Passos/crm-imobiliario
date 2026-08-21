-- ============================================================
-- Migration 022: Setup Storage e Flags para Download de Fotos
-- ============================================================

-- 1. Adicionar colunas na tabela imoveis para controle de download e backup
ALTER TABLE public.imoveis
    ADD COLUMN IF NOT EXISTS fotos_baixadas BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS fotos_originais_olx JSONB;

-- 2. Configurar o bucket do Supabase Storage
-- Cria o bucket público se não existir
INSERT INTO storage.buckets (id, name, public) 
VALUES ('imoveis_fotos', 'imoveis_fotos', true)
ON CONFLICT (id) DO NOTHING;

-- 3. Políticas de Segurança (RLS) para o bucket
-- Permite leitura pública das imagens
DO $$ BEGIN
    CREATE POLICY "Leitura Pública de Fotos" 
    ON storage.objects FOR SELECT 
    USING ( bucket_id = 'imoveis_fotos' );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Permite inserção/upload de novas imagens
DO $$ BEGIN
    CREATE POLICY "Upload de Fotos" 
    ON storage.objects FOR INSERT 
    WITH CHECK ( bucket_id = 'imoveis_fotos' );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Permite update (sobrescrever arquivo caso necessário)
DO $$ BEGIN
    CREATE POLICY "Update de Fotos" 
    ON storage.objects FOR UPDATE 
    USING ( bucket_id = 'imoveis_fotos' );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
