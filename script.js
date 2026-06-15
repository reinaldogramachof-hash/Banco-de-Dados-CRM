const state = {
    token: localStorage.getItem("crm_token"),
    user: null,
    page: "dashboard",
    records: [],
    editing: null,
    references: {},
};

const modules = {
    dashboard: { label: "Dashboard", icon: "DB", kicker: "Visão executiva" },
    clientes: {
        label: "Clientes", icon: "CL", singular: "Cliente",
        columns: [["nome", "Cliente"], ["cpf_cnpj", "CPF/CNPJ"], ["segmento", "Segmento"], ["status", "Status"]],
        fields: [
            ["tipo", "Tipo", "select", ["PJ", "PF"]], ["nome", "Nome / Razão social", "text", null, true],
            ["cpf_cnpj", "CPF/CNPJ", "text", null, true], ["telefone", "Telefone"], ["email", "E-mail", "email"],
            ["segmento", "Segmento"], ["status", "Status", "select", ["ATIVO", "INATIVO", "PROSPECTO"]],
        ],
        action: ["Detalhes", showClientDetails],
    },
    leads: {
        label: "Leads", icon: "LD", singular: "Lead",
        columns: [["nome", "Lead"], ["empresa", "Empresa"], ["origem", "Origem"], ["status", "Status"], ["responsavel_nome", "Responsável"]],
        fields: [
            ["nome", "Nome", "text", null, true], ["empresa", "Empresa"], ["telefone", "Telefone"], ["email", "E-mail", "email"],
            ["origem", "Origem", "select", ["Google", "LinkedIn", "Indicação", "Instagram", "Evento", "Outro"]],
            ["status", "Status", "select", ["NOVO", "QUALIFICADO", "CONVERTIDO", "DESCARTADO"]],
            ["responsavel_id", "Responsável", "reference", "usuarios"],
        ],
        action: ["Converter", convertLead],
    },
    oportunidades: {
        label: "Oportunidades", icon: "OP", singular: "Oportunidade",
        columns: [["titulo", "Oportunidade"], ["cliente_nome", "Cliente"], ["etapa", "Etapa"], ["valor_estimado", "Valor"], ["probabilidade", "Probabilidade"], ["valor_ponderado", "Ponderado"]],
        fields: [
            ["cliente_id", "Cliente", "reference", "clientes"], ["responsavel_id", "Responsável", "reference", "usuarios"],
            ["titulo", "Título", "text", null, true], ["valor_estimado", "Valor estimado", "number", null, true],
            ["etapa", "Etapa", "select", ["PROSPECCAO", "QUALIFICACAO", "PROPOSTA", "NEGOCIACAO", "FECHAMENTO", "PERDIDA"]],
            ["probabilidade", "Probabilidade (%)", "number"], ["previsao_fechamento", "Previsão de fechamento", "date"],
        ],
    },
    propostas: {
        label: "Propostas", icon: "PR", singular: "Proposta",
        columns: [["oportunidade_titulo", "Oportunidade"], ["valor", "Valor"], ["validade", "Validade"], ["status", "Status"]],
        fields: [
            ["oportunidade_id", "Oportunidade", "reference", "oportunidades"], ["valor", "Valor", "number"],
            ["validade", "Validade", "date"], ["status", "Status", "select", ["RASCUNHO", "ENVIADA", "APROVADA", "RECUSADA", "EXPIRADA"]],
        ],
        action: ["Aprovar", approveProposal],
    },
    contratos: {
        label: "Contratos", icon: "CT", singular: "Contrato",
        columns: [["numero", "Número"], ["cliente_nome", "Cliente"], ["valor", "Valor"], ["data_inicio", "Inicio"], ["status", "Status"]],
        fields: [
            ["cliente_id", "Cliente", "reference", "clientes"], ["responsavel_id", "Responsável", "reference", "usuarios"],
            ["numero", "Número (automático se vazio)"], ["valor", "Valor", "number"], ["data_inicio", "Data de início", "date"],
            ["data_fim", "Data final", "date"], ["status", "Status", "select", ["ATIVO", "ENCERRADO", "CANCELADO", "SUSPENSO"]],
        ],
    },
    atividades: {
        label: "Atividades", icon: "AT", singular: "Atividade",
        columns: [["titulo", "Atividade"], ["cliente_nome", "Cliente"], ["tipo", "Tipo"], ["data_agendada", "Agendada"], ["status", "Status"]],
        fields: [
            ["cliente_id", "Cliente", "reference", "clientes"], ["usuario_id", "Responsável", "reference", "usuarios"],
            ["tipo", "Tipo", "select", ["LIGACAO", "REUNIAO", "VISITA", "FOLLOW_UP", "EMAIL", "PROPOSTA"]],
            ["titulo", "Título"], ["descricao", "Descrição", "textarea"], ["data_agendada", "Data e hora", "datetime-local"],
            ["status", "Status", "select", ["PENDENTE", "CONCLUIDA", "CANCELADA"]],
        ],
    },
    "contas-receber": {
        label: "Financeiro", icon: "FI", singular: "Conta a receber",
        columns: [["cliente_nome", "Cliente"], ["contrato_numero", "Contrato"], ["valor", "Valor"], ["vencimento", "Vencimento"], ["pagamento", "Pagamento"], ["status", "Status"]],
        fields: [
            ["cliente_id", "Cliente", "reference", "clientes"], ["contrato_id", "Contrato", "reference", "contratos"],
            ["valor", "Valor", "number"], ["vencimento", "Vencimento", "date"], ["pagamento", "Pagamento", "date"],
            ["status", "Status", "select", ["ABERTO", "PAGO", "VENCIDO", "CANCELADO"]],
        ],
        action: ["Dar baixa", payReceivable],
    },
    comissoes: {
        label: "Comissões", icon: "CM", singular: "Comissão",
        columns: [["usuario_nome", "Vendedor"], ["contrato_numero", "Contrato"], ["percentual", "Percentual"], ["valor", "Valor"]],
        fields: [
            ["usuario_id", "Vendedor", "reference", "usuarios"], ["contrato_id", "Contrato", "reference", "contratos"],
            ["percentual", "Percentual", "number"], ["valor", "Valor", "number"],
        ],
    },
    usuarios: {
        label: "Usuários", icon: "US", singular: "Usuário",
        columns: [["nome", "Nome"], ["email", "E-mail"], ["perfil_nome", "Perfil"], ["ativo", "Ativo"]],
        fields: [
            ["nome", "Nome"], ["email", "E-mail", "email"], ["senha", "Senha", "password"],
            ["perfil_id", "Perfil", "reference", "perfis"], ["ativo", "Usuário ativo", "checkbox"],
        ],
    },
    perfis: {
        label: "Perfis", icon: "PF", singular: "Perfil",
        columns: [["nome", "Perfil"], ["descricao", "Descrição"]],
        fields: [["nome", "Nome"], ["descricao", "Descrição", "textarea"]],
    },
    logs: {
        label: "Auditoria", icon: "LG", singular: "Log", readonly: true,
        columns: [["criado_em", "Data"], ["usuario_nome", "Usuário"], ["tabela", "Tabela"], ["acao", "Ação"], ["registro_id", "Registro"]],
    },
};

const $ = (selector) => document.querySelector(selector);
const content = $("#content");

async function api(path, options = {}) {
    const response = await fetch(`/api/${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
            ...(options.headers || {}),
        },
    });
    const data = await response.json().catch(() => ({}));
    if (response.status === 401 && path !== "auth/login") logout();
    if (!response.ok) throw new Error(data.erro || "Não foi possível concluir a operação.");
    return data;
}

function money(value) {
    return Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function pretty(value) {
    let str = String(value ?? "").replaceAll("_", " ").toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
    const dict = {
        "Prospeccao": "Prospecção",
        "Qualificacao": "Qualificação",
        "Negociacao": "Negociação",
        "Ligacao": "Ligação",
        "Reuniao": "Reunião",
        "Concluida": "Concluída",
        "Indicacao": "Indicação",
        "Aprovacao": "Aprovação"
    };
    return dict[str] || str;
}

function formatValue(key, value) {
    if (value === null || value === undefined || value === "") return "-";
    if (["valor", "valor_estimado", "valor_ponderado"].includes(key)) return money(value);
    if (key === "percentual" || key === "probabilidade") return `${value}%`;
    if (key === "ativo") return value ? "Sim" : "Não";
    if (key.includes("data") || key.endsWith("_em") || ["vencimento", "pagamento", "validade"].includes(key)) {
        const date = new Date(String(value).includes("T") ? value : `${value}T00:00:00`);
        return Number.isNaN(date.getTime()) ? value : date.toLocaleString("pt-BR", { dateStyle: "short", ...(String(value).includes(":") ? { timeStyle: "short" } : {}) });
    }
    return pretty(value);
}

function notify(message, error = false) {
    const toast = $("#toast");
    toast.textContent = message;
    toast.className = `toast ${error ? "error" : "success"}`;
    setTimeout(() => toast.classList.add("hidden"), 3200);
}

function renderNav() {
    const groups = [
        ["Principal", ["dashboard", "clientes", "leads", "oportunidades"]],
        ["Comercial", ["propostas", "contratos", "atividades"]],
        ["Financeiro", ["contas-receber", "comissoes"]],
        ["Administração", ["usuarios", "perfis", "logs"]],
    ];
    $("#main-nav").innerHTML = groups.map(([group, keys]) => `
        <p class="nav-group">${group}</p>
        ${keys.map(key => `<button data-page="${key}" class="${state.page === key ? "active" : ""}" title="${modules[key].label}">
            <span class="nav-icon">${modules[key].icon}</span><span class="nav-label">${modules[key].label}</span>
        </button>`).join("")}
    `).join("");
    $("#main-nav").querySelectorAll("button").forEach(button => button.addEventListener("click", () => navigate(button.dataset.page)));
}

async function navigate(page) {
    state.page = page;
    state.editing = null;
    renderNav();
    const module = modules[page];
    $("#page-title").textContent = module.label;
    $("#page-kicker").textContent = module.kicker || "Gestão operacional";
    $("#new-record").classList.toggle("hidden", page === "dashboard" || module.readonly);
    document.body.classList.remove("menu-open");
    content.innerHTML = `<div class="loading">Carregando ${module.label.toLowerCase()}...</div>`;
    try {
        if (page === "dashboard") await renderDashboard();
        else await renderModule(page);
    } catch (error) {
        content.innerHTML = `<div class="empty"><h3>Não foi possível carregar</h3><p>${error.message}</p></div>`;
    }
}

function tooltipHtml(text) {
    if (!text) return "";
    return `<div class="info-tooltip"><span class="info-icon">i</span><span class="tooltip-text">${text}</span></div>`;
}

async function renderDashboard() {
    const data = await api("dashboard/kpis");
    const cards = [
        ["Clientes ativos", data.clientes_ativos, "Base comercial ativa", "Quantidade de clientes com status Ativo."],
        ["Leads", data.total_leads, "Contatos no funil", "Total de leads cadastrados independentemente da origem ou status."],
        ["Pipeline aberto", money(data.oportunidades_abertas), "Valor potencial", "Soma do valor estimado de todas as oportunidades não fechadas ou perdidas."],
        ["Pipeline ponderado", money(data.pipeline_ponderado), "Probabilidade aplicada", "Soma dos valores das oportunidades multiplicados pela sua probabilidade de fechamento."],
        ["Recebido", money(data.financeiro.pago), "Contas pagas", "Valor total de contas a receber já com status Pago."],
        ["Em aberto", money(data.financeiro.aberto), "A receber", "Valor total de contas a receber com status Aberto."],
        ["Atividades atrasadas", data.atividades_atrasadas, "Exigem atenção", "Número de atividades agendadas para datas passadas que ainda constam como Pendente."],
        ["Comissões", money(data.comissoes_previstas), "Total previsto", "Valor total de comissões calculadas para os contratos ativos e encerrados."],
    ];
    content.innerHTML = `
        <div class="kpi-grid">${cards.map(([label, value, note, desc]) => `
            <article class="kpi-card"><span>${label}${tooltipHtml(desc)}</span><strong>${value}</strong><small>${note}</small></article>`).join("")}
        </div>
        <div class="dashboard-grid">
            ${chartCard("Faturamento mensal", data.faturamento_mensal, "mes", "faturamento", true, "Soma do valor dos contratos iniciados a cada mês.")}
            ${pieChartCardHtml("Leads por origem", "leads-chart", "Distribuição percentual dos leads baseada no canal de captação de origem.")}
            ${chartCard("Funil de oportunidades", data.oportunidades_etapa, "categoria", "total", false, "Quantidade de oportunidades posicionadas em cada etapa do funil de vendas.")}
            ${pieChartCardHtml("Contratos por status", "contratos-chart", "Proporção da quantidade de contratos por status operacional.")}
        </div>
        <div class="summary-grid">
            <article class="panel"><header><div><span class="eyebrow">Financeiro</span><h2>Contas a receber${tooltipHtml("Resumo financeiro agrupado pelo status da conta a receber (Aberto, Pago ou Vencido).")}</h2></div></header>
                <div class="finance-lines">
                    <div><span>Em aberto</span><strong>${money(data.financeiro.aberto)}</strong></div>
                    <div><span>Recebido</span><strong>${money(data.financeiro.pago)}</strong></div>
                    <div class="danger"><span>Vencido</span><strong>${money(data.financeiro.vencido)}</strong></div>
                </div>
            </article>
            <article class="panel"><header><div><span class="eyebrow">Equipe</span><h2>Comissões por vendedor${tooltipHtml("Total de comissões acumuladas por usuário com base nos contratos fechados.")}</h2></div></header>
                <div class="finance-lines">${data.comissoes_vendedor.map(item => `<div><span>${item.vendedor}</span><strong>${money(item.total)}</strong></div>`).join("") || "<p>Sem dados.</p>"}</div>
            </article>
        </div>`;
    
    initPieChart("leads-chart", data.leads_origem, "categoria", "total");
    initPieChart("contratos-chart", data.contratos_status, "categoria", "total");
}

function chartCard(title, rows, labelKey, valueKey, currency = false, desc = "") {
    const max = Math.max(...rows.map(row => Number(row[valueKey])), 1);
    return `<article class="panel chart-card"><header><div><span class="eyebrow">Indicador</span><h2>${title}${tooltipHtml(desc)}</h2></div></header>
        <div class="bar-chart">${rows.map(row => `<div class="bar-row">
            <span>${pretty(row[labelKey])}</span><div><i style="width:${Math.max(Number(row[valueKey]) / max * 100, 3)}%"></i></div>
            <strong>${currency ? money(row[valueKey]) : row[valueKey]}</strong>
        </div>`).join("") || "<p>Sem dados para o periodo.</p>"}</div></article>`;
}

function pieChartCardHtml(title, canvasId, desc = "") {
    return `<article class="panel chart-card"><header><div><span class="eyebrow">Indicador</span><h2>${title}${tooltipHtml(desc)}</h2></div></header>
        <div class="pie-chart-container"><canvas id="${canvasId}"></canvas></div></article>`;
}

function initPieChart(canvasId, rows, labelKey, valueKey) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    if (!rows || rows.length === 0) {
        ctx.parentElement.innerHTML = "<p class='empty-chart'>Sem dados para o periodo.</p>";
        return;
    }
    const labels = rows.map(r => pretty(r[labelKey]));
    const data = rows.map(r => Number(r[valueKey]));
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, font: { family: 'Inter, sans-serif' } } }
            }
        }
    });
}

async function renderModule(page) {
    state.records = await api(page);
    const module = modules[page];
    content.innerHTML = `
        <article class="panel data-panel">
            <header class="data-header">
                <div><span class="eyebrow">${state.records.length} registros</span><h2>${module.label}</h2></div>
                <label class="search"><span>Buscar</span><input id="table-search" placeholder="Filtrar nesta lista"></label>
            </header>
            <div class="table-wrap"><table><thead><tr>
                ${module.columns.map(([, label]) => `<th>${label}</th>`).join("")}
                ${module.readonly ? "" : "<th class='actions-cell'>Ações</th>"}
            </tr></thead><tbody id="data-rows"></tbody></table></div>
        </article>`;
    renderRows();
    $("#table-search").addEventListener("input", renderRows);
}

function renderRows() {
    const module = modules[state.page];
    const query = ($("#table-search")?.value || "").toLowerCase();
    const rows = state.records.filter(record => JSON.stringify(record).toLowerCase().includes(query));
    $("#data-rows").innerHTML = rows.map(record => `<tr>
        ${module.columns.map(([key]) => `<td data-label="${module.columns.find(c => c[0] === key)[1]}">${formatValue(key, record[key])}</td>`).join("")}
        ${module.readonly ? "" : `<td class="actions-cell">
            ${module.action ? `<button class="text-button action" data-id="${record.id}">${module.action[0]}</button>` : ""}
            <button class="text-button edit" data-id="${record.id}">Editar</button>
            <button class="text-button danger delete" data-id="${record.id}">Excluir</button>
        </td>`}
    </tr>`).join("") || `<tr><td colspan="${module.columns.length + 1}"><div class="empty">Nenhum registro encontrado.</div></td></tr>`;
    document.querySelectorAll(".edit").forEach(button => button.addEventListener("click", () => openForm(state.records.find(r => String(r.id) === button.dataset.id))));
    document.querySelectorAll(".delete").forEach(button => button.addEventListener("click", () => deleteRecord(button.dataset.id)));
    document.querySelectorAll(".action").forEach(button => button.addEventListener("click", () => module.action[1](button.dataset.id)));
}

async function loadReferences(module) {
    const references = [...new Set((module.fields || []).filter(field => field[2] === "reference").map(field => field[3]))];
    await Promise.all(references.map(async resource => {
        state.references[resource] = state.references[resource] || await api(resource);
    }));
}

async function openForm(record = null) {
    const module = modules[state.page];
    await loadReferences(module);
    state.editing = record;
    $("#modal-title").textContent = `${record ? "Editar" : "Novo"} ${module.singular.toLowerCase()}`;
    $("#record-form").innerHTML = `
        <div class="form-grid">${module.fields.map(field => renderField(field, record)).join("")}</div>
        <p id="record-error" class="form-error"></p>
        <footer><button type="button" class="secondary" id="cancel-form">Cancelar</button><button type="submit" class="primary">Salvar</button></footer>`;
    $("#modal").classList.remove("hidden");
    $("#cancel-form").addEventListener("click", closeModal);
}

function renderField([name, label, type = "text", options, required = false], record) {
    let value = record?.[name] ?? defaultValue(name, type);
    if (type === "datetime-local" && value) value = String(value).slice(0, 16);
    const requiredAttr = required || ["select", "reference"].includes(type) ? "required" : "";
    if (type === "textarea") return `<label class="wide">${label}<textarea name="${name}" ${requiredAttr}>${value}</textarea></label>`;
    if (type === "checkbox") return `<label class="checkbox wide"><input name="${name}" type="checkbox" ${value !== false ? "checked" : ""}><span>${label}</span></label>`;
    if (type === "select") return `<label>${label}<select name="${name}" ${requiredAttr}>${options.map(option => `<option value="${option}" ${value === option ? "selected" : ""}>${pretty(option)}</option>`).join("")}</select></label>`;
    if (type === "reference") {
        const rows = state.references[options] || [];
        return `<label>${label}<select name="${name}" ${requiredAttr}><option value="">Selecione</option>${rows.map(row => {
            const text = row.nome || row.titulo || row.numero || row.email;
            return `<option value="${row.id}" ${String(value) === String(row.id) ? "selected" : ""}>${text}</option>`;
        }).join("")}</select></label>`;
    }
    return `<label>${label}<input name="${name}" type="${type}" value="${value}" ${requiredAttr} ${type === "number" ? 'min="0" step="0.01"' : ""}></label>`;
}

function defaultValue(name, type) {
    const defaults = {
        tipo: "PJ", status: state.page === "leads" ? "NOVO" : state.page === "contas-receber" ? "ABERTO" : "ATIVO",
        origem: "Google", etapa: "PROSPECCAO", probabilidade: 10, percentual: 5,
        data_inicio: new Date().toISOString().slice(0, 10), validade: new Date(Date.now() + 30 * 864e5).toISOString().slice(0, 10),
    };
    return type === "checkbox" ? true : defaults[name] ?? "";
}

async function saveRecord(event) {
    event.preventDefault();
    const form = new FormData(event.target);
    const data = {};
    modules[state.page].fields.forEach(([name, , type]) => {
        if (type === "checkbox") data[name] = event.target.elements[name].checked;
        else if (form.get(name) !== "") data[name] = type === "number" ? Number(form.get(name)) : form.get(name);
    });
    try {
        const path = state.editing ? `${state.page}/${state.editing.id}` : state.page;
        await api(path, { method: state.editing ? "PUT" : "POST", body: JSON.stringify(data) });
        closeModal();
        notify("Registro salvo com sucesso.");
        await navigate(state.page);
    } catch (error) {
        $("#record-error").textContent = error.message;
    }
}

async function deleteRecord(id) {
    if (!confirm("Deseja realmente excluir este registro?")) return;
    try {
        await api(`${state.page}/${id}`, { method: "DELETE" });
        notify("Registro excluído.");
        await navigate(state.page);
    } catch (error) { notify(error.message, true); }
}

async function convertLead(id) {
    const document = prompt("Informe o CPF/CNPJ do novo cliente:");
    if (!document) return;
    try {
        await api(`leads/${id}/converter`, { method: "POST", body: JSON.stringify({ cpf_cnpj: document, valor_estimado: 0 }) });
        notify("Lead convertido em cliente e oportunidade.");
        await navigate("leads");
    } catch (error) { notify(error.message, true); }
}

async function approveProposal(id) {
    if (!confirm("Aprovar proposta e gerar contrato?")) return;
    try {
        await api(`propostas/${id}/aprovar`, { method: "POST", body: JSON.stringify({}) });
        notify("Proposta aprovada e contrato gerado.");
        await navigate("propostas");
    } catch (error) { notify(error.message, true); }
}

async function payReceivable(id) {
    if (!confirm("Confirmar a baixa desta conta?")) return;
    try {
        await api(`contas-receber/${id}/baixar`, { method: "POST", body: JSON.stringify({}) });
        notify("Pagamento registrado.");
        await navigate("contas-receber");
    } catch (error) { notify(error.message, true); }
}

async function showClientDetails(id) {
    try {
        const client = await api(`clientes/${id}`);
        const tabs = [
            ["geral", "Dados gerais", () => `
                <div class="detail-grid">
                    ${[
                        ["Nome", client.nome], ["CPF/CNPJ", client.cpf_cnpj], ["Tipo", client.tipo],
                        ["Segmento", client.segmento], ["Telefone", client.telefone], ["E-mail", client.email],
                        ["Status", client.status],
                    ].map(([label, value]) => `<div><span>${label}</span><strong>${formatValue(label.toLowerCase(), value)}</strong></div>`).join("")}
                </div>`],
            ["enderecos", "Endereços", () => detailTable(client.enderecos, [["logradouro", "Logradouro"], ["numero", "Número"], ["cidade", "Cidade"], ["estado", "UF"]])],
            ["contatos", "Contatos", () => detailTable(client.contatos, [["nome", "Nome"], ["cargo", "Cargo"], ["telefone", "Telefone"], ["email", "E-mail"]])],
            ["oportunidades", "Oportunidades", () => detailTable(client.oportunidades, [["titulo", "Título"], ["etapa", "Etapa"], ["valor_estimado", "Valor"]])],
            ["contratos", "Contratos", () => detailTable(client.contratos, [["numero", "Número"], ["valor", "Valor"], ["status", "Status"]])],
            ["atividades", "Atividades", () => detailTable(client.atividades, [["titulo", "Título"], ["data_agendada", "Agendada"], ["status", "Status"]])],
            ["contas_receber", "Financeiro", () => detailTable(client.contas_receber, [["valor", "Valor"], ["vencimento", "Vencimento"], ["pagamento", "Pagamento"], ["status", "Status"]])],
        ];
        $("#modal-title").textContent = client.nome;
        $("#record-form").innerHTML = `
            <div class="detail-tabs">${tabs.map(([key, label], index) => `<button type="button" data-tab="${key}" class="${index === 0 ? "active" : ""}">${label}</button>`).join("")}</div>
            <div id="detail-content">${tabs[0][2]()}</div>
            <footer><button type="button" class="secondary" id="cancel-form">Fechar</button></footer>`;
        $("#modal").classList.remove("hidden");
        $("#cancel-form").addEventListener("click", closeModal);
        document.querySelectorAll(".detail-tabs button").forEach(button => button.addEventListener("click", () => {
            document.querySelectorAll(".detail-tabs button").forEach(item => item.classList.toggle("active", item === button));
            const tab = tabs.find(item => item[0] === button.dataset.tab);
            $("#detail-content").innerHTML = tab[2]();
        }));
    } catch (error) {
        notify(error.message, true);
    }
}

function detailTable(rows, columns) {
    if (!rows?.length) return '<div class="empty">Nenhum registro vinculado.</div>';
    return `<div class="table-wrap detail-table"><table><thead><tr>${columns.map(([, label]) => `<th>${label}</th>`).join("")}</tr></thead>
        <tbody>${rows.map(row => `<tr>${columns.map(([key]) => `<td>${formatValue(key, row[key])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function closeModal() {
    $("#modal").classList.add("hidden");
    state.editing = null;
}

async function login(event) {
    event.preventDefault();
    $("#login-error").textContent = "";
    try {
        const result = await api("auth/login", {
            method: "POST",
            body: JSON.stringify({ email: $("#login-email").value, senha: $("#login-senha").value }),
        });
        state.token = result.token;
        state.user = result.usuario;
        localStorage.setItem("crm_token", state.token);
        startApp();
    } catch (error) { $("#login-error").textContent = error.message; }
}

function logout() {
    localStorage.removeItem("crm_token");
    state.token = null;
    state.user = null;
    $("#app").classList.add("hidden");
    $("#login-view").classList.remove("hidden");
}

function startApp() {
    $("#login-view").classList.add("hidden");
    $("#app").classList.remove("hidden");
    $("#user-name").textContent = state.user.nome;
    $("#user-role").textContent = state.user.perfil_nome;
    $("#user-avatar").textContent = state.user.nome.split(" ").slice(0, 2).map(part => part[0]).join("");
    $("#today").textContent = new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "2-digit", month: "long" });
    renderNav();
    navigate("dashboard");
}

function setSidebarCollapsed(collapsed) {
    document.body.classList.toggle("sidebar-collapsed", collapsed);
    const toggle = $("#sidebar-toggle");
    toggle.setAttribute("aria-expanded", String(!collapsed));
    toggle.setAttribute("aria-label", collapsed ? "Expandir menu lateral" : "Recolher menu lateral");
    toggle.title = collapsed ? "Expandir menu" : "Recolher menu";
    localStorage.setItem("crm_sidebar_collapsed", String(collapsed));
}

async function bootstrap() {
    setSidebarCollapsed(localStorage.getItem("crm_sidebar_collapsed") === "true");
    if (state.token) {
        try {
            state.user = await api("auth/me");
            startApp();
            return;
        } catch (_) { /* login view remains visible */ }
    }
    logout();
}

$("#login-form").addEventListener("submit", login);
$("#logout").addEventListener("click", logout);
$("#new-record").addEventListener("click", () => openForm());
$("#modal-close").addEventListener("click", closeModal);
$("#record-form").addEventListener("submit", saveRecord);
$("#menu-toggle").addEventListener("click", () => document.body.classList.toggle("menu-open"));
$("#sidebar-toggle").addEventListener("click", () => setSidebarCollapsed(!document.body.classList.contains("sidebar-collapsed")));
$("#modal").addEventListener("click", event => { if (event.target === $("#modal")) closeModal(); });
bootstrap();
