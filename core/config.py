from dotenv import load_dotenv
import os

load_dotenv()  # Automatically loads .env from root

DATABASE_URL = os.getenv("DATABASE_URL")

API_KEY = os.getenv("API_KEY")
