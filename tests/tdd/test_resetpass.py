import unittest
import requests
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

class TestResetPasswordFunctionality(unittest.TestCase):
    def setUp(self):
        server = os.getenv('IP_ADRESS')
        self.base_url = f"http://{server}:3000"
        self.email = os.getenv('SENDER_EMAIL')
        self.password = "123"
        self.new_password = "new_password_123"
        self.uri = os.getenv('NEONDB')
        self.conn = psycopg2.connect(self.uri)
        self.cursor = self.conn.cursor()
        self.create_user_account()

    def create_user_account(self):
        url = f"{self.base_url}/create_user"
        data = {
            "email": self.email,
            "password": self.password,
            "confirm_password": self.password
        }
        response = requests.post(url, json=data)
        if response.status_code != 200:
            raise Exception(f"Failed to create user account: {response.text}")

    def tearDown(self):
        self.cursor.execute(f"DELETE FROM users WHERE email = '{self.email}'")
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def test_reset_password(self):
        url = f"{self.base_url}/change_pass"
        data = {
            "email": self.email,
            "password": self.new_password,
            "confirm_password": self.new_password
        }
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 200)
        login_url = f"{self.base_url}/login"
        login_data = {
            "email": self.email,
            "password": self.new_password
        }
        login_response = requests.post(login_url, json=login_data)
        self.assertEqual(login_response.status_code, 200)

    def test_reset_password_invalid_email(self):
        url = f"{self.base_url}/change_pass"
        data = {
            "email": 'invalidemail@example.com',
            "password": self.new_password,
            "confirm_password": '123'
        }
        response = requests.post(url, json=data)
        self.assertNotEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
