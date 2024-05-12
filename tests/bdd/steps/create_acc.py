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

@given('I have a valid email')
def step_registered_user(context):
    pass

@when('I fill the form')
def step_correct_credentials(context):
    global registration_response
    url = "http://localhost:3000/create_user"
    data = { "email": standard_mail, "password" : "123", "confirm_password" : "123" }
    registration_response = None
    while registration_response is None:
        registration_response = requests.post(url, json=data)
        time.sleep(1) 

@then('I should be registered successfully')
def step_logged_in_successfully(context):
    assert registration_response.status_code == 200
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE email = '{standard_mail}'")
    conn.commit()
    cursor.close()

@given('I do not have a valid email')
def step_registered_user(context):
    pass

@when('I fill the form with the invalid email and the rest of info')
def step_incorrect_credentials(context):
    global registration_response
    url = "http://localhost:3000/create_user"
    data = { "email": standard_mail, "password" : "123", "confirm_password" : "incorrect" }
    registration_response = None
    while registration_response is None:
        registration_response = requests.post(url, json=data)
        time.sleep(1) 

@then('I should see an error message stating that for some reason it did not work')
def step_see_error_message(context):
    assert registration_response.status_code != 200
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE email = '{standard_mail}'")
    conn.commit()
    cursor.close()
    conn.close()
