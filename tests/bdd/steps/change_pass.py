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
def step_password_match(context):
    global registration_response
    url = f"http://{server}:3000/change_pass"
    data = { "email": standard_mail, "password" : None, "confirm_password" : None }
    registration_response = None
    while registration_response is None:
        registration_response = requests.post(url, json=data)
        time.sleep(1) 
    assert registration_response.status_code == 200

@when('I create a new password and confirm it')
def step_correct_credentials(context):
    global registration_response
    url = f"http://{server}:3000/change_pass"
    data = { "email": standard_mail, "password" : "123", "confirm_password" : "123" }
    registration_response = None
    while registration_response is None:
        registration_response = requests.post(url, json=data)
        time.sleep(1) 

@then('the password should be changed in the database')
def step_password_changed_successfully(context):
    assert registration_response.status_code == 200
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET password = '123' WHERE email = '{standard_mail}'")
    conn.commit()
    cursor.close()

@when('I enter a new password and its confirmation and they do not match')
def step_incorrect_credentials(context):
    global registration_response
    url = f"http://{server}:3000/change_pass"
    data = { "email": standard_mail, "password" : "123", "confirm_password" : "incorrect" }
    registration_response = None
    while registration_response is None:
        registration_response = requests.post(url, json=data)
        time.sleep(1) 

@then('I should see an error message and the password is not changed in the database')
def step_see_error_message(context):
    assert registration_response.status_code != 200