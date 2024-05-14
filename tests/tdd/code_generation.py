import unittest
import requests
from dotenv import load_dotenv
import os
import psycopg2
import smtplib

load_dotenv()

class TestUserAuthentication(unittest.TestCase):
    def setUp(self):
        server = os.getenv('IP_ADRESS')
        self.base_url = f"http://{server}:3000/"
        self.email = os.getenv('SENDER_EMAIL')
        self.uri = os.getenv('NEONDB')
        self.conn = psycopg2.connect(self.uri)
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.cursor.execute(f"UPDATE users SET confirmation_code = null WHERE email = '{self.email}'")
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def test_code_generation_db(self):
        url = f"{self.base_url}/gen_code"
        data = {"email": self.email}
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 200)
        
    def test_wrong_email(self):
        url = f"{self.base_url}/gen_code"
        data = { "email": "wrong_email"}
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 409)
 
if __name__ == '__main__':
    unittest.main()