import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração do logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# NeonDB URI
uri = os.getenv('NEONDB')

# Api Keys
api_key_gemini = os.getenv('API_KEY_GEM')
api_key_maps = os.getenv('API_KEY_MAPS')

# Mail Config
smtp_server = "smtp.office365.com"
sender_email = "no-reply-appye@hotmail.com"
sender_password = "yeeapp123"
port = 587
