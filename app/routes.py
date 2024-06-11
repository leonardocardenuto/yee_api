# Py modules imports
from flask import Blueprint, jsonify, request
import random
import re


import os.path
import pickle
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

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
    
# Rota check mais próxima
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

#Rota para inserir no Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

@bp.route('/insert_medication', methods=['POST'])
def insert_medication():
    creds = None

    data = request.get_json()
    medication = data.get('medication')
    summary = f"Tomar {medication}"
    interval_hours = int(data.get('interval'))
    as_from = datetime.strptime(data.get('as_from'), '%m/%d/%y %H:%M:%S')
    to = datetime.strptime(data.get('to'), '%m/%d/%y %H:%M:%S')
    user_name = data.get('user_name')
    
    # O arquivo token.pickle armazena os tokens de acesso e atualização do usuário
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Cria eventos para cada dose dentro do período especificado
    current_time = as_from
    while current_time <= to:
        event = {
            'summary': summary,
            'location': '',
            'description': '',
            'start': {
                'dateTime': current_time.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': (current_time + timedelta(minutes=30)).isoformat(),  # Duração de 30 minutos
                'timeZone': 'America/Sao_Paulo',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 5},
                ],
            },
        }

        # Adiciona o evento ao calendário
        service.events().insert(calendarId='primary', body=event).execute()
        
        # Incrementa o tempo atual pelo intervalo de horas
        current_time += timedelta(hours=interval_hours)
        
    commit("""
        INSERT INTO medications (medication, user_name, startdate, enddate, interval_hours)
        VALUES (%s, %s, %s, %s, %s)
        """, 
        (medication, user_name, as_from, to, interval_hours)
        )
        
    return jsonify({"status": "success"}), 200

# Rota para pegar medicamentos
@bp.route('/get_medication', methods=['POST'])
def get_medication():
    logger.info("Received request: %s %s", request.method, request.url)
    logger.debug("Request headers: %s", request.headers)
    logger.debug("Request data: %s", request.get_data())
    try:
        data = request.get_json()
        user_name = data.get('user_name')

        medications = exec_query(f"SELECT medication, startdate, enddate, interval_hours FROM medications WHERE user_name = '{user_name}' ORDER BY enddate ASC")
        
        result = [
        {
            'medicacao': medication[0],
            'inicio': medication[1], 
            'fim': medication[2],
            'invervalo':medication[3]
        }
        for medication in medications]

        return jsonify(result), 200

    except Exception as e:
        logger.debug(e)
        return jsonify({'error': str(e)}), 500
        