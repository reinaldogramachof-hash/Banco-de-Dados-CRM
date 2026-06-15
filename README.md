# CRM Corporativo com Dashboard SIG

Aplicacao web local para gestao comercial, relacionamento com clientes,
contratos, atividades, financeiro, comissoes e indicadores gerenciais.

O sistema inclui uma API HTTP em Python, interface responsiva em HTML/CSS/JS,
banco SQLite inicializado automaticamente e scripts separados para
PostgreSQL/Supabase.

## Recursos

- Dashboard com indicadores comerciais e financeiros
- Clientes com enderecos, contatos e historico relacionado
- Leads com conversao em cliente e oportunidade
- Oportunidades com etapas, probabilidade e valor ponderado
- Propostas com aprovacao e geracao automatica de contrato
- Contratos com numeracao automatica
- Atividades agendadas, proximas e atrasadas
- Contas a receber com baixa de pagamento
- Comissoes por contrato
- Usuarios, perfis e controle de permissoes
- Logs de auditoria
- Sidebar responsiva, retratil no desktop e com rolagem interna

## Stack

- Backend: Python 3.10+ e biblioteca padrao
- Servidor HTTP: `ThreadingHTTPServer`
- Banco local: SQLite
- Frontend: HTML, CSS e JavaScript sem framework
- Autenticacao: token assinado com HMAC SHA-256
- Senhas: PBKDF2-SHA256
- Testes: `unittest` com fluxo HTTP integrado
- Banco alternativo: PostgreSQL / Supabase

Nao ha dependencias Python externas para executar a aplicacao web.

## Estrutura principal

```text
.
|-- server.py                   # Servidor web, API e inicializacao do SQLite
|-- schema.sql                  # Schema e carga inicial usados pelo servidor local
|-- index.html                  # Interface web
|-- style.css                   # Estilos e responsividade
|-- script.js                   # Navegacao e integracao com a API
|-- tests/test_crm.py           # Teste integrado da API
|-- database/                   # Scripts PostgreSQL/Supabase separados
|-- supabase/migrations/        # Migration para Supabase CLI
|-- schema_supabase.sql         # Schema consolidado para Supabase
|-- verifica_supabase.sql       # Consultas de verificacao
|-- app.py                      # Interface desktop independente (Tkinter)
`-- .env.example                # Referencia das variaveis disponiveis
```

## Executar no Windows

Requisito: Python 3.10 ou superior.

No PowerShell, dentro da pasta do projeto:

```powershell
python server.py
```

Se o comando `python` estiver associado a Microsoft Store, use o caminho do
interpretador instalado:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" server.py
```

Para manter o servidor em segundo plano:

```powershell
Start-Process `
  -FilePath "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" `
  -ArgumentList "server.py" `
  -WorkingDirectory $PWD `
  -WindowStyle Hidden
```

Acesse:

```text
http://127.0.0.1:8000/
```

Verifique a API:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Resposta esperada:

```json
{"status":"ok","banco":"crm_corporativo.db"}
```

Para localizar e encerrar o processo que usa a porta 8000:

```powershell
$pidServidor = (Get-NetTCPConnection -LocalPort 8000 -State Listen).OwningProcess
Stop-Process -Id $pidServidor
```

## Executar no Linux ou macOS

```bash
python3 server.py
```

Depois acesse `http://127.0.0.1:8000/`.

## Banco local

Na primeira inicializacao, `server.py` cria `crm_corporativo.db` a partir de
`schema.sql` e insere a carga inicial.

Para recriar o banco de desenvolvimento:

1. Encerre o servidor.
2. Remova somente `crm_corporativo.db`.
3. Inicie `server.py` novamente.

Esse procedimento apaga todos os dados locais existentes.

## Acesso inicial

| Usuario | Email | Perfil |
|---|---|---|
| Joao Silva | `joao@crm.local` | Administrador |
| Maria Souza | `maria@crm.local` | Gerente |
| Carlos Lima | `carlos@crm.local` | Vendedor |
| Ana Costa | `ana@crm.local` | Vendedor |
| Pedro Santos | `pedro@crm.local` | Supervisor |

Senha comum da carga de desenvolvimento: `Senha@123`.

Troque `JWT_SECRET` e as senhas antes de expor o sistema em outra rede ou
publica-lo.

## Variaveis de ambiente

Valores reconhecidos por `server.py`:

| Variavel | Padrao | Finalidade |
|---|---|---|
| `DATABASE_FILE` | `crm_corporativo.db` | Nome ou caminho do banco SQLite |
| `JWT_SECRET` | chave de desenvolvimento | Assinatura dos tokens |
| `HOST` | `127.0.0.1` | Endereco de escuta |
| `PORT` | `8000` | Porta HTTP |

O projeto nao carrega `.env` automaticamente. O arquivo `.env.example` serve
como referencia; defina as variaveis no processo antes de iniciar o servidor.

PowerShell:

```powershell
$env:DATABASE_FILE = "crm_corporativo.db"
$env:JWT_SECRET = "uma-chave-longa-e-aleatoria"
$env:HOST = "127.0.0.1"
$env:PORT = "8000"
python server.py
```

Linux ou macOS:

```bash
DATABASE_FILE=crm_corporativo.db \
JWT_SECRET=uma-chave-longa-e-aleatoria \
HOST=127.0.0.1 \
PORT=8000 \
python3 server.py
```

## Interface

No desktop, o botao ao lado da marca recolhe ou expande a sidebar. A escolha
fica salva no `localStorage` do navegador. Em telas menores, o botao `Menu` no
topo abre a navegacao lateral.

A area de navegacao possui rolagem interna, mantendo a identificacao do usuario
e a acao de sair visiveis.

## API

A URL base local e:

```text
http://127.0.0.1:8000/api
```

Somente estas rotas sao publicas:

```text
GET  /api/health
POST /api/auth/login
```

As demais exigem:

```http
Authorization: Bearer <token>
```

Rotas principais:

```text
POST /api/auth/login
GET  /api/auth/me

GET|POST       /api/clientes
GET|PUT|DELETE /api/clientes/:id
GET            /api/clientes/:id/enderecos
GET            /api/clientes/:id/contatos

GET|POST       /api/leads
POST           /api/leads/:id/converter

GET|POST       /api/oportunidades
GET            /api/oportunidades/funil/resumo

GET|POST       /api/propostas
POST           /api/propostas/:id/aprovar

GET|POST       /api/contratos
GET|POST       /api/atividades
GET            /api/atividades/proximas
GET            /api/atividades/atrasadas

GET|POST       /api/contas-receber
POST           /api/contas-receber/:id/baixar

GET|POST       /api/comissoes
POST           /api/comissoes/gerar/:contratoId

GET|POST       /api/usuarios
GET|POST       /api/perfis
GET            /api/logs

GET            /api/dashboard/kpis
GET            /api/dashboard/faturamento-mensal
GET            /api/dashboard/leads-status
GET            /api/dashboard/leads-origem
GET            /api/dashboard/oportunidades-etapa
GET            /api/dashboard/propostas-status
GET            /api/dashboard/contratos-status
GET            /api/dashboard/financeiro
POST           /api/dashboard/refresh-kpis
```

Os recursos CRUD tambem aceitam `GET /:id`, `PUT /:id` e `DELETE /:id`, exceto
recursos somente para consulta. A listagem aceita `q` para busca textual e
filtros suportados pelo recurso. O limite atual e de 500 registros por
resposta.

Alteracoes em usuarios e perfis exigem perfil `Administrador` ou `Diretor`.
Logs sao somente para consulta.

## Testes

Execute:

```powershell
python -m unittest discover -s tests -v
```

Ou, quando necessario:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" `
  -m unittest discover -s tests -v
```

O teste usa um banco SQLite temporario e uma porta HTTP aleatoria. Ele cobre
login, clientes, leads, conversao, oportunidade, proposta, contrato, baixa
financeira, comissao, dashboard e auditoria.

## PostgreSQL / Supabase

Arquivos disponiveis:

- `schema_supabase.sql`: schema consolidado
- `database/schema.sql`: estrutura PostgreSQL
- `database/seed.sql`: carga inicial
- `database/indexes.sql`: indices adicionais
- `database/views.sql`: materialized view e funcao de atualizacao
- `supabase/migrations/20260608190000_crm_corporativo.sql`: migration da CLI
- `verifica_supabase.sql`: consultas para validar a instalacao

No SQL Editor do Supabase, execute o schema e depois `database/seed.sql`.

Com a Supabase CLI configurada:

```bash
supabase db push
```

A view `vw_kpi_vendas` consolida faturamento e contratos pagos por mes. Para
atualiza-la no PostgreSQL:

```sql
SELECT refresh_kpi_vendas();
```

No SQLite, os KPIs sao calculados em tempo real. Por isso,
`POST /api/dashboard/refresh-kpis` apenas retorna uma confirmacao.

O frontend local nao utiliza diretamente a chave publica do Supabase. As
operacoes da interface passam pela API Python.

## Observacoes de seguranca

- O servidor padrao escuta apenas em `127.0.0.1`.
- Nao use a chave `JWT_SECRET` padrao em producao.
- Altere as credenciais da carga inicial.
- Use HTTPS e um proxy reverso ao publicar o sistema.
- Faca backup do SQLite antes de apagar ou substituir o banco.
- Revise permissoes, CORS, expiracao de sessao e estrategia de deploy antes de
  disponibilizar a aplicacao publicamente.
# Banco-de-Dados-CRM
# Banco-de-Dados-CRM
