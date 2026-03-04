#!/bin/sh

export PYTHONPATH="/app:${PYTHONPATH}"

# If app tables exist but alembic_version doesn't, stamp directly via sqlite3
python -c "
import sqlite3, os
db = os.getenv('DB_URL', 'sqlite:///data.db').replace('sqlite:///', '')
if not os.path.exists(db):
    exit(0)
conn = sqlite3.connect(db)
tables = [r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]
if 'users' in tables and 'alembic_version' not in tables:
    conn.execute('CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)')
    conn.execute(\"INSERT INTO alembic_version VALUES ('0001_initial')\")
    conn.commit()
    print('Stamped existing database at 0001_initial')
conn.close()
"

alembic upgrade head

exec "$@"
