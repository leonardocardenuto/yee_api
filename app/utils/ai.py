import google.generativeai as genai
from app.config import logger , api_key_gemini, api_key_maps
from flask import jsonify
from app.utils.db import fetch_schema, exec_query
import requests
import re

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
        "max_output_tokens":1000
        },
    safety_settings=safety_settings
    )
        
def identify_image(img):

    response = model.generate_content(["""Colete os dados da imagem e preencha o relatório abaixo com os dados sem unidades de medidas somente os números ( com vígulas ou sem ) caso não haja coloque como null.
        Relatório -
        Pressão: 
        Peso:
        Altura:
        Glicemia:
        """, img])
    
    return response.text

def ask_gemini(question, latitude, longitude, user_name, type=None):
    if not type:
        prompt = f'Com base na necessidade do usuário : {question}; ' \
                 f'Indique o tipo da solicitação dele, CONVERSA (em casos de cumprimentos ou agradecimentos), ' \
                 f'DADOS (em caso de perguntas relacionadas a algo externo) ou ' \
                 f'LOCALIDADE (em caso de solicitações de estabelecimentos próximos a ele). Exemplo de Output desejado: DADOS'
        response = model.generate_content([prompt])
        result = ask_gemini(question, latitude, longitude, user_name, (response.text).strip())
    else:
        result = None
        if 'CONVERSA' in type:
            prompt = f'Seu papel é, com base no input do usuário, ' \
                        f'cumprimentá-lo ou aceitar agradecimentos. Em caso de solicitações de apresentação, diga que você é o assistente virtual oficial da Yee. Input do usuário {question}'
            response = model.generate_content([prompt])
            result = response.text
        elif 'DADOS' in type:
            prompt = f'Seu papel é gerar uma consulta SQL filtrada pelo usuário em questão {user_name} com base nessa solicitação {question}, ' \
                    f'e a partir desse esquema PostgreSQL {fetch_schema()}. Você não deve fazer updates, create ou drop; caso seja requisitado, informe que não é capaz de fazê-lo.' \
                    f'Também não deve procurar nada no banco sem o usuário informado ou com outro usuário.'
            response = model.generate_content([prompt])

            query_returned = re.findall(r'sql\s+(.*?)\s+```', response.text, re.DOTALL)

            if query_returned:
                query_returned = query_returned[0]
            if not query_returned:
                result = response.text
            else:
                logger.debug(query_returned)
                result_db = exec_query(query_returned) 
                result_interpretation = model.generate_content(f'Traduza para linguagem natural o resultado do banco de dados {result_db}, que responde a pergunta do usuário {question} a ele.')
                result = result_interpretation.text.strip()
        elif 'LOCALIDADE' in type:
            prompt = f"Com base na necessidade do usuário : {question}; Peço que identifique o tipo de localidade procurada dentre os da lista abaixo:'hospital','pharmacy','None'. Informe somente o tipo escolhido."
            response = model.generate_content([prompt])
            type = response.text
            type = type.strip()
            result = search_nearby_hospitals(type, api_key_maps, latitude, longitude)
        else:
            raise ValueError("Tipo de solicitação desconhecido.")
    return result

def search_nearby_hospitals(place_type, api_key, latitude, longitude, radius=600):
    base_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = {
        'key': api_key,
        'location': f'{latitude},{longitude}',
        'radius': radius,
        'type': place_type,
        'rank_by': 'distance'
    }
    response = requests.get(base_url, params=params)
    result_string = ''
    if response.status_code == 200:
        data = response.json()
        if 'results' in data:
            result_string += f"Segue a lista dos estabelecimentos mais próximos de você em um raio de {radius} metros:"
            for item in data['results']:
                name = item['name']
                address = item['vicinity']
                rating = item.get('rating', 'N/A')
                result_string += f"\n\nNome: {name}\n"
                result_string += f"Endereço: {address}\n"
                result_string += f"Avaliação: {rating} estrelas\n"
        else:
            result_string = "Nenhum estabelecimento encontrado."
        return result_string
    else:
        return jsonify({'message': "Um erro ao vasculhar locais ocorreu!"}), 500
    