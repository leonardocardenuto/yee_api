from flask import Blueprint, jsonify, request
import requests
import random
import PIL.Image
import base64
from PIL import Image
from io import BytesIO
import re
from app.config import logger, api_key_maps
from app.utils.db import auth, exec_query,commit
from app.utils.mail import send_mail
from app.utils.ai import identify_image , ask_gemini


bp = Blueprint('routes', __name__)

def search_nearby_hospitals(type ,api_key, latitude, longitude, radius=10000):
    base_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = {
        'key': api_key,
        'location': f'{latitude},{longitude}',
        'radius': radius,
        'type': type
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print('Failed to retrieve data:', 500)
        return False
    
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
        
        user = auth(email,password)

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
        
        existing_user = exec_query("SELECT * FROM users WHERE email = %s", (email,))


        if existing_user:
            return jsonify({'error': 'Um usuário com esse e-mail já existe!'}), 409
        
        send_mail('welcome',email)
        commit("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))

        return jsonify({'message': 'Usuário criado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para alterar a senha
@bp.route('/change_pass', methods=['POST'])
def change_pass():
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
        
        commit("UPDATE users SET password = %s WHERE email = %s", (password,email,))

        return jsonify({'message': 'Senha redefinida com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota gerar o código de confirmação
@bp.route('/gen_code', methods=['POST'])
def gen_code():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())

    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email é obrigatório!'}), 400

        existing_user = exec_query("SELECT * FROM users WHERE email = %s", (email,))

        if not existing_user:
            return jsonify({'error': 'Não existe um usuário com esse e-mail!'}), 409

        code = random.randint(100000, 999999)
        commit("UPDATE users SET confirmation_code = %s WHERE email = %s", (code, email,))
        send_mail('verify_code',code)

        return jsonify({'message': 'Código gerado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Rota verificar o código de confirmação
@bp.route('/check_code', methods=['POST'])
def check_code():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())

    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('confirmation_code')

        if not code:
            return jsonify({'error': 'Código é obrigatório!'}), 400

        existing_code = exec_query("SELECT * FROM users WHERE email = %s AND confirmation_code = %s", (email,code,))

        if not existing_code:
            return jsonify({'error': 'Código incorreto!'}), 409

        commit("UPDATE users SET confirmation_code = null WHERE email = %s AND confirmation_code = %s", (email,code,))

        return jsonify({'message':  'Código verificado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
#================================================
#
#   ATENÇÃO ESSA ROTA SÓ FUNCIONA EM LOCALHOST!
#
#================================================

# Rota ler imagem
@bp.route('/get_text', methods=['POST'])
def get_text():
    try:
        data = request.get_json()
        email = data.get('email')
        image_data = data.get('image_b64')
        
        if not email:
            return jsonify({'error': 'Email é obrigatório!'}), 400

        email_found = exec_query("SELECT * FROM users WHERE email = %s", (email,))

        if not email_found:
            return jsonify({'error': 'Permissão negada!!'}), 400
        
        if not image_data:
            return jsonify({'error': 'A imagem é obrigatória!'}), 400

        image_data = base64.b64decode(image_data)
        decoded_image = Image.open(BytesIO(image_data))
        decoded_image.save("./images/decoded_image.jpg")

        img = PIL.Image.open('./images/decoded_image.jpg')

        report = identify_image(img)

        def safe_extract_numeric(pattern, string):
            match = re.search(pattern, string)
            return float(match.group(1)) if match else None

        def safe_extract_string(pattern, string):
            match = re.search(pattern, string)
            return match.group(1) if match else None

        pressao = safe_extract_string(r'Pressão:\s*(\S+)', report)
        peso = safe_extract_numeric(r'Peso:\s*(\d+(\.\d+)?)', report)
        altura = safe_extract_numeric(r'Altura:\s*(\d+(\.\d+)?)', report)
        glicemia = safe_extract_numeric(r'Glicemia:\s*(\d+(\.\d+)?)', report)
        insert_query = """
        INSERT INTO medical_exams (pressao, peso, altura, glicemia, user_email)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        commit(insert_query, (pressao, peso, altura, glicemia, email))

        return jsonify({'message':  report}), 200
    except Exception as e:
        logger.debug(e)
        return jsonify({'error': str(e)}), 500
    
# Rota check mais próxima
@bp.route('/ask_ai', methods=['POST'])
def ask_ai():
    try:
        data = request.get_json()
        email = data.get('email')
        question = data.get('question')
        
        if not email:
            return jsonify({'error': 'Email é obrigatório!'}), 400

        email = exec_query("SELECT * FROM users WHERE email = %s", (email))

        if not email:
            return jsonify({'error': 'Permissão negada!!'}), 400
        
        if not question:
            return jsonify({'error': 'A pergunta é obrigatória!'}), 400

        latitude = -23.647778
        longitude = -46.573333
        response = ask_gemini([f"Com base na necessidade do usuário : {question}; Peço que identifique o tipo de localidade procurada dentre os da lista abaixo:'hospital','pharmacy','None'. Informe somente o tipo escolhido."])
        logger.debug(response)
        type = response
        type = type.strip()
        results = search_nearby_hospitals(type ,api_key_maps, latitude, longitude)
        if results:
            result_string = ""
            for item in results['results']:
                name = item['name']
                address = item['vicinity']
                rating = item.get('rating', 'N/A')
                type = ', '.join(item['types'])
                result_string += f"\nName: {name}"
                result_string += f"\nAddress: {address}"
                result_string += f"\nRating: {rating}"
                result_string += f"Types: {type}"
                result_string += f"\nLatitude: {latitude}, Longitude: {longitude}"
        
            return jsonify({'message':  result_string}), 200
        else:
            return jsonify({'message':  "Um erro ao vasculhar locais ocorreu!"}), 500
    except Exception as e:
        logger.debug(e)
        return jsonify({'error': str(e)}), 500

