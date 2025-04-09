#!/bin/bash

function postgres_ready(){
python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect(dbname="$POSTGRES_DB", user="$POSTGRES_USER", password="$POSTGRES_PASSWORD", host="$POSTGRES_HOST")
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
  >&2 echo "Postgres indisponível - sleeping"
  sleep 1
done

>&2 echo "Banco disponível. Executando migrations.py..."

cd /app
python migrations.py
rasa train 
rasa run --connector whatsapp_connector.WhatsAppInput --debug