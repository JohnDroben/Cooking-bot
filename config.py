import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# TheMealDB API
THEMEALDB_BASE_URL = 'https://www.themealdb.com/api/json/v1/1'

# Video Search APIs
VK_API_TOKEN = os.getenv('VK_API_TOKEN', '')  # VK API токен для поиска видео
RUTUBE_API_TOKEN = os.getenv('RUTUBE_API_TOKEN', '')  # Rutube API токен (если доступен)

# Database
DATABASE_NAME = 'recipes.db'

# Bot settings
MAX_RECIPES_PER_SEARCH = 5
MAX_FAVORITES_PER_USER = 50
MAX_VIDEO_RESULTS = 3  # Максимальное количество видео для каждого сервиса
