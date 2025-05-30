import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Print email configuration
print(f'MAIL_SERVER: {os.environ.get("MAIL_SERVER")}')
print(f'MAIL_PORT: {os.environ.get("MAIL_PORT")}')
print(f'MAIL_USE_TLS: {os.environ.get("MAIL_USE_TLS")}')
print(f'MAIL_USERNAME: {os.environ.get("MAIL_USERNAME")}')
print(f'MAIL_PASSWORD: {os.environ.get("MAIL_PASSWORD")}')
print(f'MAIL_DEFAULT_SENDER: {os.environ.get("MAIL_DEFAULT_SENDER")}')
