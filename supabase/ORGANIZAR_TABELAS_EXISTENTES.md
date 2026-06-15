# Organizar as tabelas existentes no Supabase

## Analise do retorno

O retorno confirma a criacao das 13 tabelas:

1. `perfis`
2. `usuarios`
3. `clientes`
4. `enderecos`
5. `contatos`
6. `leads`
7. `oportunidades`
8. `propostas`
9. `contratos`
10. `atividades`
11. `contas_receber`
12. `comissoes`
13. `logs`

As tabelas de `clientes` ate `logs` estao alinhadas com o modelo principal.
As tabelas `perfis` e `usuarios`, porem, ja existiam com uma estrutura anterior.
O comando `CREATE TABLE IF NOT EXISTS` preservou essa estrutura em vez de
atualiza-la.

Diferencas encontradas:

- `perfis.id` e `usuarios.perfil_id` usam `int4`, mas sao compativeis entre si.
- `perfis` nao possui `criado_em`.
- `usuarios.perfil_id`, `ativo` e `criado_em` aceitam nulo.
- `usuarios.criado_em` usa `timestamp` sem fuso horario.
- `usuarios` nao possui `atualizado_em`.

Nao e necessario alterar os IDs de `int4` para `int8` neste momento. Isso
evita uma migracao arriscada de chave primaria e estrangeira sem beneficio
pratico para o volume atual.

## Ordem de execucao

Execute cada bloco separadamente no SQL Editor.

## 1. Verificar dados nulos em `usuarios`

```sql
SELECT
    COUNT(*) FILTER (WHERE perfil_id IS NULL) AS sem_perfil,
    COUNT(*) FILTER (WHERE ativo IS NULL) AS sem_status,
    COUNT(*) FILTER (WHERE criado_em IS NULL) AS sem_data_criacao
FROM public.usuarios;
```

Se `sem_perfil` for maior que zero, relacione esses usuarios a um perfil antes
do passo 4:

```sql
SELECT id, nome, email, perfil_id
FROM public.usuarios
WHERE perfil_id IS NULL;
```

Exemplo de correcao individual:

```sql
UPDATE public.usuarios
SET perfil_id = (
    SELECT id
    FROM public.perfis
    WHERE nome = 'Vendedor'
)
WHERE id = 'UUID-DO-USUARIO';
```

## 2. Inserir os perfis padrao

```sql
INSERT INTO public.perfis (nome, descricao) VALUES
    ('Administrador', 'Acesso completo ao sistema'),
    ('Diretor', 'Visao executiva e indicadores'),
    ('Gerente', 'Gestao da operacao comercial'),
    ('Supervisor', 'Supervisao de equipe e atividades'),
    ('Vendedor', 'Operacao de vendas e carteira')
ON CONFLICT (nome) DO UPDATE
SET descricao = EXCLUDED.descricao;
```

## 3. Corrigir colunas ausentes e valores nulos

```sql
BEGIN;

ALTER TABLE public.perfis
    ADD COLUMN IF NOT EXISTS criado_em TIMESTAMPTZ;

UPDATE public.perfis
SET criado_em = now()
WHERE criado_em IS NULL;

ALTER TABLE public.perfis
    ALTER COLUMN criado_em SET DEFAULT now(),
    ALTER COLUMN criado_em SET NOT NULL;

ALTER TABLE public.usuarios
    ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMPTZ;

UPDATE public.usuarios
SET ativo = TRUE
WHERE ativo IS NULL;

UPDATE public.usuarios
SET criado_em = CURRENT_TIMESTAMP
WHERE criado_em IS NULL;

UPDATE public.usuarios
SET atualizado_em = criado_em
WHERE atualizado_em IS NULL;

ALTER TABLE public.usuarios
    ALTER COLUMN ativo SET DEFAULT TRUE,
    ALTER COLUMN ativo SET NOT NULL,
    ALTER COLUMN criado_em SET DEFAULT now(),
    ALTER COLUMN criado_em SET NOT NULL,
    ALTER COLUMN atualizado_em SET DEFAULT now(),
    ALTER COLUMN atualizado_em SET NOT NULL;

COMMIT;
```

## 4. Tornar `perfil_id` obrigatorio

Execute somente quando a consulta abaixo retornar zero:

```sql
SELECT COUNT(*) AS usuarios_sem_perfil
FROM public.usuarios
WHERE perfil_id IS NULL;
```

Depois:

```sql
ALTER TABLE public.usuarios
ALTER COLUMN perfil_id SET NOT NULL;
```

## 5. Padronizar o fuso de `usuarios.criado_em`

O retorno indica que essa coluna usa `timestamp` sem fuso. Execute a consulta:

```sql
SELECT data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'usuarios'
  AND column_name = 'criado_em';
```

Se o resultado for `timestamp without time zone` e os valores existentes
representarem o horario de Sao Paulo, execute:

```sql
ALTER TABLE public.usuarios
ALTER COLUMN criado_em TYPE TIMESTAMPTZ
USING criado_em AT TIME ZONE 'America/Sao_Paulo';
```

Se os valores estiverem em UTC, substitua `America/Sao_Paulo` por `UTC`.

## 6. Criar ou confirmar os relacionamentos

Este bloco cria apenas as chaves estrangeiras que ainda nao existem.

```sql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_usuarios_perfil'
    ) THEN
        ALTER TABLE public.usuarios
        ADD CONSTRAINT fk_usuarios_perfil
        FOREIGN KEY (perfil_id) REFERENCES public.perfis(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_enderecos_cliente'
    ) THEN
        ALTER TABLE public.enderecos
        ADD CONSTRAINT fk_enderecos_cliente
        FOREIGN KEY (cliente_id) REFERENCES public.clientes(id)
        ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_contatos_cliente'
    ) THEN
        ALTER TABLE public.contatos
        ADD CONSTRAINT fk_contatos_cliente
        FOREIGN KEY (cliente_id) REFERENCES public.clientes(id)
        ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_leads_responsavel'
    ) THEN
        ALTER TABLE public.leads
        ADD CONSTRAINT fk_leads_responsavel
        FOREIGN KEY (responsavel_id) REFERENCES public.usuarios(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_leads_cliente'
    ) THEN
        ALTER TABLE public.leads
        ADD CONSTRAINT fk_leads_cliente
        FOREIGN KEY (cliente_id) REFERENCES public.clientes(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_oportunidades_cliente'
    ) THEN
        ALTER TABLE public.oportunidades
        ADD CONSTRAINT fk_oportunidades_cliente
        FOREIGN KEY (cliente_id) REFERENCES public.clientes(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_oportunidades_lead'
    ) THEN
        ALTER TABLE public.oportunidades
        ADD CONSTRAINT fk_oportunidades_lead
        FOREIGN KEY (lead_id) REFERENCES public.leads(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_oportunidades_responsavel'
    ) THEN
        ALTER TABLE public.oportunidades
        ADD CONSTRAINT fk_oportunidades_responsavel
        FOREIGN KEY (responsavel_id) REFERENCES public.usuarios(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_propostas_oportunidade'
    ) THEN
        ALTER TABLE public.propostas
        ADD CONSTRAINT fk_propostas_oportunidade
        FOREIGN KEY (oportunidade_id) REFERENCES public.oportunidades(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_contratos_cliente'
    ) THEN
        ALTER TABLE public.contratos
        ADD CONSTRAINT fk_contratos_cliente
        FOREIGN KEY (cliente_id) REFERENCES public.clientes(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_contratos_proposta'
    ) THEN
        ALTER TABLE public.contratos
        ADD CONSTRAINT fk_contratos_proposta
        FOREIGN KEY (proposta_id) REFERENCES public.propostas(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_contratos_responsavel'
    ) THEN
        ALTER TABLE public.contratos
        ADD CONSTRAINT fk_contratos_responsavel
        FOREIGN KEY (responsavel_id) REFERENCES public.usuarios(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_atividades_cliente'
    ) THEN
        ALTER TABLE public.atividades
        ADD CONSTRAINT fk_atividades_cliente
        FOREIGN KEY (cliente_id) REFERENCES public.clientes(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_atividades_usuario'
    ) THEN
        ALTER TABLE public.atividades
        ADD CONSTRAINT fk_atividades_usuario
        FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_contas_receber_cliente'
    ) THEN
        ALTER TABLE public.contas_receber
        ADD CONSTRAINT fk_contas_receber_cliente
        FOREIGN KEY (cliente_id) REFERENCES public.clientes(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_contas_receber_contrato'
    ) THEN
        ALTER TABLE public.contas_receber
        ADD CONSTRAINT fk_contas_receber_contrato
        FOREIGN KEY (contrato_id) REFERENCES public.contratos(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_comissoes_usuario'
    ) THEN
        ALTER TABLE public.comissoes
        ADD CONSTRAINT fk_comissoes_usuario
        FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_comissoes_contrato'
    ) THEN
        ALTER TABLE public.comissoes
        ADD CONSTRAINT fk_comissoes_contrato
        FOREIGN KEY (contrato_id) REFERENCES public.contratos(id)
        ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_logs_usuario'
    ) THEN
        ALTER TABLE public.logs
        ADD CONSTRAINT fk_logs_usuario
        FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
    END IF;
END
$$;
```

Observacao: se as chaves estrangeiras ja existirem com nomes gerados
automaticamente, o bloco acima pode criar relacionamentos equivalentes
duplicados. Execute primeiro esta consulta:

```sql
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS tabela_referenciada
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON kcu.constraint_name = tc.constraint_name
 AND kcu.constraint_schema = tc.constraint_schema
JOIN information_schema.constraint_column_usage ccu
  ON ccu.constraint_name = tc.constraint_name
 AND ccu.constraint_schema = tc.constraint_schema
WHERE tc.table_schema = 'public'
  AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, kcu.column_name;
```

Se a consulta ja listar todos os relacionamentos, pule o bloco de criacao.

## 7. Criar os indices de consulta

```sql
CREATE INDEX IF NOT EXISTS idx_usuarios_email
    ON public.usuarios(email);
CREATE INDEX IF NOT EXISTS idx_clientes_cpf_cnpj
    ON public.clientes(cpf_cnpj);
CREATE INDEX IF NOT EXISTS idx_clientes_status
    ON public.clientes(status);
CREATE INDEX IF NOT EXISTS idx_leads_status
    ON public.leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_origem
    ON public.leads(origem);
CREATE INDEX IF NOT EXISTS idx_oportunidades_etapa
    ON public.oportunidades(etapa);
CREATE INDEX IF NOT EXISTS idx_contratos_status
    ON public.contratos(status);
CREATE INDEX IF NOT EXISTS idx_contas_receber_status
    ON public.contas_receber(status);
CREATE INDEX IF NOT EXISTS idx_contas_receber_vencimento
    ON public.contas_receber(vencimento);
CREATE INDEX IF NOT EXISTS idx_atividades_data_agendada
    ON public.atividades(data_agendada);
CREATE INDEX IF NOT EXISTS idx_logs_usuario_id
    ON public.logs(usuario_id);
CREATE INDEX IF NOT EXISTS idx_logs_tabela
    ON public.logs(tabela);
```

## 8. Documentar os dominios das tabelas

Os comentarios aparecem nas ferramentas de administracao e ajudam a entender
o papel de cada tabela.

```sql
COMMENT ON TABLE public.perfis IS
    'Acesso: perfis e niveis de permissao';
COMMENT ON TABLE public.usuarios IS
    'Acesso: usuarios internos do CRM';
COMMENT ON TABLE public.clientes IS
    'Relacionamento: cadastro principal de clientes';
COMMENT ON TABLE public.enderecos IS
    'Relacionamento: enderecos vinculados aos clientes';
COMMENT ON TABLE public.contatos IS
    'Relacionamento: contatos vinculados aos clientes';
COMMENT ON TABLE public.leads IS
    'Comercial: entradas e qualificacao de potenciais clientes';
COMMENT ON TABLE public.oportunidades IS
    'Comercial: funil e previsao de vendas';
COMMENT ON TABLE public.propostas IS
    'Comercial: propostas associadas as oportunidades';
COMMENT ON TABLE public.contratos IS
    'Comercial: contratos resultantes das negociacoes';
COMMENT ON TABLE public.atividades IS
    'Operacao: tarefas e acompanhamentos comerciais';
COMMENT ON TABLE public.contas_receber IS
    'Financeiro: valores, vencimentos e pagamentos';
COMMENT ON TABLE public.comissoes IS
    'Financeiro: comissoes por vendedor e contrato';
COMMENT ON TABLE public.logs IS
    'Auditoria: historico das operacoes do sistema';
```

## 9. Ativar a seguranca

O backend deve acessar o banco com uma credencial de servidor. A chave
publicavel nao deve receber acesso direto a estas tabelas.

```sql
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon;

ALTER TABLE public.perfis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.enderecos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contatos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.oportunidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.propostas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contratos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.atividades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contas_receber ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comissoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.logs ENABLE ROW LEVEL SECURITY;
```

## 10. Exibir as tabelas na ordem do processo

O Table Editor do Supabase normalmente ordena as tabelas pelo nome e nao
permite uma ordem visual personalizada. Use esta consulta como mapa logico:

```sql
SELECT *
FROM (
    VALUES
        (1, 'Acesso', 'perfis'),
        (2, 'Acesso', 'usuarios'),
        (3, 'Relacionamento', 'clientes'),
        (4, 'Relacionamento', 'enderecos'),
        (5, 'Relacionamento', 'contatos'),
        (6, 'Comercial', 'leads'),
        (7, 'Comercial', 'oportunidades'),
        (8, 'Comercial', 'propostas'),
        (9, 'Comercial', 'contratos'),
        (10, 'Operacao', 'atividades'),
        (11, 'Financeiro', 'contas_receber'),
        (12, 'Financeiro', 'comissoes'),
        (13, 'Auditoria', 'logs')
) AS mapa(ordem, dominio, tabela)
ORDER BY ordem;
```

## 11. Validacao final

```sql
SELECT
    c.table_name,
    COUNT(*) AS total_colunas
FROM information_schema.columns c
WHERE c.table_schema = 'public'
  AND c.table_name IN (
      'perfis', 'usuarios', 'clientes', 'enderecos', 'contatos',
      'leads', 'oportunidades', 'propostas', 'contratos',
      'atividades', 'contas_receber', 'comissoes', 'logs'
  )
GROUP BY c.table_name
ORDER BY c.table_name;
```

Resultado esperado:

| Tabela | Colunas |
|---|---:|
| atividades | 10 |
| clientes | 10 |
| comissoes | 6 |
| contatos | 7 |
| contas_receber | 9 |
| contratos | 11 |
| enderecos | 9 |
| leads | 11 |
| logs | 8 |
| oportunidades | 12 |
| perfis | 4 |
| propostas | 7 |
| usuarios | 8 |

Execute tambem o arquivo [`verifica_supabase.sql`](../verifica_supabase.sql)
para inspecionar colunas, constraints, indices, view e quantidade de dados.
