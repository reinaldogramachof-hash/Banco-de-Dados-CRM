-- Carga inicial idempotente para PostgreSQL / Supabase.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO perfis (nome, descricao) VALUES
('Administrador', 'Acesso completo ao sistema'),
('Diretor', 'Visao executiva e indicadores'),
('Gerente', 'Gestao da operacao comercial'),
('Supervisor', 'Supervisao de equipe e atividades'),
('Vendedor', 'Operacao de vendas e carteira')
ON CONFLICT (nome) DO UPDATE SET descricao = EXCLUDED.descricao;

INSERT INTO usuarios (nome, email, senha_hash, perfil_id, ativo)
SELECT dados.nome, dados.email, encode(digest('Senha@123', 'sha256'), 'hex'), p.id, TRUE
FROM (VALUES
    ('Joao Silva', 'joao@crm.local', 'Administrador'),
    ('Maria Souza', 'maria@crm.local', 'Gerente'),
    ('Carlos Lima', 'carlos@crm.local', 'Vendedor'),
    ('Ana Costa', 'ana@crm.local', 'Vendedor'),
    ('Pedro Santos', 'pedro@crm.local', 'Supervisor')
) AS dados(nome, email, perfil)
JOIN perfis p ON p.nome = dados.perfil
ON CONFLICT (email) DO UPDATE SET
    nome = EXCLUDED.nome, perfil_id = EXCLUDED.perfil_id, ativo = TRUE;

INSERT INTO clientes (tipo, nome, cpf_cnpj, telefone, email, segmento, status)
SELECT
    'PJ',
    'Empresa Corporativa ' || lpad(i::text, 2, '0'),
    '10.000.000/0001-' || lpad(i::text, 2, '0'),
    '(11) 4000-' || lpad(i::text, 4, '0'),
    'contato' || i || '@empresa.local',
    (ARRAY['Tecnologia', 'Saude', 'Educacao', 'Industria'])[((i - 1) % 4) + 1],
    'ATIVO'
FROM generate_series(1, 20) i
ON CONFLICT (cpf_cnpj) DO UPDATE SET
    nome = EXCLUDED.nome, segmento = EXCLUDED.segmento, status = 'ATIVO';

INSERT INTO enderecos (cliente_id, cep, logradouro, numero, bairro, cidade, estado)
SELECT c.id, '01000-000', 'Avenida Corporativa', split_part(c.cpf_cnpj, '-', 2), 'Centro', 'Sao Paulo', 'SP'
FROM clientes c
WHERE c.cpf_cnpj LIKE '10.000.000/0001-%'
  AND NOT EXISTS (SELECT 1 FROM enderecos e WHERE e.cliente_id = c.id);

INSERT INTO contatos (cliente_id, nome, cargo, telefone, email)
SELECT
    c.id,
    'Contato ' || contato.numero || ' - ' || c.nome,
    CASE contato.numero WHEN 1 THEN 'Gestor' ELSE 'Compras' END,
    '(11) 90000-000' || contato.numero,
    'contato' || contato.numero || '.' || replace(lower(c.nome), ' ', '') || '@crm.local'
FROM clientes c
CROSS JOIN (VALUES (1), (2)) AS contato(numero)
WHERE c.cpf_cnpj LIKE '10.000.000/0001-%'
  AND NOT EXISTS (
      SELECT 1 FROM contatos existente
      WHERE existente.cliente_id = c.id
        AND existente.email = 'contato' || contato.numero || '.' || replace(lower(c.nome), ' ', '') || '@crm.local'
  );

INSERT INTO leads (nome, empresa, telefone, email, origem, status, responsavel_id, cliente_id)
SELECT
    'Lead ' || lpad(i::text, 2, '0'),
    'Prospect ' || lpad(i::text, 2, '0'),
    '(21) 98888-' || lpad(i::text, 4, '0'),
    'lead' || i || '@crm.local',
    (ARRAY['Google', 'LinkedIn', 'Indicacao', 'Instagram'])[((i - 1) % 4) + 1],
    (ARRAY['CONVERTIDO', 'NOVO', 'QUALIFICADO'])[((i - 1) % 3) + 1],
    CASE WHEN i % 2 = 0 THEN carlos.id ELSE ana.id END,
    CASE WHEN ((i - 1) % 3) = 0 THEN cliente.id ELSE NULL END
FROM generate_series(1, 50) i
CROSS JOIN LATERAL (SELECT id FROM usuarios WHERE email = 'carlos@crm.local') carlos
CROSS JOIN LATERAL (SELECT id FROM usuarios WHERE email = 'ana@crm.local') ana
LEFT JOIN LATERAL (
    SELECT id FROM clientes
    WHERE cpf_cnpj = '10.000.000/0001-' || lpad((((i - 1) % 20) + 1)::text, 2, '0')
) cliente ON TRUE
WHERE NOT EXISTS (SELECT 1 FROM leads l WHERE l.email = 'lead' || i || '@crm.local');

INSERT INTO contratos (cliente_id, responsavel_id, numero, valor, data_inicio, data_fim, status)
SELECT
    c.id,
    CASE WHEN i % 2 = 0 THEN carlos.id ELSE ana.id END,
    'CTR-' || extract(year FROM current_date)::int || '-' || lpad(i::text, 4, '0'),
    12000 + (i - 1) * 1750,
    current_date - ((i - 1) * 12),
    current_date + 365,
    'ATIVO'
FROM generate_series(1, 15) i
JOIN clientes c ON c.cpf_cnpj = '10.000.000/0001-' || lpad(i::text, 2, '0')
CROSS JOIN LATERAL (SELECT id FROM usuarios WHERE email = 'carlos@crm.local') carlos
CROSS JOIN LATERAL (SELECT id FROM usuarios WHERE email = 'ana@crm.local') ana
ON CONFLICT (numero) DO UPDATE SET valor = EXCLUDED.valor, status = 'ATIVO';

INSERT INTO contas_receber (cliente_id, contrato_id, valor, vencimento, pagamento, status)
SELECT c.cliente_id, c.id, c.valor, c.data_inicio, c.data_inicio + 2, 'PAGO'
FROM contratos c
WHERE c.numero LIKE 'CTR-' || extract(year FROM current_date)::int || '-%'
  AND NOT EXISTS (SELECT 1 FROM contas_receber cr WHERE cr.contrato_id = c.id);

INSERT INTO comissoes (usuario_id, contrato_id, percentual, valor)
SELECT c.responsavel_id, c.id, 5, round(c.valor * 0.05, 2)
FROM contratos c
WHERE c.responsavel_id IS NOT NULL
ON CONFLICT (contrato_id) DO UPDATE SET
    usuario_id = EXCLUDED.usuario_id, percentual = 5, valor = EXCLUDED.valor;

INSERT INTO oportunidades (cliente_id, responsavel_id, titulo, valor_estimado, etapa, probabilidade, previsao_fechamento)
SELECT c.cliente_id, c.responsavel_id, 'Projeto ' || c.numero, c.valor, 'FECHAMENTO', 100, current_date + 20
FROM contratos c
WHERE NOT EXISTS (SELECT 1 FROM oportunidades o WHERE o.titulo = 'Projeto ' || c.numero);

INSERT INTO atividades (cliente_id, usuario_id, tipo, titulo, descricao, data_agendada, status)
SELECT
    c.id,
    CASE WHEN i % 2 = 0 THEN carlos.id ELSE ana.id END,
    'REUNIAO',
    'Reuniao de acompanhamento ' || i,
    'Revisao comercial da conta',
    now() + ((i - 4) || ' days')::interval,
    CASE WHEN i < 3 THEN 'CONCLUIDA' ELSE 'PENDENTE' END
FROM generate_series(1, 10) i
JOIN clientes c ON c.cpf_cnpj = '10.000.000/0001-' || lpad(i::text, 2, '0')
CROSS JOIN LATERAL (SELECT id FROM usuarios WHERE email = 'carlos@crm.local') carlos
CROSS JOIN LATERAL (SELECT id FROM usuarios WHERE email = 'ana@crm.local') ana
WHERE NOT EXISTS (SELECT 1 FROM atividades a WHERE a.titulo = 'Reuniao de acompanhamento ' || i);

REFRESH MATERIALIZED VIEW vw_kpi_vendas;
