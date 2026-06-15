import os, re
src = 'server.py'
dst = 'api/index.py'
os.makedirs('api', exist_ok=True)
with open(src, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Imports
code = code.replace('import sqlite3', 'import psycopg2\nimport psycopg2.extras')

# 2. Variables
code = code.replace('DB_PATH = BASE_DIR / os.getenv("DATABASE_FILE", "crm_corporativo.db")\nSCHEMA_PATH = BASE_DIR / "schema.sql"', 'DB_URL = os.getenv("DATABASE_URL")')

# 3. def connect()
old_connect = '''def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn'''

new_connect = '''def connect():
    conn = psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = True
    return conn'''
code = code.replace(old_connect, new_connect)

# 4. sqlite3.IntegrityError -> psycopg2.IntegrityError
code = code.replace('sqlite3.IntegrityError', 'psycopg2.IntegrityError')

# 5. execute params ? -> %s
code = code.replace('?', '%s')

# 6. Handler -> handler
code = code.replace('class Handler(SimpleHTTPRequestHandler):', 'class handler(SimpleHTTPRequestHandler):')
code = code.replace('Handler)', 'handler)')

# 7. initialize_database
code = code.replace('initialize_database()\n', '# initialize_database()\n')

# 8. boolean values
code = code.replace('clean["ativo"] = 1 if clean["ativo"] else 0', 'clean["ativo"] = True if clean["ativo"] else False')

# Fix UUIDs and Dates that PostgreSQL expects explicitly
# psycopg2 might complain if UUIDs are string, but usually PG casts them if they are in UUID columns.
# wait, %s is used, so it'll send strings, postgres automatically casts string to UUID.

with open(dst, 'w', encoding='utf-8') as f:
    f.write(code)
print('Converted successfully!')
