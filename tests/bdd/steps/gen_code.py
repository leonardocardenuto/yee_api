import requests
from dotenv import load_dotenv
import os
import time
import psycopg2

load_dotenv()

registration_response = None
uri = os.getenv('NEONDB')
conn = psycopg2.connect(uri)
standard_mail = os.getenv('SENDER_EMAIL')
server = os.getenv('IP_ADRESS')

@given('I am a registered user and forgot my password')
def step_registered_user(context):
    pass

@when('I give my email')
def step_registered_email(context):
    global registration_response
    url = f"http://{server}:3000/gen_code"
    data = { "email": standard_mail}
    registration_response = None
    while registration_response is None:
        registration_response = requests.post(url, json=data)
        time.sleep(1) 

@then('Then the a random code should be changed generated, inserted in db and sent by email')
def step_code_genereted_sent_successfully(context):
    assert registration_response.status_code == 200

@when('give my email and it is not sent or the code is note inserted in db')
def step_incorrect_credentials(context):
    global registration_response
    url = f"http://{server}:3000/gen_code"
    data = { "email": standard_mail}
    registration_response = None
    while registration_response != 200:
        registration_response = requests.post(url, json=data)
        time.sleep(1) 

@then('I should see an error message stating that for some reason it did not work')
def step_see_error_message(context):
    assert registration_response.status_code != 200
