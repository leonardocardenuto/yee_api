from flask import Blueprint, jsonify, request
import psycopg2
import logging
from dotenv import load_dotenv
import os

load_dotenv()

bp = Blueprint('routes', __name__)

# Configuração do logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# NeonDB URI
uri = os.getenv('NEONDB')

# Função para conectar ao banco de dados
def connect_to_database():
    try:
        conn = psycopg2.connect(uri)
        logger.debug("Connected to database")
        return conn
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        raise

# Rota para checar conexão
@bp.route('/check_connection', methods=['GET'])
def check_connection():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return jsonify({'message': 'NeonDB connection successful'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para logar
@bp.route('/login', methods=['POST'])
def login():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())

    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email, senha, and confirmar senha são obrigatórios!'}), 400

        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            return jsonify({'message': 'Sucesso!'}), 200
        else:
            return jsonify({'error': 'Email ou senha inválidos!'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Rota para criar usuário
@bp.route('/create_user', methods=['POST'])
def create_user():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())

    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if not email or not password or not confirm_password:
            return jsonify({'error': 'Email, senha, and confirmar senha são obrigatórios!'}), 400

        if password != confirm_password:
            return jsonify({'error': 'As senhas não são iguais!'}), 400

        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({'error': 'Um usuário com esse e-mail já existe!'}), 409

        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Usuário criado com sucesso!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


