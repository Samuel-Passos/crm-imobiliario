-- ==========================================
-- Migration: Tabela prospecoes_chat
-- Cria a tabela para registrar envios de chat OLX
-- Execute no Supabase SQL Editor
-- ==========================================

CREATE TABLE IF NOT EXISTS prospecoes_chat (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  imovel_id           INTEGER REFERENCES imoveis(id) ON DELETE CASCADE,
  status              TEXT NOT NULL DEFAULT 'aguardando_resposta',
  -- Valores possíveis para status:
  -- 'aguardando_resposta' → Chat enviado, aguardando o proprietário responder
  -- 'respondido'          → Proprietário respondeu (Fase 2)
  -- 'sem_resposta'        → Tempo expirou sem resposta
  -- 'chat_indisponivel'   → Anúncio não tem botão chat
  -- 'anuncio_expirado'    → Anúncio foi removido/expirado
  -- 'erro'               → Falha técnica no envio
  mensagem_enviada    TEXT,
  resposta_recebida   TEXT,           -- preenchida na Fase 2 (monitoramento)
  data_primeiro_envio TIMESTAMPTZ NOT NULL DEFAULT now(),
  data_ultimo_envio   TIMESTAMPTZ NOT NULL DEFAULT now(),
  numero_tentativas   INTEGER NOT NULL DEFAULT 1,
  criado_em           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice para busca rápida por imóvel (evita prospectar duas vezes)
CREATE UNIQUE INDEX IF NOT EXISTS idx_prospecoes_chat_imovel_id
  ON prospecoes_chat (imovel_id);

-- Índice para busca por status (monitoramento de respostas - Fase 2)
CREATE INDEX IF NOT EXISTS idx_prospecoes_chat_status
  ON prospecoes_chat (status);

-- Índice para busca por data (relatórios diários)
CREATE INDEX IF NOT EXISTS idx_prospecoes_chat_data_primeiro_envio
  ON prospecoes_chat (data_primeiro_envio);

-- Instrução para verificar se a tabela foi criada corretamente
-- SELECT COUNT(*) FROM prospecoes_chat;
