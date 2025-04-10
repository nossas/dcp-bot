from actions.db_utils import get_db_connection

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            whatsapp_id TEXT UNIQUE
        );
    """)

    # Tabela mídias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS midias (
            id SERIAL PRIMARY KEY,
            path TEXT,
            mime_type TEXT
        );
    """)
    # Tabela riscos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS riscos (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            id_usuario BIGINT REFERENCES usuarios(id),
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            endereco TEXT,
            classificacao TEXT,
            descricao TEXT,
            id_midias INTEGER[],
            identificar BOOLEAN
        );
    """)

    # Tabela pontos de referência
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pontos_referencia (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            descricao TEXT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    create_tables()
