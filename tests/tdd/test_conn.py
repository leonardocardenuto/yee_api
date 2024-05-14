import unittest
from unittest.mock import patch
import requests
from dotenv import load_dotenv
import os

load_dotenv()

class TestDbConn(unittest.TestCase):
    
    def setUp(self):
        server = os.getenv('IP_ADRESS')
        self.base_url = f"http://{server}:3000"
    
    def test_db_conn(self):
        url = f"{self.base_url}/check_connection"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)

    @patch('requests.get')
    def test_failed_conn(self, mock_get):
        mock_get.return_value.status_code = 500
        url = f"{self.base_url}/check_connection"
        response = requests.get(url)
        self.assertNotEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
