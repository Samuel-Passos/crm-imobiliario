-- Execute este comando no painel SQL do Supabase
ALTER TABLE configuracoes_ia ADD COLUMN IF NOT EXISTS delay_entre_chats INTEGER DEFAULT 60;
