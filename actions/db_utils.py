import yaml
import psycopg2
import logging

logger = logging.getLogger(__name__)

def load_db_credentials(filepath="credentials.yml"):
    try:
        with open(filepath, "r") as file:
            credentials = yaml.safe_load(file)
            return credentials.get("db", {})
    except Exception as e:
        logger.error(f"Erro ao carregar credenciais do banco: {e}")
        return {}

def get_db_connection():
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
