import requests
from dotenv import load_dotenv
import os
import time
import psycopg2

load_dotenv()

gen_response = None
uri = os.getenv('NEONDB')
conn = psycopg2.connect(uri)
standard_mail = os.getenv('SENDER_EMAIL')
server = os.getenv('IP_ADRESS')

@given('a valid email to  generate the code')
def step_registered_user(context):
    pass

@when('attempts to generate')
def step_correct_credentials(context):
    global gen_response
    url = f"http://{server}:3000/create_user"
    data = { "email": standard_mail, "password" : "123", "confirm_password" : "123" }
    requests.post(url, json=data)
    url = f"http://{server}:3000/gen_code"
    data = { "email": standard_mail}
    gen_response = None
    while gen_response is None:
        gen_response = requests.post(url, json=data)
        time.sleep(1) 

@then('it should generate successfully')
def step_generation_successfull(context):
    assert gen_response.status_code == 200
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE email = '{standard_mail}'")
    conn.commit()
    cursor.close()

@given('a invalid email to  generate the code')
def step_registered_user(context):
    pass

@when('attempts to generate it with a wrong email')
def step_incorrect_credentials(context):
    global gen_response
    url = f"http://{server}:3000/gen_code"
    data = { "email": standard_mail}
    gen_response = None
    while gen_response is None:
        gen_response = requests.post(url, json=data)
        time.sleep(1) 

@then('it should show some kind of error')
def step_see_error_message(context):
    assert gen_response.status_code != 200