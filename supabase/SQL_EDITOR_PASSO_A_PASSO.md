# Supabase SQL Editor - Execucao passo a passo

Este guia usa como fonte oficial o arquivo
[`schema_supabase.sql`](../schema_supabase.sql). Execute os blocos abaixo na
ordem apresentada.

> Importante: selecione o projeto correto no painel do Supabase antes de abrir
> o SQL Editor. Os comandos usam `IF NOT EXISTS` e podem ser repetidos sem
> recriar as tabelas.

## Passo 0 - Extensao para UUID

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

## Passo 1 - Tabela `perfis`

```sql
CREATE TABLE IF NOT EXISTS perfis (
    id BIGSERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE,
    descricao TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 2 - Tabela `usuarios`

Depende de `perfis`.

```sql
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil_id BIGINT NOT NULL REFERENCES perfis(id),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 3 - Tabela `clientes`

```sql
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo VARCHAR(2) NOT NULL DEFAULT 'PJ'
        CHECK (tipo IN ('PF', 'PJ')),
    nome VARCHAR(180) NOT NULL,
    cpf_cnpj VARCHAR(30) NOT NULL UNIQUE,
    telefone VARCHAR(30),
    email VARCHAR(150),
    segmento VARCHAR(80),
    status VARCHAR(20) NOT NULL DEFAULT 'ATIVO'
        CHECK (status IN ('ATIVO', 'INATIVO', 'PROSPECTO')),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 4 - Tabela `enderecos`

Depende de `clientes`.

```sql
CREATE TABLE IF NOT EXISTS enderecos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    cep VARCHAR(12),
    logradouro VARCHAR(180) NOT NULL,
    numero VARCHAR(20),
    bairro VARCHAR(100),
    cidade VARCHAR(100) NOT NULL,
    estado CHAR(2) NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 5 - Tabela `contatos`

Depende de `clientes`.

```sql
CREATE TABLE IF NOT EXISTS contatos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    nome VARCHAR(150) NOT NULL,
    cargo VARCHAR(100),
    telefone VARCHAR(30),
    email VARCHAR(150),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 6 - Tabela `leads`

Depende de `usuarios` e `clientes`.

```sql
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(150) NOT NULL,
    empresa VARCHAR(180),
    telefone VARCHAR(30),
    email VARCHAR(150),
    origem VARCHAR(30) NOT NULL
        CHECK (origem IN (
            'Google', 'LinkedIn', 'Indicacao',
            'Instagram', 'Evento', 'Outro'
        )),
    status VARCHAR(20) NOT NULL DEFAULT 'NOVO'
        CHECK (status IN (
            'NOVO', 'QUALIFICADO', 'CONVERTIDO', 'DESCARTADO'
        )),
    responsavel_id UUID NOT NULL REFERENCES usuarios(id),
    cliente_id UUID REFERENCES clientes(id),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 7 - Tabela `oportunidades`

Depende de `clientes`, `leads` e `usuarios`.

```sql
CREATE TABLE IF NOT EXISTS oportunidades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    lead_id UUID REFERENCES leads(id),
    responsavel_id UUID NOT NULL REFERENCES usuarios(id),
    titulo VARCHAR(180) NOT NULL,
    valor_estimado NUMERIC(14,2) NOT NULL DEFAULT 0
        CHECK (valor_estimado >= 0),
    etapa VARCHAR(20) NOT NULL DEFAULT 'PROSPECCAO'
        CHECK (etapa IN (
            'PROSPECCAO', 'QUALIFICACAO', 'PROPOSTA',
            'NEGOCIACAO', 'FECHAMENTO', 'PERDIDA'
        )),
    probabilidade SMALLINT NOT NULL DEFAULT 10
        CHECK (probabilidade BETWEEN 0 AND 100),
    previsao_fechamento DATE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 8 - Tabela `propostas`

Depende de `oportunidades`.

```sql
CREATE TABLE IF NOT EXISTS propostas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    oportunidade_id UUID NOT NULL REFERENCES oportunidades(id),
    valor NUMERIC(14,2) NOT NULL CHECK (valor >= 0),
    validade DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'RASCUNHO'
        CHECK (status IN (
            'RASCUNHO', 'ENVIADA', 'APROVADA', 'RECUSADA', 'EXPIRADA'
        )),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 9 - Tabela `contratos`

Depende de `clientes`, `propostas` e `usuarios`.

```sql
CREATE TABLE IF NOT EXISTS contratos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    proposta_id UUID REFERENCES propostas(id),
    responsavel_id UUID REFERENCES usuarios(id),
    numero VARCHAR(40) NOT NULL UNIQUE,
    valor NUMERIC(14,2) NOT NULL CHECK (valor >= 0),
    data_inicio DATE NOT NULL,
    data_fim DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'ATIVO'
        CHECK (status IN (
            'ATIVO', 'ENCERRADO', 'CANCELADO', 'SUSPENSO'
        )),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 10 - Tabela `atividades`

Depende de `clientes` e `usuarios`.

```sql
CREATE TABLE IF NOT EXISTS atividades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    usuario_id UUID NOT NULL REFERENCES usuarios(id),
    tipo VARCHAR(20) NOT NULL
        CHECK (tipo IN (
            'LIGACAO', 'REUNIAO', 'VISITA',
            'FOLLOW_UP', 'EMAIL', 'PROPOSTA'
        )),
    titulo VARCHAR(180) NOT NULL,
    descricao TEXT,
    data_agendada TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDENTE'
        CHECK (status IN ('PENDENTE', 'CONCLUIDA', 'CANCELADA')),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 11 - Tabela `contas_receber`

Depende de `clientes` e `contratos`.

```sql
CREATE TABLE IF NOT EXISTS contas_receber (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    contrato_id UUID REFERENCES contratos(id),
    valor NUMERIC(14,2) NOT NULL CHECK (valor >= 0),
    vencimento DATE NOT NULL,
    pagamento DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'ABERTO'
        CHECK (status IN ('ABERTO', 'PAGO', 'VENCIDO', 'CANCELADO')),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (status <> 'PAGO' OR pagamento IS NOT NULL)
);
```

## Passo 12 - Tabela `comissoes`

Depende de `usuarios` e `contratos`.

```sql
CREATE TABLE IF NOT EXISTS comissoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id),
    contrato_id UUID NOT NULL UNIQUE
        REFERENCES contratos(id) ON DELETE CASCADE,
    percentual NUMERIC(5,2) NOT NULL DEFAULT 5
        CHECK (percentual BETWEEN 0 AND 100),
    valor NUMERIC(14,2) NOT NULL CHECK (valor >= 0),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 13 - Tabela `logs`

Depende de `usuarios`.

```sql
CREATE TABLE IF NOT EXISTS logs (
    id BIGSERIAL PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios(id),
    tabela VARCHAR(80) NOT NULL,
    registro_id UUID,
    acao VARCHAR(30) NOT NULL,
    dados_anteriores JSONB,
    dados_novos JSONB,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Passo 14 - Indices

```sql
CREATE INDEX IF NOT EXISTS idx_usuarios_email
    ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_clientes_cpf_cnpj
    ON clientes(cpf_cnpj);
CREATE INDEX IF NOT EXISTS idx_clientes_status
    ON clientes(status);
CREATE INDEX IF NOT EXISTS idx_leads_status
    ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_origem
    ON leads(origem);
CREATE INDEX IF NOT EXISTS idx_oportunidades_etapa
    ON oportunidades(etapa);
CREATE INDEX IF NOT EXISTS idx_contratos_status
    ON contratos(status);
CREATE INDEX IF NOT EXISTS idx_contas_receber_status
    ON contas_receber(status);
CREATE INDEX IF NOT EXISTS idx_contas_receber_vencimento
    ON contas_receber(vencimento);
CREATE INDEX IF NOT EXISTS idx_atividades_data_agendada
    ON atividades(data_agendada);
CREATE INDEX IF NOT EXISTS idx_logs_usuario_id
    ON logs(usuario_id);
CREATE INDEX IF NOT EXISTS idx_logs_tabela
    ON logs(tabela);
```

## Passo 15 - Perfis iniciais

```sql
INSERT INTO perfis (nome, descricao) VALUES
    ('Administrador', 'Acesso completo ao sistema'),
    ('Diretor', 'Visao executiva e indicadores'),
    ('Gerente', 'Gestao da operacao comercial'),
    ('Supervisor', 'Supervisao de equipe e atividades'),
    ('Vendedor', 'Operacao de vendas e carteira')
ON CONFLICT (nome) DO UPDATE
SET descricao = EXCLUDED.descricao;
```

## Passo 16 - View de indicadores

Execute este passo somente depois de criar `contas_receber`.

```sql
DROP MATERIALIZED VIEW IF EXISTS vw_kpi_vendas;

CREATE MATERIALIZED VIEW vw_kpi_vendas AS
SELECT
    date_trunc('month', cr.pagamento)::date AS mes,
    SUM(cr.valor)::numeric(14,2) AS faturamento_mensal,
    COUNT(DISTINCT cr.contrato_id) AS contratos_pagos
FROM contas_receber cr
WHERE cr.status = 'PAGO'
GROUP BY date_trunc('month', cr.pagamento)
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_vw_kpi_vendas_mes
    ON vw_kpi_vendas(mes);

CREATE OR REPLACE FUNCTION refresh_kpi_vendas()
RETURNS void
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    REFRESH MATERIALIZED VIEW vw_kpi_vendas;
$$;
```

## Passo 17 - Seguranca

O sistema atual acessa os dados por uma API de backend. Este bloco impede
acesso anonimo direto e ativa RLS sem criar politicas publicas.

```sql
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon;

ALTER TABLE perfis ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE enderecos ENABLE ROW LEVEL SECURITY;
ALTER TABLE contatos ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE oportunidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE propostas ENABLE ROW LEVEL SECURITY;
ALTER TABLE contratos ENABLE ROW LEVEL SECURITY;
ALTER TABLE atividades ENABLE ROW LEVEL SECURITY;
ALTER TABLE contas_receber ENABLE ROW LEVEL SECURITY;
ALTER TABLE comissoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;
```

## Passo 18 - Verificacao

Execute para confirmar as 13 tabelas:

```sql
SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
  AND table_name IN (
      'perfis',
      'usuarios',
      'clientes',
      'enderecos',
      'contatos',
      'leads',
      'oportunidades',
      'propostas',
      'contratos',
      'atividades',
      'contas_receber',
      'comissoes',
      'logs'
  )
ORDER BY table_name;
```

Resultado esperado: 13 linhas.

Para verificar as chaves estrangeiras:

```sql
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS tabela_referenciada,
    ccu.column_name AS coluna_referenciada
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
 AND tc.constraint_schema = kcu.constraint_schema
JOIN information_schema.constraint_column_usage ccu
  ON ccu.constraint_name = tc.constraint_name
 AND ccu.constraint_schema = tc.constraint_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;
```

## Aplicacao completa

Se preferir executar tudo de uma vez, use o conteudo de
[`schema_supabase.sql`](../schema_supabase.sql) no SQL Editor.
