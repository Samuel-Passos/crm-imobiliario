-- Migração para logs detalhados (item por item) do Scraper
CREATE TABLE IF NOT EXISTS logs_detalhados_scraper (
    id BIGSERIAL PRIMARY KEY,
    estatistica_id BIGINT REFERENCES estatisticas_scraper(id) ON DELETE CASCADE,
    data_hora TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    imovel_id BIGINT,
    url TEXT,
    com_telefone BOOLEAN DEFAULT FALSE,
    origem_telefone TEXT, -- 'botao', 'descricao' ou null
    expirado BOOLEAN DEFAULT FALSE,
    erro TEXT,
    duracao_segundos INTEGER
);

-- Index para busca rápida por ID da execução pai
CREATE INDEX IF NOT EXISTS idx_logs_detalhados_stat_id ON logs_detalhados_scraper (estatistica_id);
CREATE INDEX IF NOT EXISTS idx_logs_detalhados_data ON logs_detalhados_scraper (data_hora);

-- Permissões
ALTER TABLE logs_detalhados_scraper ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Scraper can insert detailed logs" ON logs_detalhados_scraper FOR ALL USING (true) WITH CHECK (true);
