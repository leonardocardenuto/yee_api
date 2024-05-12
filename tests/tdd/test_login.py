import unittest
import requests
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

class TestUserAuthentication(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:3000"
        self.email = os.getenv('SENDER_EMAIL')
        self.password = "123"
        self.uri = os.getenv('NEONDB')
        self.conn = psycopg2.connect(self.uri)
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.cursor.execute(f"DELETE FROM users WHERE email = '{self.email}'")
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def test_user_registration(self):
        url = f"{self.base_url}/create_user"
        data = { "email": self.email, "password": self.password, "confirm_password": self.password }
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 200)

    def test_successful_login(self):
        self._register_user()
        url = f"{self.base_url}/login"
        data = { "email": self.email, "password": self.password }
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 200)

    def test_failed_login(self):
        url = f"{self.base_url}/login"
        data = { "email": self.email, "password": "incorrect" }
        response = requests.post(url, json=data)
        self.assertNotEqual(response.status_code, 200)

    def _register_user(self):
        url = f"{self.base_url}/create_user"
        data = { "email": self.email, "password": self.password, "confirm_password": self.password }
        requests.post(url, json=data)

if __name__ == '__main__':
    unittest.main()
