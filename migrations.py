from actions.db_utils import get_db_connection

def create_tables():
    """Cria as tabelas base no banco de dados.

    Returns:
        None
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            whatsapp_id TEXT UNIQUE,
            notificacoes BOOLEAN DEFAULT NULL
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS riscos (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            id_usuario BIGINT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            endereco TEXT,
            classificacao TEXT,
            descricao TEXT,
            id_midias INTEGER[],
            CONSTRAINT fk_usuario
                FOREIGN KEY (id_usuario)
                REFERENCES usuarios(id)
                ON DELETE SET NULL
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
