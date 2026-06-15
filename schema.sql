PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS perfis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    descricao TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
        substr(lower(hex(randomblob(2))), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6)))),
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    senha_hash TEXT NOT NULL,
    perfil_id INTEGER NOT NULL REFERENCES perfis(id),
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clientes (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
        substr(lower(hex(randomblob(2))), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6)))),
    tipo TEXT NOT NULL DEFAULT 'PJ' CHECK (tipo IN ('PF', 'PJ')),
    nome TEXT NOT NULL,
    cpf_cnpj TEXT NOT NULL UNIQUE,
    telefone TEXT,
    email TEXT,
    segmento TEXT,
    status TEXT NOT NULL DEFAULT 'ATIVO' CHECK (status IN ('ATIVO', 'INATIVO', 'PROSPECTO')),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enderecos (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
        substr(lower(hex(randomblob(2))), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6)))),
    cliente_id TEXT NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    cep TEXT, logradouro TEXT NOT NULL, numero TEXT, bairro TEXT, cidade TEXT NOT NULL, estado TEXT NOT NULL,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contatos (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
        substr(lower(hex(randomblob(2))), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6)))),
    cliente_id TEXT NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    nome TEXT NOT NULL, cargo TEXT, telefone TEXT, email TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leads (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
        substr(lower(hex(randomblob(2))), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6)))),
    nome TEXT NOT NULL, empresa TEXT, telefone TEXT, email TEXT,
    origem TEXT NOT NULL CHECK (origem IN ('Google', 'LinkedIn', 'Indicacao', 'Instagram', 'Evento', 'Outro')),
    status TEXT NOT NULL DEFAULT 'NOVO' CHECK (status IN ('NOVO', 'QUALIFICADO', 'CONVERTIDO', 'DESCARTADO')),
    responsavel_id TEXT NOT NULL REFERENCES usuarios(id),
    cliente_id TEXT REFERENCES clientes(id),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS oportunidades (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
        substr(lower(hex(randomblob(2))), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6)))),
    cliente_id TEXT NOT NULL REFERENCES clientes(id),
    lead_id TEXT REFERENCES leads(id),
    responsavel_id TEXT NOT NULL REFERENCES usuarios(id),
    titulo TEXT NOT NULL,
    valor_estimado REAL NOT NULL DEFAULT 0 CHECK (valor_estimado >= 0),
    etapa TEXT NOT NULL DEFAULT 'PROSPECCAO' CHECK (etapa IN ('PROSPECCAO', 'QUALIFICACAO', 'PROPOSTA', 'NEGOCIACAO', 'FECHAMENTO', 'PERDIDA')),
    probabilidade INTEGER NOT NULL DEFAULT 10 CHECK (probabilidade BETWEEN 0 AND 100),
    previsao_fechamento TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS propostas (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
        substr(lower(hex(randomblob(2))), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6)))),
    oportunidade_id TEXT NOT NULL REFERENCES oportunidades(id),
    valor REAL NOT NULL CHECK (valor >= 0),
    validade TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'RASCUNHO' CHECK (status IN ('RASCUNHO', 'ENVIADA', 'APROVADA', 'RECUSADA', 'EXPIRADA')),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contratos (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
        substr(lower(hex(randomblob(2))), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6)))),
    cliente_id TEXT NOT NULL REFERENCES clientes(id),
    proposta_id TEXT REFERENCES propostas(id),
    responsavel_id TEXT REFERENCES usuarios(id),
    numero TEXT NOT NULL UNIQUE,
    valor REAL NOT NULL CHECK (valor >= 0),
    data_inicio TEXT NOT NULL, data_fim TEXT,
    status TEXT NOT NULL DEFAULT 'ATIVO' CHECK (status IN ('ATIVO', 'ENCERRADO', 'CANCELADO', 'SUSPENSO')),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS atividades (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
        substr(lower(hex(randomblob(2))), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6)))),
    cliente_id TEXT NOT NULL REFERENCES clientes(id),
    usuario_id TEXT NOT NULL REFERENCES usuarios(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('LIGACAO', 'REUNIAO', 'VISITA', 'FOLLOW_UP', 'EMAIL', 'PROPOSTA')),
    titulo TEXT NOT NULL, descricao TEXT, data_agendada TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE' CHECK (status IN ('PENDENTE', 'CONCLUIDA', 'CANCELADA')),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contas_receber (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
        substr(lower(hex(randomblob(2))), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6)))),
    cliente_id TEXT NOT NULL REFERENCES clientes(id),
    contrato_id TEXT REFERENCES contratos(id),
    valor REAL NOT NULL CHECK (valor >= 0),
    vencimento TEXT NOT NULL, pagamento TEXT,
    status TEXT NOT NULL DEFAULT 'ABERTO' CHECK (status IN ('ABERTO', 'PAGO', 'VENCIDO', 'CANCELADO')),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comissoes (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
        substr(lower(hex(randomblob(2))), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6)))),
    usuario_id TEXT NOT NULL REFERENCES usuarios(id),
    contrato_id TEXT NOT NULL UNIQUE REFERENCES contratos(id) ON DELETE CASCADE,
    percentual REAL NOT NULL DEFAULT 5 CHECK (percentual BETWEEN 0 AND 100),
    valor REAL NOT NULL CHECK (valor >= 0),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id TEXT REFERENCES usuarios(id),
    tabela TEXT NOT NULL, registro_id TEXT, acao TEXT NOT NULL,
    dados_anteriores TEXT, dados_novos TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_clientes_cpf_cnpj ON clientes(cpf_cnpj);
CREATE INDEX IF NOT EXISTS idx_clientes_status ON clientes(status);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_origem ON leads(origem);
CREATE INDEX IF NOT EXISTS idx_oportunidades_etapa ON oportunidades(etapa);
CREATE INDEX IF NOT EXISTS idx_contratos_status ON contratos(status);
CREATE INDEX IF NOT EXISTS idx_contas_status ON contas_receber(status);
CREATE INDEX IF NOT EXISTS idx_contas_vencimento ON contas_receber(vencimento);
CREATE INDEX IF NOT EXISTS idx_atividades_data ON atividades(data_agendada);
CREATE INDEX IF NOT EXISTS idx_logs_usuario ON logs(usuario_id);
CREATE INDEX IF NOT EXISTS idx_logs_tabela ON logs(tabela);

INSERT OR IGNORE INTO perfis (nome, descricao) VALUES
('Administrador', 'Acesso completo ao sistema'),
('Diretor', 'Visao executiva e indicadores'),
('Gerente', 'Gestao da operacao comercial'),
('Supervisor', 'Supervisao de equipe e atividades'),
('Vendedor', 'Operacao de vendas e carteira');
