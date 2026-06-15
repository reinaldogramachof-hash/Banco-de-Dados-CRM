import sys

file_path = 'script.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Visao executiva': 'Visão executiva',
    'Nome / Razao social': 'Nome / Razão social',
    '"Responsavel"': '"Responsável"',
    '"Indicacao"': '"Indicação"',
    '"Titulo"': '"Título"',
    'Previsao de fechamento': 'Previsão de fechamento',
    '"Numero"': '"Número"',
    'Numero (automatico se vazio)': 'Número (automático se vazio)',
    'Data de inicio': 'Data de início',
    '"Descricao"': '"Descrição"',
    '"Comissoes"': '"Comissões"',
    '"Comissao"': '"Comissão"',
    '"Usuarios"': '"Usuários"',
    '"Usuario"': '"Usuário"',
    'Usuario ativo': 'Usuário ativo',
    '"Acao"': '"Ação"',
    'Nao foi possivel concluir a operacao.': 'Não foi possível concluir a operação.',
    '? "Sim" : "Nao"': '? "Sim" : "Não"',
    '"Administracao"': '"Administração"',
    'Nao foi possivel carregar': 'Não foi possível carregar',
    'Gestao operacional': 'Gestão operacional'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Accents fixed in script.js!")
