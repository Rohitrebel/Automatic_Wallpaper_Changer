from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env file

MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
SANDBOX_URL = os.getenv('SANDBOX_URL')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
API_KEY = os.getenv('API_KEY')
DEVICE_ID = os.getenv('DEVICE_ID')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
FRAME_SIZE = int(os.getenv('FRAME_SIZE'))
MUL_FACTOR = int(os.getenv('MUL_FACTOR'))