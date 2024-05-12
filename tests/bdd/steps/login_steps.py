import requests
from dotenv import load_dotenv
import os
import time
import psycopg2

load_dotenv()

registration_response = None
login_response = None
uri = os.getenv('NEONDB')
conn = psycopg2.connect(uri)
standard_mail = os.getenv('SENDER_EMAIL')

@given('I am a registered user')
def step_registered_user(context):
    global registration_response
    url = "http://localhost:3000/create_user"
    data = { "email": standard_mail, "password" : "123", "confirm_password" : "123" }
    registration_response = None
    while registration_response is None:
        registration_response = requests.post(url, json=data)
        time.sleep(1) 
    assert registration_response.status_code == 200

@when('I enter my correct username and password')
def step_correct_credentials(context):
    global login_response
    url = "http://localhost:3000/login"
    data = { "email": standard_mail, "password" : "123" }
    login_response = None
    while login_response is None:
        login_response = requests.post(url, json=data)
        time.sleep(1)

@then('I should be logged in successfully')
def step_logged_in_successfully(context):
    assert login_response is not None
    assert login_response.status_code == 200
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE email = '{standard_mail}'")
    conn.commit()
    cursor.close()

@when('I enter an incorrect username or password')
def step_incorrect_credentials(context):
    global login_response
    url = "http://localhost:3000/login"
    data = { "email": os.getenv('SENDER_EMAIL'), "password" : "incorrect" }
    login_response = None
    while login_response is None:
        login_response = requests.post(url, json=data)
        time.sleep(1)

@then('I should see an error message')
def step_see_error_message(context):
    assert login_response is not None
    assert login_response.status_code != 200
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE email = '{standard_mail}'")
    conn.commit()
    cursor.close()
    conn.close()
