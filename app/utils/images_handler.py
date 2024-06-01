import PIL.Image
import base64
from PIL import Image
from io import BytesIO


def restore_image(image_data):
    image_data = base64.b64decode(image_data)
    decoded_image = Image.open(BytesIO(image_data))
    decoded_image.save("./images/decoded_image.jpg")
    img = PIL.Image.open('./images/decoded_image.jpg')
    return img