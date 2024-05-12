import requests
from dotenv import load_dotenv
import os
import time
import psycopg2

load_dotenv()

check_response = None
uri = os.getenv('NEONDB')
conn = psycopg2.connect(uri)
standard_mail = os.getenv('SENDER_EMAIL')

@given('a valid database uri')
def step_registered_user(context):
    pass

@when('attempts to connect')
def step_correct_credentials(context):
    global check_response
    url = "http://localhost:3000/check_connection"
    check_response = None
    while check_response is None:
        check_response = requests.post(url)
        time.sleep(1) 

@then('it should connect successfully')
def step_logged_in_successfully(context):
    assert check_response.status_code == 200