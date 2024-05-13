import requests
from dotenv import load_dotenv
import os
import time
import psycopg2

server = os.getenv('IP_ADRESS')
load_dotenv()

check_response = None
uri = os.getenv('NEONDB')
conn = psycopg2.connect(uri)

@given('a valid database uri')
def step_registered_user(context):
    pass

@when('attempts to connect')
def step_correct_credentials(context):
    global check_response
    url = f"http://{server}:3000/check_connection"
    check_response = None
    while check_response is None:
        check_response = requests.get(url)
        time.sleep(1) 

@then('it should connect successfully')
def step_conn_successfully(context):
    assert check_response.status_code == 200