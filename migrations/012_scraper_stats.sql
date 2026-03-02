-- Migração para tabela de estatísticas do Scraper
CREATE TABLE IF NOT EXISTS estatisticas_scraper (
    id BIGSERIAL PRIMARY KEY,
    data_inicio TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_fim TIMESTAMP WITH TIME ZONE,
    leads_processados INTEGER DEFAULT 0,
    leads_expirados INTEGER DEFAULT 0,
    leads_sem_telefone INTEGER DEFAULT 0,
    leads_com_telefone INTEGER DEFAULT 0,
    encontrados_via_botao INTEGER DEFAULT 0,
    encontrados_via_descricao INTEGER DEFAULT 0,
    erros INTEGER DEFAULT 0
);

-- Index para performance por data
CREATE INDEX IF NOT EXISTS idx_estatisticas_data ON estatisticas_scraper (data_inicio);

-- Permissões para que o scraper possa escrever
ALTER TABLE estatisticas_scraper ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Scraper can do everything" ON estatisticas_scraper FOR ALL USING (true) WITH CHECK (true);
