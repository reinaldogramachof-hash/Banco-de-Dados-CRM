import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import uuid
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / os.getenv("DATABASE_FILE", "crm_corporativo.db")
SCHEMA_PATH = BASE_DIR / "schema.sql"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
JWT_SECRET = os.getenv("JWT_SECRET", "troque-esta-chave-em-producao").encode()
PUBLIC_PATHS = {"/api/auth/login", "/api/health"}

RESOURCES = {
    "perfis": {
        "fields": ("nome", "descricao"),
        "required": ("nome",),
        "admin": True,
    },
    "usuarios": {
        "fields": ("nome", "email", "senha_hash", "perfil_id", "ativo"),
        "required": ("nome", "email", "perfil_id"),
        "admin": True,
        "joins": "LEFT JOIN perfis p ON p.id = t.perfil_id",
        "select": "t.*, p.nome AS perfil_nome",
    },
    "clientes": {
        "fields": ("tipo", "nome", "cpf_cnpj", "telefone", "email", "segmento", "status"),
        "required": ("tipo", "nome", "cpf_cnpj", "status"),
        "search": ("nome", "cpf_cnpj", "segmento", "status"),
    },
    "enderecos": {
        "fields": ("cliente_id", "cep", "logradouro", "numero", "bairro", "cidade", "estado"),
        "required": ("cliente_id", "logradouro", "cidade", "estado"),
    },
    "contatos": {
        "fields": ("cliente_id", "nome", "cargo", "telefone", "email"),
        "required": ("cliente_id", "nome"),
    },
    "leads": {
        "fields": ("nome", "empresa", "telefone", "email", "origem", "status", "responsavel_id", "cliente_id"),
        "required": ("nome", "origem", "status", "responsavel_id"),
        "search": ("nome", "empresa", "origem", "status", "responsavel_id"),
        "joins": "LEFT JOIN usuarios u ON u.id = t.responsavel_id",
        "select": "t.*, u.nome AS responsavel_nome",
    },
    "oportunidades": {
        "fields": ("cliente_id", "lead_id", "responsavel_id", "titulo", "valor_estimado", "etapa", "probabilidade", "previsao_fechamento"),
        "required": ("cliente_id", "responsavel_id", "titulo", "valor_estimado", "etapa", "probabilidade"),
        "search": ("titulo", "etapa", "cliente_id", "responsavel_id"),
        "joins": "LEFT JOIN clientes c ON c.id = t.cliente_id LEFT JOIN usuarios u ON u.id = t.responsavel_id",
        "select": "t.*, c.nome AS cliente_nome, u.nome AS responsavel_nome, ROUND(t.valor_estimado * t.probabilidade / 100.0, 2) AS valor_ponderado",
    },
    "propostas": {
        "fields": ("oportunidade_id", "valor", "validade", "status"),
        "required": ("oportunidade_id", "valor", "validade", "status"),
        "search": ("status", "oportunidade_id"),
        "joins": "LEFT JOIN oportunidades o ON o.id = t.oportunidade_id",
        "select": "t.*, o.titulo AS oportunidade_titulo",
    },
    "contratos": {
        "fields": ("cliente_id", "proposta_id", "responsavel_id", "numero", "valor", "data_inicio", "data_fim", "status"),
        "required": ("cliente_id", "valor", "data_inicio", "status"),
        "search": ("numero", "status", "cliente_id"),
        "joins": "LEFT JOIN clientes c ON c.id = t.cliente_id LEFT JOIN usuarios u ON u.id = t.responsavel_id",
        "select": "t.*, c.nome AS cliente_nome, u.nome AS responsavel_nome",
    },
    "atividades": {
        "fields": ("cliente_id", "usuario_id", "tipo", "titulo", "descricao", "data_agendada", "status"),
        "required": ("cliente_id", "usuario_id", "tipo", "titulo", "data_agendada", "status"),
        "search": ("tipo", "status", "cliente_id", "usuario_id"),
        "joins": "LEFT JOIN clientes c ON c.id = t.cliente_id LEFT JOIN usuarios u ON u.id = t.usuario_id",
        "select": "t.*, c.nome AS cliente_nome, u.nome AS usuario_nome",
    },
    "contas-receber": {
        "table": "contas_receber",
        "fields": ("cliente_id", "contrato_id", "valor", "vencimento", "pagamento", "status"),
        "required": ("cliente_id", "valor", "vencimento", "status"),
        "search": ("status", "cliente_id", "contrato_id"),
        "joins": "LEFT JOIN clientes c ON c.id = t.cliente_id LEFT JOIN contratos ct ON ct.id = t.contrato_id",
        "select": "t.*, c.nome AS cliente_nome, ct.numero AS contrato_numero",
    },
    "comissoes": {
        "fields": ("usuario_id", "contrato_id", "percentual", "valor"),
        "required": ("usuario_id", "contrato_id", "percentual", "valor"),
        "search": ("usuario_id", "contrato_id"),
        "joins": "LEFT JOIN usuarios u ON u.id = t.usuario_id LEFT JOIN contratos c ON c.id = t.contrato_id",
        "select": "t.*, u.nome AS usuario_nome, c.numero AS contrato_numero",
    },
    "logs": {
        "fields": (),
        "readonly": True,
        "search": ("usuario_id", "tabela", "acao"),
        "joins": "LEFT JOIN usuarios u ON u.id = t.usuario_id",
        "select": "t.*, u.nome AS usuario_nome",
    },
}

ENUMS = {
    "clientes.tipo": {"PF", "PJ"},
    "clientes.status": {"ATIVO", "INATIVO", "PROSPECTO"},
    "leads.origem": {"Google", "LinkedIn", "Indicacao", "Instagram", "Evento", "Outro"},
    "leads.status": {"NOVO", "QUALIFICADO", "CONVERTIDO", "DESCARTADO"},
    "oportunidades.etapa": {"PROSPECCAO", "QUALIFICACAO", "PROPOSTA", "NEGOCIACAO", "FECHAMENTO", "PERDIDA"},
    "propostas.status": {"RASCUNHO", "ENVIADA", "APROVADA", "RECUSADA", "EXPIRADA"},
    "contratos.status": {"ATIVO", "ENCERRADO", "CANCELADO", "SUSPENSO"},
    "atividades.tipo": {"LIGACAO", "REUNIAO", "VISITA", "FOLLOW_UP", "EMAIL", "PROPOSTA"},
    "atividades.status": {"PENDENTE", "CONCLUIDA", "CANCELADA"},
    "contas_receber.status": {"ABERTO", "PAGO", "VENCIDO", "CANCELADO"},
}


class ApiError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def password_hash(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return f"pbkdf2_sha256$210000${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def password_ok(password, stored):
    try:
        algorithm, iterations, salt, expected = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return hmac.compare_digest(hashlib.sha256(password.encode()).hexdigest(), stored)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.urlsafe_b64decode(salt), int(iterations))
        return hmac.compare_digest(base64.urlsafe_b64encode(digest).decode(), expected)
    except (ValueError, TypeError):
        return False


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def sign_token(user):
    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = b64(json.dumps({
        "sub": user["id"], "nome": user["nome"], "perfil": user["perfil_nome"],
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=8)).timestamp()),
    }, separators=(",", ":")).encode())
    signature = b64(hmac.new(JWT_SECRET, f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def verify_token(token):
    try:
        header, payload, signature = token.split(".")
        expected = b64(hmac.new(JWT_SECRET, f"{header}.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if data["exp"] < datetime.now(timezone.utc).timestamp():
            raise ValueError
        return data
    except (ValueError, KeyError, json.JSONDecodeError):
        raise ApiError(HTTPStatus.UNAUTHORIZED, "Token invalido ou expirado.")


def as_dict(row):
    if not row:
        return None
    result = dict(row)
    for field in ("dados_anteriores", "dados_novos"):
        if result.get(field):
            try:
                result[field] = json.loads(result[field])
            except json.JSONDecodeError:
                pass
    if "ativo" in result:
        result["ativo"] = bool(result["ativo"])
    result.pop("senha_hash", None)
    return result


def audit(conn, user_id, table, record_id, action, before=None, after=None):
    conn.execute(
        "INSERT INTO logs (usuario_id, tabela, registro_id, acao, dados_anteriores, dados_novos) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, table, str(record_id) if record_id else None, action,
         json.dumps(before, ensure_ascii=False, default=str) if before else None,
         json.dumps(after, ensure_ascii=False, default=str) if after else None),
    )


def initialize_database():
    with connect() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
            seed_database(conn)


def seed_database(conn):
    profile_ids = {r["nome"]: r["id"] for r in conn.execute("SELECT id, nome FROM perfis")}
    people = [
        ("Joao Silva", "joao@crm.local", "Administrador"),
        ("Maria Souza", "maria@crm.local", "Gerente"),
        ("Carlos Lima", "carlos@crm.local", "Vendedor"),
        ("Ana Costa", "ana@crm.local", "Vendedor"),
        ("Pedro Santos", "pedro@crm.local", "Supervisor"),
    ]
    users = {}
    for name, email, profile in people:
        user_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO usuarios (id, nome, email, senha_hash, perfil_id, ativo) VALUES (?, ?, ?, ?, ?, 1)",
            (user_id, name, email, password_hash("Senha@123"), profile_ids[profile]),
        )
        users[email] = user_id

    segments = ["Tecnologia", "Saude", "Educacao", "Industria"]
    clients = []
    for i in range(1, 21):
        client_id = str(uuid.uuid4())
        clients.append(client_id)
        conn.execute(
            "INSERT INTO clientes (id, tipo, nome, cpf_cnpj, telefone, email, segmento, status) VALUES (?, 'PJ', ?, ?, ?, ?, ?, 'ATIVO')",
            (client_id, f"Empresa Corporativa {i:02d}", f"10.000.000/0001-{i:02d}", f"(11) 4000-{i:04d}",
             f"contato{i}@empresa.local", segments[(i - 1) % 4]),
        )
        conn.execute(
            "INSERT INTO enderecos (cliente_id, cep, logradouro, numero, bairro, cidade, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (client_id, f"0100{i:04d}", "Avenida Corporativa", str(100 + i), "Centro", "Sao Paulo", "SP"),
        )
        for c in range(1, 3):
            conn.execute(
                "INSERT INTO contatos (cliente_id, nome, cargo, telefone, email) VALUES (?, ?, ?, ?, ?)",
                (client_id, f"Contato {c} Empresa {i}", "Gestor" if c == 1 else "Compras",
                 f"(11) 9000-{i:02d}{c:02d}", f"contato{c}.empresa{i}@crm.local"),
            )

    salespeople = [users["carlos@crm.local"], users["ana@crm.local"]]
    origins = ["Google", "LinkedIn", "Indicacao", "Instagram"]
    lead_statuses = ["CONVERTIDO", "NOVO", "QUALIFICADO"]
    for i in range(1, 51):
        conn.execute(
            "INSERT INTO leads (nome, empresa, telefone, email, origem, status, responsavel_id, cliente_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (f"Lead {i:02d}", f"Prospect {i:02d}", f"(21) 98888-{i:04d}", f"lead{i}@crm.local",
             origins[(i - 1) % 4], lead_statuses[(i - 1) % 3], salespeople[i % 2],
             clients[(i - 1) % len(clients)] if lead_statuses[(i - 1) % 3] == "CONVERTIDO" else None),
        )

    today = date.today()
    for i in range(15):
        contract_id = str(uuid.uuid4())
        value = 12000 + i * 1750
        responsible = salespeople[i % 2]
        number = f"CTR-{today.year}-{i + 1:04d}"
        conn.execute(
            "INSERT INTO contratos (id, cliente_id, responsavel_id, numero, valor, data_inicio, data_fim, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'ATIVO')",
            (contract_id, clients[i], responsible, number, value, str(today - timedelta(days=i * 12)),
             str(today + timedelta(days=365))),
        )
        conn.execute(
            "INSERT INTO contas_receber (cliente_id, contrato_id, valor, vencimento, pagamento, status) VALUES (?, ?, ?, ?, ?, 'PAGO')",
            (clients[i], contract_id, value, str(today - timedelta(days=i * 10)), str(today - timedelta(days=i * 10 - 2))),
        )
        conn.execute(
            "INSERT INTO comissoes (usuario_id, contrato_id, percentual, valor) VALUES (?, ?, 5, ?)",
            (responsible, contract_id, round(value * 0.05, 2)),
        )
        conn.execute(
            "INSERT INTO oportunidades (cliente_id, responsavel_id, titulo, valor_estimado, etapa, probabilidade, previsao_fechamento) VALUES (?, ?, ?, ?, 'FECHAMENTO', 100, ?)",
            (clients[i], responsible, f"Projeto corporativo {i + 1}", value, str(today + timedelta(days=20))),
        )

    for i in range(10):
        conn.execute(
            "INSERT INTO atividades (cliente_id, usuario_id, tipo, titulo, descricao, data_agendada, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (clients[i], salespeople[i % 2], "REUNIAO", f"Reuniao de acompanhamento {i + 1}",
             "Revisao comercial da conta", str(datetime.now() + timedelta(days=i - 3)),
             "CONCLUIDA" if i < 2 else "PENDENTE"),
        )


class Handler(SimpleHTTPRequestHandler):
    server_version = "CRMCorporativo/1.0"

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def do_PUT(self):
        self.dispatch("PUT")

    def do_PATCH(self):
        self.dispatch("PUT")

    def do_DELETE(self):
        self.dispatch("DELETE")

    def dispatch(self, method):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if not path.startswith("/api/"):
            return super().do_GET() if method == "GET" else self.send_error(404)
        try:
            user = None if path in PUBLIC_PATHS else self.authenticate()
            data = self.read_json() if method in {"POST", "PUT"} else {}
            response, status = self.route(method, path, parse_qs(parsed.query), data, user)
            self.send_json(response, status)
        except ApiError as exc:
            self.send_json({"erro": exc.message}, exc.status)
        except sqlite3.IntegrityError as exc:
            self.send_json({"erro": self.integrity_message(exc)}, HTTPStatus.CONFLICT)
        except (ValueError, TypeError, KeyError) as exc:
            self.send_json({"erro": f"Dados invalidos: {exc}"}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            print(f"Erro: {exc}")
            self.send_json({"erro": "Erro interno do servidor."}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def route(self, method, path, query, data, user):
        if path == "/api/health":
            return {"status": "ok", "banco": DB_PATH.name}, 200
        if path == "/api/auth/login" and method == "POST":
            return self.login(data), 200
        if path == "/api/auth/me" and method == "GET":
            return self.current_user(user), 200
        if path.startswith("/api/dashboard"):
            return self.dashboard(method, path, user), 200
        if path == "/api/atividades/proximas" and method == "GET":
            return self.activity_list("datetime(t.data_agendada) >= datetime('now') AND t.status = 'PENDENTE'"), 200
        if path == "/api/atividades/atrasadas" and method == "GET":
            return self.activity_list("datetime(t.data_agendada) < datetime('now') AND t.status = 'PENDENTE'"), 200
        if path == "/api/oportunidades/funil/resumo" and method == "GET":
            return self.funnel(), 200

        parts = path.removeprefix("/api/").split("/")
        resource = parts[0]
        record_id = parts[1] if len(parts) > 1 else None
        action = parts[2] if len(parts) > 2 else None

        if resource == "clientes" and len(parts) == 3 and parts[2] in {"enderecos", "contatos"}:
            query = {**query, "cliente_id": [parts[1]]}
            resource, record_id = parts[2], None
        if resource == "leads" and action == "converter" and method == "POST":
            return self.convert_lead(record_id, data, user), 201
        if resource == "propostas" and action == "aprovar" and method == "POST":
            return self.approve_proposal(record_id, data, user), 201
        if resource == "contas-receber" and action == "baixar" and method == "POST":
            return self.pay_receivable(record_id, data, user), 200
        if resource == "comissoes" and record_id == "gerar" and action and method == "POST":
            return self.generate_commission(action, data, user), 201

        if resource not in RESOURCES:
            raise ApiError(HTTPStatus.NOT_FOUND, "Rota nao encontrada.")
        config = RESOURCES[resource]
        self.authorize(config, user, method)
        if method == "GET":
            return (self.get_one(resource, record_id) if record_id else self.list_records(resource, query)), 200
        if method == "POST" and not record_id:
            return self.create_record(resource, data, user), 201
        if method == "PUT" and record_id:
            return self.update_record(resource, record_id, data, user), 200
        if method == "DELETE" and record_id:
            return self.delete_record(resource, record_id, user), 200
        raise ApiError(HTTPStatus.NOT_FOUND, "Rota nao encontrada.")

    def authenticate(self):
        header = self.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise ApiError(HTTPStatus.UNAUTHORIZED, "Autenticacao obrigatoria.")
        return verify_token(header[7:])

    def authorize(self, config, user, method):
        if config.get("readonly") and method != "GET":
            raise ApiError(HTTPStatus.METHOD_NOT_ALLOWED, "Recurso somente para consulta.")
        if config.get("admin") and method != "GET" and user["perfil"] not in {"Administrador", "Diretor"}:
            raise ApiError(HTTPStatus.FORBIDDEN, "Perfil sem permissao para esta operacao.")

    def login(self, data):
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("senha", ""))
        with connect() as conn:
            row = conn.execute(
                "SELECT u.*, p.nome AS perfil_nome FROM usuarios u JOIN perfis p ON p.id = u.perfil_id WHERE lower(u.email) = ?",
                (email,),
            ).fetchone()
            if not row or not password_ok(password, row["senha_hash"]):
                raise ApiError(HTTPStatus.UNAUTHORIZED, "Email ou senha invalidos.")
            if not row["ativo"]:
                raise ApiError(HTTPStatus.FORBIDDEN, "Usuario inativo.")
            audit(conn, row["id"], "usuarios", row["id"], "LOGIN")
            user = dict(row)
            return {"token": sign_token(user), "usuario": as_dict(row)}

    def current_user(self, token_user):
        with connect() as conn:
            row = conn.execute(
                "SELECT u.*, p.nome AS perfil_nome FROM usuarios u JOIN perfis p ON p.id = u.perfil_id WHERE u.id = ? AND u.ativo = 1",
                (token_user["sub"],),
            ).fetchone()
        if not row:
            raise ApiError(HTTPStatus.UNAUTHORIZED, "Usuario indisponivel.")
        return as_dict(row)

    def list_records(self, resource, query):
        config = RESOURCES[resource]
        table = config.get("table", resource.replace("-", "_"))
        select = config.get("select", "t.*")
        joins = config.get("joins", "")
        conditions, params = [], []
        allowed = set(config.get("search", ())) | {"cliente_id", "usuario_id", "responsavel_id", "status"}
        for key, values in query.items():
            if key == "q" and values[0] and config.get("search"):
                searchable = [f"CAST(t.{field} AS TEXT) LIKE ?" for field in config["search"]]
                conditions.append(f"({' OR '.join(searchable)})")
                params.extend([f"%{values[0]}%"] * len(searchable))
            elif key in allowed and values[0]:
                conditions.append(f"t.{key} = ?")
                params.append(values[0])
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        order = "t.criado_em DESC" if resource != "perfis" else "t.nome"
        with connect() as conn:
            rows = conn.execute(f"SELECT {select} FROM {table} t {joins}{where} ORDER BY {order} LIMIT 500", params).fetchall()
        return [as_dict(row) for row in rows]

    def get_one(self, resource, record_id):
        config = RESOURCES[resource]
        table = config.get("table", resource.replace("-", "_"))
        with connect() as conn:
            row = conn.execute(
                f"SELECT {config.get('select', 't.*')} FROM {table} t {config.get('joins', '')} WHERE t.id = ?",
                (record_id,),
            ).fetchone()
        if not row:
            raise ApiError(HTTPStatus.NOT_FOUND, "Registro nao encontrado.")
        result = as_dict(row)
        if resource == "clientes":
            with connect() as conn:
                for child in ("enderecos", "contatos", "oportunidades", "contratos", "atividades", "contas_receber"):
                    result[child] = [as_dict(r) for r in conn.execute(f"SELECT * FROM {child} WHERE cliente_id = ? ORDER BY criado_em DESC", (record_id,))]
        return result

    def validate(self, resource, data, partial=False):
        config = RESOURCES[resource]
        clean = {field: data[field] for field in config["fields"] if field in data}
        if "senha" in data and resource == "usuarios":
            if len(data["senha"]) < 8:
                raise ApiError(400, "A senha deve ter pelo menos 8 caracteres.")
            clean["senha_hash"] = password_hash(data["senha"])
        if resource == "usuarios":
            clean.pop("senha_hash", None) if "senha" not in data else None
            if "email" in clean and ("@" not in clean["email"] or "." not in clean["email"].split("@")[-1]):
                raise ApiError(400, "Email invalido.")
            if "ativo" in clean:
                clean["ativo"] = 1 if clean["ativo"] else 0
        for field in config["required"]:
            if not partial and (field not in clean or clean[field] in (None, "")):
                raise ApiError(400, f"Campo obrigatorio: {field}.")
        for field, value in clean.items():
            allowed = ENUMS.get(f"{resource.replace('-', '_')}.{field}")
            if allowed and value not in allowed:
                raise ApiError(400, f"Valor invalido para {field}.")
        for field in ("valor", "valor_estimado", "percentual"):
            if field in clean and float(clean[field]) < 0:
                raise ApiError(400, f"{field} nao pode ser negativo.")
        if "probabilidade" in clean and not 0 <= int(clean["probabilidade"]) <= 100:
            raise ApiError(400, "Probabilidade deve estar entre 0 e 100.")
        if resource == "contas-receber" and clean.get("status") == "PAGO" and not clean.get("pagamento"):
            clean["pagamento"] = str(date.today())
        return clean

    def create_record(self, resource, data, user):
        config = RESOURCES[resource]
        table = config.get("table", resource.replace("-", "_"))
        if resource == "usuarios" and not data.get("senha"):
            raise ApiError(400, "A senha e obrigatoria para novos usuarios.")
        prepared = dict(data)
        if resource == "contratos" and not prepared.get("numero"):
            prepared["numero"] = self.next_contract_number()
        clean = self.validate(resource, prepared)
        fields = list(clean)
        record_id = str(uuid.uuid4()) if table != "perfis" else None
        if record_id:
            fields.insert(0, "id")
            clean["id"] = record_id
        with connect() as conn:
            cursor = conn.execute(
                f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
                [clean[field] for field in fields],
            )
            record_id = record_id or cursor.lastrowid
            row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
            audit(conn, user["sub"], table, record_id, "CREATE", after=as_dict(row))
        return self.get_one(resource, record_id)

    def update_record(self, resource, record_id, data, user):
        config = RESOURCES[resource]
        table = config.get("table", resource.replace("-", "_"))
        clean = self.validate(resource, data, partial=True)
        if not clean:
            raise ApiError(400, "Nenhum campo valido informado.")
        with connect() as conn:
            before_row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
            if not before_row:
                raise ApiError(404, "Registro nao encontrado.")
            if "atualizado_em" in {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}:
                clean["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
            conn.execute(
                f"UPDATE {table} SET {', '.join(f'{field} = ?' for field in clean)} WHERE id = ?",
                [*clean.values(), record_id],
            )
            after_row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
            action = "STATUS_CHANGE" if "status" in clean and clean["status"] != before_row["status"] else "UPDATE"
            audit(conn, user["sub"], table, record_id, action, as_dict(before_row), as_dict(after_row))
        return self.get_one(resource, record_id)

    def delete_record(self, resource, record_id, user):
        table = RESOURCES[resource].get("table", resource.replace("-", "_"))
        with connect() as conn:
            row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
            if not row:
                raise ApiError(404, "Registro nao encontrado.")
            before = as_dict(row)
            conn.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
            audit(conn, user["sub"], table, record_id, "DELETE", before=before)
        return {"ok": True}

    def convert_lead(self, lead_id, data, user):
        with connect() as conn:
            lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
            if not lead:
                raise ApiError(404, "Lead nao encontrado.")
            if lead["status"] == "CONVERTIDO":
                raise ApiError(409, "Lead ja convertido.")
            client_id = str(uuid.uuid4())
            document = data.get("cpf_cnpj") or f"LEAD-{lead_id[:12]}"
            conn.execute(
                "INSERT INTO clientes (id, tipo, nome, cpf_cnpj, telefone, email, segmento, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'ATIVO')",
                (client_id, data.get("tipo", "PJ"), data.get("nome") or lead["empresa"] or lead["nome"],
                 document, lead["telefone"], lead["email"], data.get("segmento")),
            )
            opportunity_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO oportunidades (id, cliente_id, lead_id, responsavel_id, titulo, valor_estimado, etapa, probabilidade, previsao_fechamento) VALUES (?, ?, ?, ?, ?, ?, 'QUALIFICACAO', 25, ?)",
                (opportunity_id, client_id, lead_id, lead["responsavel_id"],
                 data.get("titulo") or f"Oportunidade - {lead['empresa'] or lead['nome']}",
                 float(data.get("valor_estimado", 0)), data.get("previsao_fechamento")),
            )
            conn.execute("UPDATE leads SET status = 'CONVERTIDO', cliente_id = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?", (client_id, lead_id))
            audit(conn, user["sub"], "leads", lead_id, "STATUS_CHANGE", as_dict(lead), {"status": "CONVERTIDO", "cliente_id": client_id})
            audit(conn, user["sub"], "clientes", client_id, "CREATE", after={"origem": "lead", "lead_id": lead_id})
        return {"cliente_id": client_id, "oportunidade_id": opportunity_id}

    def approve_proposal(self, proposal_id, data, user):
        with connect() as conn:
            proposal = conn.execute(
                "SELECT p.*, o.cliente_id, o.responsavel_id FROM propostas p JOIN oportunidades o ON o.id = p.oportunidade_id WHERE p.id = ?",
                (proposal_id,),
            ).fetchone()
            if not proposal:
                raise ApiError(404, "Proposta nao encontrada.")
            if proposal["status"] == "APROVADA":
                existing = conn.execute("SELECT * FROM contratos WHERE proposta_id = ?", (proposal_id,)).fetchone()
                if existing:
                    return as_dict(existing)
            contract_id = str(uuid.uuid4())
            number = self.next_contract_number(conn)
            start = data.get("data_inicio", str(date.today()))
            conn.execute("UPDATE propostas SET status = 'APROVADA', atualizado_em = CURRENT_TIMESTAMP WHERE id = ?", (proposal_id,))
            conn.execute(
                "INSERT INTO contratos (id, cliente_id, proposta_id, responsavel_id, numero, valor, data_inicio, data_fim, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ATIVO')",
                (contract_id, proposal["cliente_id"], proposal_id, proposal["responsavel_id"], number,
                 proposal["valor"], start, data.get("data_fim")),
            )
            audit(conn, user["sub"], "propostas", proposal_id, "STATUS_CHANGE", as_dict(proposal), {"status": "APROVADA"})
            audit(conn, user["sub"], "contratos", contract_id, "CREATE", after={"numero": number, "valor": proposal["valor"]})
        return self.get_one("contratos", contract_id)

    def pay_receivable(self, receivable_id, data, user):
        payment_date = data.get("pagamento") or str(date.today())
        with connect() as conn:
            before = conn.execute("SELECT * FROM contas_receber WHERE id = ?", (receivable_id,)).fetchone()
            if not before:
                raise ApiError(404, "Conta nao encontrada.")
            conn.execute("UPDATE contas_receber SET status = 'PAGO', pagamento = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?", (payment_date, receivable_id))
            after = conn.execute("SELECT * FROM contas_receber WHERE id = ?", (receivable_id,)).fetchone()
            audit(conn, user["sub"], "contas_receber", receivable_id, "STATUS_CHANGE", as_dict(before), as_dict(after))
        return self.get_one("contas-receber", receivable_id)

    def generate_commission(self, contract_id, data, user):
        percentage = float(data.get("percentual", 5))
        with connect() as conn:
            contract = conn.execute("SELECT * FROM contratos WHERE id = ?", (contract_id,)).fetchone()
            if not contract:
                raise ApiError(404, "Contrato nao encontrado.")
            seller_id = data.get("usuario_id") or contract["responsavel_id"]
            if not seller_id:
                raise ApiError(400, "Informe o vendedor da comissao.")
            value = round(contract["valor"] * percentage / 100, 2)
            commission_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO comissoes (id, usuario_id, contrato_id, percentual, valor) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(contrato_id) DO UPDATE SET usuario_id=excluded.usuario_id, percentual=excluded.percentual, valor=excluded.valor",
                (commission_id, seller_id, contract_id, percentage, value),
            )
            row = conn.execute("SELECT * FROM comissoes WHERE contrato_id = ?", (contract_id,)).fetchone()
            audit(conn, user["sub"], "comissoes", row["id"], "CREATE", after=as_dict(row))
        return as_dict(row)

    def next_contract_number(self, conn=None):
        own = conn is None
        conn = conn or connect()
        try:
            count = conn.execute("SELECT COUNT(*) FROM contratos WHERE numero LIKE ?", (f"CTR-{date.today().year}-%",)).fetchone()[0]
            return f"CTR-{date.today().year}-{count + 1:04d}"
        finally:
            if own:
                conn.close()

    def dashboard(self, method, path, user):
        if method == "POST" and path == "/api/dashboard/refresh-kpis":
            return {"ok": True, "mensagem": "SQLite calcula os KPIs em tempo real."}
        with connect() as conn:
            if path == "/api/dashboard/faturamento-mensal":
                return [dict(r) for r in conn.execute(
                    "SELECT substr(pagamento, 1, 7) AS mes, ROUND(SUM(valor), 2) AS faturamento, COUNT(DISTINCT contrato_id) AS contratos "
                    "FROM contas_receber WHERE status='PAGO' GROUP BY substr(pagamento, 1, 7) ORDER BY mes"
                )]
            group_routes = {
                "/api/dashboard/leads-status": ("leads", "status"),
                "/api/dashboard/leads-origem": ("leads", "origem"),
                "/api/dashboard/oportunidades-etapa": ("oportunidades", "etapa"),
                "/api/dashboard/propostas-status": ("propostas", "status"),
                "/api/dashboard/contratos-status": ("contratos", "status"),
            }
            if path in group_routes:
                table, field = group_routes[path]
                return [dict(r) for r in conn.execute(f"SELECT {field} AS categoria, COUNT(*) AS total FROM {table} GROUP BY {field} ORDER BY total DESC")]
            if path == "/api/dashboard/financeiro":
                return self.financial_kpis(conn)
            if path != "/api/dashboard/kpis":
                raise ApiError(404, "Indicador nao encontrado.")
            result = {
                "clientes_ativos": conn.execute("SELECT COUNT(*) FROM clientes WHERE status='ATIVO'").fetchone()[0],
                "total_leads": conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0],
                "oportunidades_abertas": conn.execute("SELECT COALESCE(SUM(valor_estimado),0) FROM oportunidades WHERE etapa NOT IN ('FECHAMENTO','PERDIDA')").fetchone()[0],
                "pipeline_ponderado": conn.execute("SELECT COALESCE(SUM(valor_estimado * probabilidade / 100.0),0) FROM oportunidades WHERE etapa NOT IN ('FECHAMENTO','PERDIDA')").fetchone()[0],
                "atividades_pendentes": conn.execute("SELECT COUNT(*) FROM atividades WHERE status='PENDENTE'").fetchone()[0],
                "atividades_atrasadas": conn.execute("SELECT COUNT(*) FROM atividades WHERE status='PENDENTE' AND datetime(data_agendada)<datetime('now')").fetchone()[0],
                "comissoes_previstas": conn.execute("SELECT COALESCE(SUM(valor),0) FROM comissoes").fetchone()[0],
                "financeiro": self.financial_kpis(conn),
                "faturamento_mensal": self.dashboard("GET", "/api/dashboard/faturamento-mensal", user),
                "leads_status": self.dashboard("GET", "/api/dashboard/leads-status", user),
                "leads_origem": self.dashboard("GET", "/api/dashboard/leads-origem", user),
                "oportunidades_etapa": self.dashboard("GET", "/api/dashboard/oportunidades-etapa", user),
                "contratos_status": self.dashboard("GET", "/api/dashboard/contratos-status", user),
                "propostas_status": self.dashboard("GET", "/api/dashboard/propostas-status", user),
                "comissoes_vendedor": [dict(r) for r in conn.execute(
                    "SELECT u.nome AS vendedor, ROUND(SUM(c.valor),2) AS total FROM comissoes c JOIN usuarios u ON u.id=c.usuario_id GROUP BY u.id ORDER BY total DESC"
                )],
            }
            return result

    def financial_kpis(self, conn):
        row = conn.execute(
            "SELECT ROUND(COALESCE(SUM(CASE WHEN status='ABERTO' THEN valor ELSE 0 END),0),2) AS aberto, "
            "ROUND(COALESCE(SUM(CASE WHEN status='PAGO' THEN valor ELSE 0 END),0),2) AS pago, "
            "ROUND(COALESCE(SUM(CASE WHEN status='VENCIDO' OR (status='ABERTO' AND date(vencimento)<date('now')) THEN valor ELSE 0 END),0),2) AS vencido "
            "FROM contas_receber"
        ).fetchone()
        return dict(row)

    def funnel(self):
        with connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT etapa, COUNT(*) AS quantidade, ROUND(SUM(valor_estimado),2) AS valor, "
                "ROUND(SUM(valor_estimado * probabilidade / 100.0),2) AS ponderado FROM oportunidades GROUP BY etapa ORDER BY "
                "CASE etapa WHEN 'PROSPECCAO' THEN 1 WHEN 'QUALIFICACAO' THEN 2 WHEN 'PROPOSTA' THEN 3 WHEN 'NEGOCIACAO' THEN 4 WHEN 'FECHAMENTO' THEN 5 ELSE 6 END"
            )]

    def activity_list(self, condition):
        config = RESOURCES["atividades"]
        with connect() as conn:
            rows = conn.execute(
                f"SELECT {config['select']} FROM atividades t {config['joins']} WHERE {condition} ORDER BY t.data_agendada LIMIT 100"
            ).fetchall()
        return [as_dict(r) for r in rows]

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            raise ApiError(400, "JSON invalido.")

    def send_json(self, data, status=200):
        content = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    @staticmethod
    def integrity_message(exc):
        text = str(exc)
        if "UNIQUE constraint failed" in text:
            return "Ja existe um registro com este valor unico."
        if "FOREIGN KEY constraint failed" in text:
            return "O registro esta relacionado a outros dados ou a referencia informada nao existe."
        if "CHECK constraint failed" in text:
            return "Um dos valores informados nao e permitido."
        if "NOT NULL constraint failed" in text:
            return "Preencha todos os campos obrigatorios."
        return "Nao foi possivel salvar o registro."


if __name__ == "__main__":
    initialize_database()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"CRM Corporativo rodando em http://{HOST}:{PORT}")
    print("Acesso inicial: joao@crm.local / Senha@123")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
