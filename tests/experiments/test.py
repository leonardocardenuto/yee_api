#===========================================
#
#   TESTE DE ROTA GET_TEXT NO LOCALHOST!
#
#===========================================

import requests
import base64
import os

def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
    return encoded_string

def send_image_to_server(image_path, url):
    encoded_image = image_to_base64(image_path)
    data = {'email': 'teste', 'image_b64': encoded_image}
    response = requests.post(url, json=data)
    return response

image_path = "./tests/experiments/teste.jpeg"
url = "http://localhost:3000/get_text"
response = send_image_to_server(image_path, url)

if response.status_code == 200:
    response_json = response.json()
    if 'message' in response_json:
        message_json = response_json['message']
        print("Message returned from the server:")
        print(message_json)
        os.remove("./images/decoded_image.jpg")


    else:
        print("No message returned from the server.")
else:
    print("Failed to send image. Status code:", response.status_code)
