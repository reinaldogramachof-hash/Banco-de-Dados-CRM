-- Diagnostico do schema CRM Corporativo no PostgreSQL / Supabase.
SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'perfis', 'usuarios', 'clientes', 'enderecos', 'contatos', 'leads',
      'oportunidades', 'propostas', 'contratos', 'atividades',
      'contas_receber', 'comissoes', 'logs'
  )
ORDER BY table_name;

SELECT
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
      'perfis', 'usuarios', 'clientes', 'enderecos', 'contatos', 'leads',
      'oportunidades', 'propostas', 'contratos', 'atividades',
      'contas_receber', 'comissoes', 'logs'
  )
ORDER BY table_name, ordinal_position;

SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
   AND tc.table_schema = kcu.table_schema
WHERE tc.table_schema = 'public'
  AND tc.table_name IN (
      'perfis', 'usuarios', 'clientes', 'enderecos', 'contatos', 'leads',
      'oportunidades', 'propostas', 'contratos', 'atividades',
      'contas_receber', 'comissoes', 'logs'
  )
ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;

SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

SELECT
    schemaname,
    matviewname,
    ispopulated
FROM pg_matviews
WHERE schemaname = 'public'
  AND matviewname = 'vw_kpi_vendas';

SELECT nome, descricao FROM perfis ORDER BY nome;
SELECT COUNT(*) AS usuarios FROM usuarios;
SELECT COUNT(*) AS clientes FROM clientes;
SELECT COUNT(*) AS leads FROM leads;
SELECT COUNT(*) AS contratos FROM contratos;
SELECT COUNT(*) AS contas_receber FROM contas_receber;
SELECT * FROM vw_kpi_vendas ORDER BY mes;
