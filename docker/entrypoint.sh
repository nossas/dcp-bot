#!/bin/bash

function postgres_ready(){
python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect(
        dbname="$POSTGRES_DB",
        user="$POSTGRES_USER",
        password="$POSTGRES_PASSWORD",
        host="$POSTGRES_HOST"
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

function should_run_migrations(){
python << END
import sys
import psycopg2
conn = psycopg2.connect(
    dbname="$POSTGRES_DB",
    user="$POSTGRES_USER",
    password="$POSTGRES_PASSWORD",
    host="$POSTGRES_HOST"
)
cur = conn.cursor()
cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users');")
exists = cur.fetchone()[0]
cur.close()
conn.close()
if not exists:
    sys.exit(0)  # table does not exist: run migrations
sys.exit(1)      # table exists: skip migrations
END
}

until postgres_ready; do
  >&2 echo "Postgres indisponível - sleeping"
  sleep 1
done

cd /app

if should_run_migrations; then
  >&2 echo "Rodando migrations.py porque a tabela 'users' não existe."
  python migrations.py
else
  >&2 echo "Tabela 'users' já existe. Pulando migrations."
fi

rasa train
rasa run --connector whatsapp_connector.WhatsAppInput --debug
