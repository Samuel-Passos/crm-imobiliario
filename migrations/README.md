# Migrations — CRM Imobiliário

Execute os arquivos abaixo **na ordem** no **SQL Editor** do seu projeto Supabase.

## Ordem de Execução

| # | Arquivo | O que faz |
|---|---------|-----------|
| 1 | `001_create_profiles.sql` | Cria enum `role_enum`, tabela `profiles`, trigger de auto-criação ao registrar usuário |
| 2 | `002_create_kanban_colunas.sql` | Cria tabela `kanban_colunas` + insere as 13 colunas padrão |
| 3 | `003_create_contatos.sql` | Cria enum `tipo_contato_enum` e tabela `contatos` |
| 4 | `004_alter_imoveis.sql` | Adiciona campos de kanban, permuta, notas e coordenadas na tabela `imoveis` |
| 5 | `005_rls_policies.sql` | Ativa RLS e cria políticas de acesso por role em todas as tabelas |

## ⚠️ Atenção antes de rodar a Migration 004

A Migration 004 assume que já existe uma tabela chamada **`imoveis`** no seu Supabase.
Antes de executar, confirme os nomes das colunas atuais com:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'imoveis'
ORDER BY ordinal_position;
```

## ⚠️ Ajuste necessário no trigger da Migration 004

O trigger que move automaticamente o imóvel para **Caixa de Entrada** está comentado.
Para ativá-lo, identifique na tabela `links_anuncios`:
- O nome exato da coluna `status`
- O nome da FK que referencia `imoveis.id`

Depois edite a linha:
```sql
WHERE id = NEW.imovel_id;  -- substitua por sua coluna FK real
```
E descomente o bloco `CREATE TRIGGER trg_auto_kanban`.

## Como executar no Supabase

1. Acesse [app.supabase.com](https://app.supabase.com) → seu projeto
2. Vá em **SQL Editor**
3. Clique em **New query**
4. Cole o conteúdo de cada arquivo, um por vez, na ordem acima
5. Clique em **Run**

## Verificação pós-migration

```sql
-- Confirmar tabelas criadas
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Confirmar colunas adicionadas em imoveis
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'imoveis'
AND column_name IN (
  'kanban_coluna_id','kanban_ordem','aceita_permuta',
  'notas_corretor','historico_kanban','latitude','longitude'
);

-- Confirmar colunas padrão do kanban
SELECT nome, ordem FROM kanban_colunas ORDER BY ordem;
```
