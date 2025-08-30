import os

# Bot Token
BOT_TOKEN = "8198276297:AAH_3Fc7Xr9_tUa6HfiH8jwncs3gy8ZAalQ"

# PostgreSQL Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '6200')
DB_NAME = os.getenv('DB_NAME', 'genbot')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '123321')
