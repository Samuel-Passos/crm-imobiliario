-- ============================================================
-- Migration 005: Row Level Security (RLS)
-- Políticas por role: admin, corretor, secretario, cliente
-- ============================================================

-- ================================================
-- Helper function: retorna o role do usuário atual
-- ================================================
CREATE OR REPLACE FUNCTION public.get_user_role()
RETURNS role_enum AS $$
    SELECT role FROM public.profiles WHERE user_id = auth.uid();
$$ LANGUAGE SQL SECURITY DEFINER STABLE;

-- ================================================
-- RLS na tabela: profiles
-- ================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Admin: acesso total
CREATE POLICY "admin_all_profiles" ON public.profiles
    FOR ALL USING (public.get_user_role() = 'admin');

-- Qualquer usuário autenticado pode ler e editar o próprio perfil
CREATE POLICY "own_profile_select" ON public.profiles
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "own_profile_update" ON public.profiles
    FOR UPDATE USING (user_id = auth.uid());

-- ================================================
-- RLS na tabela: imoveis
-- ================================================
ALTER TABLE public.imoveis ENABLE ROW LEVEL SECURITY;

-- Admin: tudo
CREATE POLICY "admin_all_imoveis" ON public.imoveis
    FOR ALL USING (public.get_user_role() = 'admin');

-- Corretor: leitura e edição total
CREATE POLICY "corretor_select_imoveis" ON public.imoveis
    FOR SELECT USING (public.get_user_role() = 'corretor');

CREATE POLICY "corretor_update_imoveis" ON public.imoveis
    FOR UPDATE USING (public.get_user_role() = 'corretor');

-- Secretário: leitura total, UPDATE apenas em kanban e notas
CREATE POLICY "secretario_select_imoveis" ON public.imoveis
    FOR SELECT USING (public.get_user_role() = 'secretario');

-- Nota: para restringir colunas no UPDATE use uma view ou check em application level,
-- pois o Supabase RLS não suporta column-level UPDATE restrictions nativamente.
-- Alternativa: criar uma função RPC exclusiva para secretário.

-- Cliente: leitura apenas de imóveis em Aceitou ou Qualificação
CREATE POLICY "cliente_select_imoveis" ON public.imoveis
    FOR SELECT USING (
        public.get_user_role() = 'cliente'
        AND kanban_coluna_id IN (
            SELECT id FROM public.kanban_colunas
            WHERE nome IN ('Aceitou', 'Qualificação do Cadastro')
        )
    );

-- ================================================
-- RLS na tabela: links_anuncios
-- ================================================
ALTER TABLE public.links_anuncios ENABLE ROW LEVEL SECURITY;

-- Admin: tudo
CREATE POLICY "admin_all_links" ON public.links_anuncios
    FOR ALL USING (public.get_user_role() = 'admin');

-- Corretor e secretário: leitura
CREATE POLICY "corretor_select_links" ON public.links_anuncios
    FOR SELECT USING (public.get_user_role() IN ('corretor', 'secretario'));

-- ================================================
-- RLS na tabela: kanban_colunas
-- ================================================
ALTER TABLE public.kanban_colunas ENABLE ROW LEVEL SECURITY;

-- Admin e corretor: tudo
CREATE POLICY "admin_corretor_all_kanban_colunas" ON public.kanban_colunas
    FOR ALL USING (public.get_user_role() IN ('admin', 'corretor'));

-- Secretário e cliente: leitura
CREATE POLICY "secretario_cliente_select_kanban_colunas" ON public.kanban_colunas
    FOR SELECT USING (public.get_user_role() IN ('secretario', 'cliente'));

-- ================================================
-- RLS na tabela: contatos
-- ================================================
ALTER TABLE public.contatos ENABLE ROW LEVEL SECURITY;

-- Admin: tudo
CREATE POLICY "admin_all_contatos" ON public.contatos
    FOR ALL USING (public.get_user_role() = 'admin');

-- Corretor: leitura e edição
CREATE POLICY "corretor_select_contatos" ON public.contatos
    FOR SELECT USING (public.get_user_role() = 'corretor');

CREATE POLICY "corretor_update_contatos" ON public.contatos
    FOR UPDATE USING (public.get_user_role() = 'corretor');

CREATE POLICY "corretor_insert_contatos" ON public.contatos
    FOR INSERT WITH CHECK (public.get_user_role() IN ('admin', 'corretor'));

-- Secretário: leitura
CREATE POLICY "secretario_select_contatos" ON public.contatos
    FOR SELECT USING (public.get_user_role() = 'secretario');
