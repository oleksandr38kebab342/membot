#!/bin/sh
set -e

export PYTHONPATH="/app:${PYTHONPATH}"

# Try upgrade; if tables already exist, stamp as current and move on
alembic upgrade head 2>&1 || {
    echo "Upgrade failed (tables likely exist). Stamping current revision..."
    alembic stamp head
}

exec "$@"
