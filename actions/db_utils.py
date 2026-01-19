import yaml
import psycopg2
import logging

logger = logging.getLogger(__name__)

def load_db_credentials(filepath="credentials.yml"):
    """Carrega credenciais do banco a partir de um arquivo YAML.

    Args:
        filepath (str): Caminho do arquivo de credenciais.

    Returns:
        Dict: Dicionario de credenciais (ou vazio em erro).
    """
    try:
        with open(filepath, "r") as file:
            credentials = yaml.safe_load(file)
            return credentials.get("db", {})
    except Exception as e:
        logger.error(f"Erro ao carregar credenciais do banco: {e}")
        return {}

def get_db_connection():
    """Cria e retorna uma conexao com o banco usando as credenciais.

    Returns:
        Optional[psycopg2.extensions.connection]: Conexao ativa ou None em erro.
    """
    config = load_db_credentials()
    try:
        conn = psycopg2.connect(
            host=config.get("host"),
            port=config.get("port"),
            database=config.get("database"),
            user=config.get("user"),
            password=config.get("password")
        )
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar no banco de dados: {e}")
        return None
