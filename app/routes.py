from flask import Blueprint, jsonify, request
import psycopg2
import logging
from dotenv import load_dotenv
import os
import requests
import random
import google.generativeai as genai
import PIL.Image
import base64
from PIL import Image
from io import BytesIO
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


load_dotenv()

bp = Blueprint('routes', __name__)

# Configuração do logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# NeonDB URI
uri = os.getenv('NEONDB')

api_key_gemini= os.getenv('API_KEY_GEM')

# Função para conectar ao banco de dados
def connect_to_database():
    try:
        conn = psycopg2.connect(uri)
        logger.debug("Connected to database")
        return conn
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        raise

def search_nearby_hospitals(type ,api_key, latitude, longitude, radius=10000):
    logging.debug(type)
    tipo = ''
    response = ''
    if 'hospital' in type:
        tipo = 'hospital'
    elif 'pharmacy' in type:
        tipo = 'pharmacy'
    else:
        tipo = 'None'
    if tipo != 'None' and type(response) != str:
        base_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        params = {
            'key': api_key,
            'location': f'{latitude},{longitude}',
            'radius': radius,
            'type': tipo
        }
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data
    print('Failed to retrieve data:', 500)
    return []
    
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
        
        #Enviar email de boas vindas
        port = 587
        smtp_server = "smtp.office365.com"
        sender_email = "no-reply-appye@hotmail.com"
        password = "yeeapp123"
        receiver_email = email

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "Boas vindas!"

        html = f"""
        <html>
        <body>
            <p>Hello,</p>
            <p>Thanks for signing up with us to use Ye - gestao de saude.</p>
            <p>If you ever have questions, run into problems, consider an upgrade or anything at all, don’t hesitate to reach out to us via email [ADDRESS] or you can connect with us directly using the contact information below.</p>
            <p>Looking forward to hearing from you soon!</p>
            <p>Regards,</p>
        <p>Equipe Ye</p>
        </body>
        </html>
        """

        part1 = MIMEText(html, "html")

        message.attach(part1)

        context = ssl.create_default_context()
        try:
            server = smtplib.SMTP(smtp_server, port)
            server.ehlo()
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print("Email sent!")
        except smtplib.SMTPException as e:
            if "501" in str(e):
                return jsonify({'error': 'Endereco de email nao encontrado'})
            else:
                return jsonify({'error': 'Falha ao enviar email'})
        finally:
            server.quit()


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

        return jsonify({'message': 'Usuário criado com sucesso!'}), 200
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

        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if not existing_user:
            return jsonify({'error': 'Não existe um usuário com esse e-mail!'}), 409

        code = random.randint(100000, 999999)
        cursor.execute("UPDATE users SET confirmation_code = %s WHERE email = %s", (code, email))
        conn.commit()
        cursor.close()
        conn.close()

        port = 587
        smtp_server = "smtp.office365.com"
        sender_email = "no-reply-appye@hotmail.com"
        password = "yeeapp123"
        receiver_email = email

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "Redefinição de senha"

        html = f"""
        <html>
        <body>
            <p>Hi,</p>
            <p>We just need to verify your email address before you can access Ye app.</p>
            <p>Verify your email address <strong>{code}</strong></p>
            <p>Thanks! – The Ye team</p>
        </body>
        </html>
        """

        part1 = MIMEText(html, "html")

        message.attach(part1)

        context = ssl.create_default_context()
        try:
            server = smtplib.SMTP(smtp_server, port)
            server.ehlo()
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print("Email sent!")
        except Exception as e:
            print(f"Failed to send email. Error: {e}")
        finally:
            server.quit()
        
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

        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s AND confirmation_code = %s", (email,code))
        existing_code = cursor.fetchone()

        if not existing_code:
            return jsonify({'error': 'Código incorreto!'}), 409

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

        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        email = cursor.fetchone()

        if not email:
            return jsonify({'error': 'Permissão negada!!'}), 400
        
        if not image_data:
            return jsonify({'error': 'A imagem é obrigatória!'}), 400

        image_data = base64.b64decode(image_data)
        decoded_image = Image.open(BytesIO(image_data))
        decoded_image.save("./images/decoded_image.jpg")
        genai.configure(api_key=api_key_gemini)

        img = PIL.Image.open('./images/decoded_image.jpg')

        safety_settings = [
            {
                "category": "HARM_CATEGORY_DANGEROUS",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]

        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-pro-latest",
            generation_config={
                "temperature":0,
                "max_output_tokens":1000
                },
            safety_settings=safety_settings
            )
        
        response = model.generate_content(["Show the entire text displayed on the image.", img])
        return jsonify({'message':  response.text}), 200
    except Exception as e:
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

        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        email = cursor.fetchone()

        if not email:
            return jsonify({'error': 'Permissão negada!!'}), 400
        
        if not question:
            return jsonify({'error': 'A pergunta é obrigatória!'}), 400

        genai.configure(api_key=api_key_gemini)

        safety_settings = [
            {
                "category": "HARM_CATEGORY_DANGEROUS",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]

        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-pro-latest",
            generation_config={
                "temperature":0,
                "max_output_tokens":900
                },
            safety_settings=safety_settings
            )
        api_key = 'AIzaSyBmhJ8FVHqiluHu4iNog2ooc-hNaOpHul0'
        latitude = -23.647778
        longitude = -46.573333
        response = model.generate_content([f"Com base na necessidade do usuário : {question}; Peço que identifique o tipo de localidade procurada dentre os da lista abaixo:'hospital','pharmacy','None'. Informe somente o tipo escolhido."])
        logging.debug(response.text)
        type = response.text
        results = search_nearby_hospitals(type ,api_key, latitude, longitude)
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
    except Exception as e:
        logging.debug(e)
        return jsonify({'error': str(e)}), 500


