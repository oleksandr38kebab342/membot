#!/bin/sh

export PYTHONPATH="/app:${PYTHONPATH}"

alembic upgrade head

exec "$@"
