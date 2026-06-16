import hashlib
import sqlite3
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "ufbra.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def criar_banco():
    with conectar() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def gerar_hash(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UFBRA - Cadastro de Usuarios")
        self.geometry("940x620")
        self.minsize(800, 520)

        self.usuario_selecionado = None
        self.perfis = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.configurar_estilo()
        self.criar_widgets()
        self.carregar_perfis()
        self.carregar_usuarios()

    def configurar_estilo(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Header.TFrame", background="#12372a")
        style.configure("HeaderTitle.TLabel", background="#12372a", foreground="#ffffff", font=("Segoe UI", 22, "bold"))
        style.configure("HeaderSubtitle.TLabel", background="#12372a", foreground="#d7f5e9", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def criar_widgets(self):
        cabecalho = ttk.Frame(self, padding=(18, 16), style="Header.TFrame")
        cabecalho.grid(row=0, column=0, sticky="ew")
        cabecalho.columnconfigure(0, weight=1)
        ttk.Label(cabecalho, text="UFBRA", style="HeaderTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            cabecalho,
            text="Sistema academico para cadastro, consulta e gerenciamento de usuarios",
            style="HeaderSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        form = ttk.Frame(self, padding=16)
        form.grid(row=1, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        ttk.Label(form, text="Nome").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.nome_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.nome_var).grid(row=0, column=1, sticky="ew", padx=(0, 16))

        ttk.Label(form, text="Email").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.email_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.email_var).grid(row=0, column=3, sticky="ew")

        ttk.Label(form, text="Senha").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(12, 0))
        self.senha_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.senha_var, show="*").grid(row=1, column=1, sticky="ew", padx=(0, 16), pady=(12, 0))

        ttk.Label(form, text="Perfil").grid(row=1, column=2, sticky="w", padx=(0, 8), pady=(12, 0))
        self.perfil_var = tk.StringVar()
        self.perfil_combo = ttk.Combobox(form, textvariable=self.perfil_var, state="readonly")
        self.perfil_combo.grid(row=1, column=3, sticky="ew", pady=(12, 0))

        self.ativo_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form, text="Usuario ativo", variable=self.ativo_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 0))

        botoes = ttk.Frame(form)
        botoes.grid(row=2, column=2, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(botoes, text="Salvar", command=self.salvar_usuario).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(botoes, text="Limpar", command=self.limpar_formulario).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(botoes, text="Excluir", command=self.excluir_usuario).grid(row=0, column=2)

        tabela_frame = ttk.Frame(self, padding=(16, 0, 16, 16))
        tabela_frame.grid(row=2, column=0, sticky="nsew")
        tabela_frame.columnconfigure(0, weight=1)
        tabela_frame.rowconfigure(0, weight=1)

        colunas = ("nome", "email", "perfil", "ativo", "criado_em")
        self.tabela = ttk.Treeview(tabela_frame, columns=colunas, show="headings")
        for coluna, texto in zip(colunas, ("Nome", "Email", "Perfil", "Ativo", "Criado em")):
            self.tabela.heading(coluna, text=texto)

        self.tabela.column("nome", width=180)
        self.tabela.column("email", width=220)
        self.tabela.column("perfil", width=140)
        self.tabela.column("ativo", width=70, anchor="center")
        self.tabela.column("criado_em", width=150)
        self.tabela.grid(row=0, column=0, sticky="nsew")
        self.tabela.bind("<<TreeviewSelect>>", self.selecionar_usuario)

        scroll = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tabela.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tabela.configure(yscrollcommand=scroll.set)

    def carregar_perfis(self):
        with conectar() as conn:
            self.perfis = conn.execute("SELECT id, nome FROM perfis ORDER BY nome").fetchall()

        nomes = [perfil["nome"] for perfil in self.perfis]
        self.perfil_combo["values"] = nomes
        if nomes:
            self.perfil_var.set(nomes[0])

    def carregar_usuarios(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        with conectar() as conn:
            usuarios = conn.execute(
                """
                SELECT u.id, u.nome, u.email, p.nome AS perfil, u.ativo, u.criado_em
                FROM usuarios u
                LEFT JOIN perfis p ON p.id = u.perfil_id
                ORDER BY u.criado_em DESC
                """
            ).fetchall()

        for usuario in usuarios:
            self.tabela.insert(
                "",
                "end",
                iid=usuario["id"],
                values=(
                    usuario["nome"],
                    usuario["email"],
                    usuario["perfil"] or "",
                    "Sim" if usuario["ativo"] else "Nao",
                    usuario["criado_em"],
                ),
            )

    def perfil_id_atual(self):
        nome = self.perfil_var.get()
        for perfil in self.perfis:
            if perfil["nome"] == nome:
                return perfil["id"]
        return None

    def salvar_usuario(self):
        nome = self.nome_var.get().strip()
        email = self.email_var.get().strip().lower()
        senha = self.senha_var.get()

        if not nome or not email:
            messagebox.showwarning("Campos obrigatorios", "Preencha nome e email.")
            return

        if self.usuario_selecionado is None and not senha:
            messagebox.showwarning("Campo obrigatorio", "Preencha a senha para cadastrar um usuario.")
            return

        dados = (nome, email, self.perfil_id_atual(), 1 if self.ativo_var.get() else 0)

        try:
            with conectar() as conn:
                if self.usuario_selecionado:
                    if senha:
                        conn.execute(
                            "UPDATE usuarios SET nome = ?, email = ?, perfil_id = ?, ativo = ?, senha_hash = ? WHERE id = ?",
                            (*dados, gerar_hash(senha), self.usuario_selecionado),
                        )
                    else:
                        conn.execute(
                            "UPDATE usuarios SET nome = ?, email = ?, perfil_id = ?, ativo = ? WHERE id = ?",
                            (*dados, self.usuario_selecionado),
                        )
                else:
                    conn.execute(
                        "INSERT INTO usuarios (id, nome, email, senha_hash, perfil_id, ativo) VALUES (?, ?, ?, ?, ?, ?)",
                        (str(uuid.uuid4()), nome, email, gerar_hash(senha), self.perfil_id_atual(), 1 if self.ativo_var.get() else 0),
                    )
        except sqlite3.IntegrityError:
            messagebox.showerror("Email duplicado", "Ja existe um usuario cadastrado com este email.")
            return

        self.limpar_formulario()
        self.carregar_usuarios()

    def selecionar_usuario(self, _event=None):
        selecionados = self.tabela.selection()
        if not selecionados:
            return

        self.usuario_selecionado = selecionados[0]
        valores = self.tabela.item(self.usuario_selecionado, "values")
        self.nome_var.set(valores[0])
        self.email_var.set(valores[1])
        self.perfil_var.set(valores[2])
        self.ativo_var.set(valores[3] == "Sim")
        self.senha_var.set("")

    def limpar_formulario(self):
        self.usuario_selecionado = None
        self.nome_var.set("")
        self.email_var.set("")
        self.senha_var.set("")
        self.ativo_var.set(True)
        if self.perfis:
            self.perfil_var.set(self.perfis[0]["nome"])
        self.tabela.selection_remove(self.tabela.selection())

    def excluir_usuario(self):
        if not self.usuario_selecionado:
            messagebox.showwarning("Selecao obrigatoria", "Selecione um usuario para excluir.")
            return

        if not messagebox.askyesno("Confirmar exclusao", "Deseja excluir o usuario selecionado?"):
            return

        with conectar() as conn:
            conn.execute("DELETE FROM usuarios WHERE id = ?", (self.usuario_selecionado,))

        self.limpar_formulario()
        self.carregar_usuarios()


if __name__ == "__main__":
    criar_banco()
    App().mainloop()
