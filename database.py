import sqlite3
from config import DATABASE_NAME
from datetime import datetime

class Database:
    def __init__(self):
        self.db_name = DATABASE_NAME
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица избранных рецептов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorite_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                recipe_id INTEGER,
                recipe_title TEXT,
                recipe_image TEXT,
                recipe_url TEXT,
                rating INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, recipe_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, username=None, first_name=None, last_name=None):
        """Добавление нового пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        
        conn.commit()
        conn.close()
    
    def add_favorite_recipe(self, user_id, recipe_id, recipe_title, recipe_image, recipe_url):
        """Добавление рецепта в избранное"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO favorite_recipes (user_id, recipe_id, recipe_title, recipe_image, recipe_url)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, recipe_id, recipe_title, recipe_image, recipe_url))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Рецепт уже в избранном
            return False
        finally:
            conn.close()
    
    def remove_favorite_recipe(self, user_id, recipe_id):
        """Удаление рецепта из избранного"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM favorite_recipes 
            WHERE user_id = ? AND recipe_id = ?
        ''', (user_id, recipe_id))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def get_favorite_recipes(self, user_id):
        """Получение всех избранных рецептов пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT recipe_id, recipe_title, recipe_image, recipe_url, rating, added_at
            FROM favorite_recipes 
            WHERE user_id = ?
            ORDER BY rating DESC, added_at DESC
        ''', (user_id,))
        
        recipes = cursor.fetchall()
        conn.close()
        
        return [
            {
                'recipe_id': recipe[0],
                'title': recipe[1],
                'image': recipe[2],
                'url': recipe[3],
                'rating': recipe[4],
                'added_at': recipe[5]
            }
            for recipe in recipes
        ]
    
    def is_favorite_recipe(self, user_id, recipe_id):
        """Проверка, находится ли рецепт в избранном"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM favorite_recipes 
            WHERE user_id = ? AND recipe_id = ?
        ''', (user_id, recipe_id))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def update_recipe_rating(self, user_id, recipe_id, rating):
        """Обновление рейтинга рецепта"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE favorite_recipes 
            SET rating = ?
            WHERE user_id = ? AND recipe_id = ?
        ''', (rating, user_id, recipe_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    def get_recipe_rating(self, user_id, recipe_id):
        """Получение рейтинга рецепта"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT rating FROM favorite_recipes 
            WHERE user_id = ? AND recipe_id = ?
        ''', (user_id, recipe_id))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
