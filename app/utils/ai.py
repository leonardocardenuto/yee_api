import google.generativeai as genai
from app.config import logger , api_key_gemini
from app.utils.db import exec_query,commit

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

def ask_gemini(question):
    
    response = model.generate_content([question])

    return response.text
