from flask import Blueprint, jsonify, request
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import logging

bp = Blueprint('routes', __name__)

# MongoDB Atlas URI
uri = "mongodb+srv://leothedev:3Zd6C07wLWLpmF2A@cluster0.ibgokom.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Inicializar MongoDB com a versão de Server Api
client = MongoClient(uri, server_api=ServerApi('1'))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Rota para checar conexão
@bp.route('/check_connection', methods=['GET'])
def check_connection():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())

    try:
        client.admin.command('ping')
        return jsonify({'message': 'MongoDB connection successful'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
