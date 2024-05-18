import psycopg2
from app.config import uri, logger

def connect_to_database():
    try:
        conn = psycopg2.connect(uri)
        logger.debug("Connected to database")
        return conn
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        raise

def exec_query(query, params=None):
    """
    Executes a given SQL query with optional parameters and returns the result.
    """
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        raise e

def commit(query, params=None):
    """
    Executes a given SQL query of the type INSERT.
    """
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute(query,params)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def auth(email, password):
    """
    Retrieves a user by email and password.
    """
    query = "SELECT user_name,avatar FROM users WHERE (user_name = %s OR email = %s) AND password = %s"
    params = (email, email, password)
    result = exec_query(query, params)
    return result
