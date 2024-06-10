# Py modules imports
from flask import Blueprint, jsonify, request
import random
import re
from datetime import time

# Utils imports
from app.config import logger
from app.utils.db import auth, exec_query,commit
from app.utils.mail import send_mail
from app.utils.ai import identify_image , ask_gemini
from app.utils.images_handler import restore_image


bp = Blueprint('routes', __name__)


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
            return jsonify({'error': 'Email/Nome de Usuário, senha, and confirmar senha são obrigatórios!'}), 400
        
        user = auth(email,password)

        if user:
            return user, 200
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
        user_name = data.get('user_name')
        user_name = user_name.lower()
        email = data.get('email')
        email = email.lower()
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if not user_name or not email or not password or not confirm_password:
            return jsonify({'error': 'Nome de usuário, email, senha, and confirmar senha são obrigatórios!'}), 400

        if password != confirm_password:
            return jsonify({'error': 'As senhas não são iguais!'}), 401
        
        existing_user = exec_query("SELECT * FROM users WHERE user_name = %s or email = %s", (user_name, email,))

        if existing_user:
            return jsonify({'error': 'Um usuário com esse e-mail já existe!'}), 409
        
        send_mail('welcome',email)
        commit("INSERT INTO users (user_name, email, password) VALUES (%s, %s, %s)", ( user_name, email, password))

        return jsonify({'message': 'Usuário criado com sucesso!'}), 200
    except Exception as e:
        logger.debug(e)
        return jsonify({'error': str(e)}), 500

@bp.route('/alarms', methods=['POST'])
def create_alarm():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())

    try:
        data = request.get_json()
        description = data.get('description')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        time_of_day = data.get('timeOfDay')
        interval_in_hours = data.get('intervalInHours')
        user_name = data.get('user_name')
        type = data.get('type')
        alarm_id = data.get('alarmId')

        if not all([description, start_date, end_date, time_of_day, interval_in_hours, user_name, type, alarm_id]):
            return jsonify({'error': 'Todos os campos são obrigatórios!'}), 400

        start_date = start_date
        end_date = end_date

        commit("INSERT INTO alarms (description, startDate, endDate, hour, interval_hours, user_name, type, alarm_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
               (description, start_date, end_date, time_of_day, interval_in_hours, user_name, type, alarm_id))
        
        return jsonify({'message': 'Alarme criado com sucesso!'}), 200
    except Exception as e:
        logger.debug(e)
        return jsonify({'error': str(e)}), 500

@bp.route('/get_alarms', methods=['POST'])
def get_alarm():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())

    try:
        alarm_id = request.json.get('alarm_id')
        alarm_id = str(alarm_id)
        if not alarm_id:
            return jsonify({'error': 'Todos os campos são obrigatórios!'}), 400

        medication_info = exec_query("SELECT * FROM alarms WHERE alarm_id = %s", (alarm_id,))

        if not medication_info:
            return jsonify({'error': 'Alarm not found'}), 404

        row = medication_info[0]
        alarm_data = {
            'id': row[0],
            'description': row[1],
            'startDate': row[4].isoformat(),
            'endDate': row[5].isoformat(),
        }

        return jsonify(alarm_data), 200

    except Exception as e:
        logger.error("Error processing request", exc_info=True)
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

# Rota para atualizar avatar
@bp.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())

    try:
        data = request.get_json()
        user_name = data.get('user_name')
        avatar = data.get('avatar')

        commit("UPDATE users SET avatar = %s WHERE user_name = %s", (avatar,user_name,))

        return jsonify({'message':  'Avatar atualizado com sucesso!'}), 200
    except Exception as e:
        logger.debug(e)
        return jsonify({'error': str(e)}), 500
    
# Rota para pegar exames
@bp.route('/get_exams', methods=['POST'])
def get_exams():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())
    try:
        data = request.get_json()
        user_name = data.get('user_name')

        exams = exec_query(f"SELECT peso, altura, pressao, glicemia, imc, pressao_state, glicemia_state, imc_state FROM medical_exams WHERE user_name = '{user_name}'")
        
        if exams:
            for exam in exams:    
                peso, altura, pressao, glicemia, imc, pressao_state, glicemia_state, imc_state = exam
                logger.debug(f"Exam data - Peso: {peso}, Altura: {altura}, Pressao: {pressao}, Glicemia: {glicemia}, Imc: {imc}, Pressao_State : {pressao_state}, Glicemia_State : {glicemia_state}, IMC_state : {imc_state} ")
            return jsonify({
                'peso': peso,
                'altura': altura,
                'pressao': pressao,
                'glicemia': glicemia,
                'imc': imc,
                'pressao_state' : pressao_state,
                'glicemia_state' : glicemia_state,
                'imc_state' : imc_state
            })

        return jsonify({'message': 'No data found for the given ID'}), 404

    except Exception as e:
        logger.debug(e)
        return jsonify({'error': str(e)}), 500
    
# Rota para montar histórico
@bp.route('/get_previous_exams', methods=['POST'])
def get_previous_exams():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())
    try:
        data = request.get_json()
        user_name = data.get('user_name')
        user_email = data.get('email')

        filter = (data.get('filtro')).lower()

        if not user_name and not user_email:
            return "Email ou nome de usário são obrigatórios",400
        if not filter:
            return "É necessárioinformar um filtro",400
        
        translate_filter_db = {
            "pressão": "pressao"
        }

        translated_filter = translate_filter_db.get(filter, filter)
        state_field = f"{translated_filter}_state"

        query = f"""
            SELECT 
                created_on AS Data, 
                {translated_filter} AS Valores, 
                {state_field} AS Estado 
            FROM 
                medical_exams 
            WHERE 
                user_name = %s OR user_email = %s
        """
        exams = exec_query(query, (user_name, user_email,))

        # Cria uma array de dicionários
        result = [
            {
                'Data': exam[0].strftime("%d/%m/%Y"),
                'Valores': exam[1], 
                'Estado': exam[2]
            }

        for exam in exams]

        return jsonify(result), 200

    except Exception as e:
        logger.debug(e)
        return jsonify({'error': str(e)}), 500


# Rota ler imagem
@bp.route('/get_text', methods=['POST'])
def get_text():
    try:
        data = request.get_json()
        user_name = data.get('user_name')
        image_data = data.get('image_b64')
        
        if not user_name:
            return jsonify({'error': 'user_name é obrigatório!'}), 400

        email_found = exec_query("SELECT email FROM users WHERE user_name = %s", (user_name,))

        if not email_found:
            return jsonify({'error': 'Permissão negada!!'}), 400
        
        if not image_data:
            return jsonify({'error': 'A imagem é obrigatória!'}), 400


        report = identify_image(restore_image(image_data))

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
        INSERT INTO medical_exams (pressao, peso, altura, glicemia, report, user_email, user_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        commit(insert_query, (pressao, peso, altura, glicemia, report, email_found[0] , user_name))

        return jsonify({'message':  report}), 200
    except Exception as e:
        logger.debug(e)
        return jsonify({'error': str(e)}), 500
    
# Rota falar com AI
@bp.route('/ask_ai', methods=['POST'])
def ask_ai():
    try:
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        question = data.get('question')
        user_name = data.get('user_name')

        if not question:
            return jsonify({'error': 'A pergunta é obrigatória!'}), 400

        response = ask_gemini(f"{question}", latitude, longitude, user_name)
        return jsonify({'message':  response}), 200
    except Exception as e:
        logger.debug(e)
        return jsonify({'error': str(e)}), 500
