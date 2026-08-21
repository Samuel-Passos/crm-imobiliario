-- 019_create_agentes_ia.sql
-- Tabela para armazenar os Agentes de IA customizados e suas bases de conhecimento

CREATE TABLE IF NOT EXISTS public.agentes_ia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    nome TEXT NOT NULL,
    icone TEXT,
    descricao TEXT,
    instrucao_sistema TEXT NOT NULL,
    categoria TEXT DEFAULT 'Geral',
    is_public BOOLEAN DEFAULT false,
    criado_em TIMESTAMPTZ DEFAULT now(),
    atualizado_em TIMESTAMPTZ DEFAULT now()
);

-- Tabela para os arquivos de referência vinculados aos agentes
CREATE TABLE IF NOT EXISTS public.agente_arquivos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agente_id UUID REFERENCES public.agentes_ia(id) ON DELETE CASCADE,
    nome_arquivo TEXT NOT NULL,
    caminho_local TEXT NOT NULL,
    tamanho_bytes BIGINT,
    tipo_mime TEXT,
    criado_em TIMESTAMPTZ DEFAULT now()
);

-- RLS
ALTER TABLE public.agentes_ia ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agente_arquivos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Agentes visíveis para todos (se públicos) ou para o dono"
ON public.agentes_ia FOR SELECT
USING (is_public = true OR auth.uid() = user_id);

CREATE POLICY "Dono pode gerenciar seus agentes"
ON public.agentes_ia FOR ALL
USING (auth.uid() = user_id);

CREATE POLICY "Dono pode gerenciar arquivos de seus agentes"
ON public.agente_arquivos FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM public.agentes_ia 
        WHERE id = agente_id AND user_id = auth.uid()
    )
);
