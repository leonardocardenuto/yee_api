import requests
from dotenv import load_dotenv
import os
import time
import psycopg2

load_dotenv()

change_response = None
uri = os.getenv('NEONDB')
conn = psycopg2.connect(uri)
standard_mail = os.getenv('SENDER_EMAIL')
server = os.getenv('IP_ADRESS')

@given('I forgot my password')
def step_forgot_password(context):
    pass

@when('I insert a new one and confirm it')
def step_insert_new_password(context):
    global change_response
    url = f"http://{server}:3000/create_user"
    data = { "email": standard_mail, "password" : "123", "confirm_password" : "123" }
    requests.post(url, json=data)
    url = f"http://{server}:3000/change_pass"
    change_response = None
    while change_response is None:
        change_response = requests.post(url, json=data)
        time.sleep(1) 

@then('it should be changed')
def step_password_changed_successfully(context):
    assert change_response.status_code == 200
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE email = '{standard_mail}'")
    conn.commit()
    cursor.close()

@given('I forgot my password and I make a mistake')
def step_forgot_password_with_mistake(context):
    pass

@when('I insert a new one and confirm it and they dont match')
def step_insert_mismatched_password(context):
    global change_response
    url = f"http://{server}:3000/create_user"
    data = { "email": standard_mail, "password" : "123", "confirm_password" : "incorrect" }
    change_response = None
    requests.post(url, json=data)
    url = f"http://{server}:3000/change_pass"
    change_response = None
    while change_response is None:
        change_response = requests.post(url, json=data)
        time.sleep(1) 

@then('it should display an error')
def step_display_error_message(context):
    assert change_response.status_code != 200
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE email = '{standard_mail}'")
    conn.commit()
    cursor.close()
    conn.close()
