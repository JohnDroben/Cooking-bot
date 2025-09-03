import requests
from config import THEMEALDB_BASE_URL, MAX_RECIPES_PER_SEARCH
from video_search import VideoSearch

class RecipeAPI:
    def __init__(self):
        self.base_url = THEMEALDB_BASE_URL
        self.video_search = VideoSearch()
    
    def search_recipes(self, query, number=MAX_RECIPES_PER_SEARCH):
        """Поиск рецептов по запросу"""
        url = f"{self.base_url}/search.php"
        params = {
            's': query
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # TheMealDB возвращает список рецептов в поле 'meals'
            if data.get('meals'):
                # Ограничиваем количество результатов
                return {'meals': data['meals'][:number]}
            else:
                return {'meals': []}
        except requests.RequestException as e:
            return {"error": f"Ошибка API: {str(e)}"}
    
    def get_recipe_details(self, recipe_id):
        """Получение детальной информации о рецепте"""
        url = f"{self.base_url}/lookup.php"
        params = {
            'i': recipe_id
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('meals'):
                return data['meals'][0]  # Возвращаем первый рецепт
            else:
                return {"error": "Рецепт не найден"}
        except requests.RequestException as e:
            return {"error": f"Ошибка API: {str(e)}"}
    
    def get_random_recipes(self, number=5):
        """Получение случайных рецептов"""
        recipes = []
        
        try:
            # TheMealDB возвращает только один случайный рецепт за запрос
            # Поэтому делаем несколько запросов
            for _ in range(min(number, 10)):  # Ограничиваем максимум 10 запросов
                url = f"{self.base_url}/random.php"
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data.get('meals'):
                    recipes.append(data['meals'][0])
                
                # Небольшая задержка между запросами
                import time
                time.sleep(0.1)
            
            return {'meals': recipes}
        except requests.RequestException as e:
            return {"error": f"Ошибка API: {str(e)}"}
    
    def get_categories(self):
        """Получение списка категорий"""
        url = f"{self.base_url}/categories.php"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('categories', [])
        except requests.RequestException as e:
            return {"error": f"Ошибка API: {str(e)}"}
    
    def get_areas(self):
        """Получение списка кухонь мира"""
        url = f"{self.base_url}/list.php?a=list"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('meals', [])
        except requests.RequestException as e:
            return {"error": f"Ошибка API: {str(e)}"}
    
    def get_recipes_by_category(self, category):
        """Получение рецептов по категории"""
        url = f"{self.base_url}/filter.php"
        params = {'c': category}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('meals', [])
        except requests.RequestException as e:
            return {"error": f"Ошибка API: {str(e)}"}
    
    def get_recipes_by_area(self, area):
        """Получение рецептов по кухне"""
        url = f"{self.base_url}/filter.php"
        params = {'a': area}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('meals', [])
        except requests.RequestException as e:
            return {"error": f"Ошибка API: {str(e)}"}
    
    def format_recipe_info(self, recipe):
        """Форматирование информации о рецепте для отображения"""
        title = recipe.get('strMeal', 'Без названия')
        image = recipe.get('strMealThumb', '')
        category = recipe.get('strCategory', 'Не указано')
        area = recipe.get('strArea', 'Не указано')
        instructions = recipe.get('strInstructions', 'Инструкции не найдены')
        
        # Собираем ингредиенты
        ingredients = []
        for i in range(1, 21):  # TheMealDB может иметь до 20 ингредиентов
            ingredient = recipe.get(f'strIngredient{i}')
            measure = recipe.get(f'strMeasure{i}')
            if ingredient and ingredient.strip():
                ingredients.append(f"• {ingredient} - {measure or 'по вкусу'}")
        
        # Ограничиваем длину инструкций
        if len(instructions) > 500:
            instructions = instructions[:500] + "..."
        
        # Формируем текст с ингредиентами
        ingredients_text = "\n".join(ingredients[:10])  # Показываем первые 10 ингредиентов
        if len(ingredients) > 10:
            ingredients_text += f"\n... и еще {len(ingredients) - 10} ингредиентов"
        
        # Проверяем наличие видеорецепта из TheMealDB
        youtube_url = recipe.get('strYoutube', '')
        video_text = ""
        
        if youtube_url:
            video_text += f"\n🎥 <a href=\"{youtube_url}\">YouTube видеорецепт</a>"
        
        # Ищем дополнительные видео на других платформах
        additional_videos = self.video_search.search_all_videos(title)
        if additional_videos:
            video_text += self.video_search.format_video_links(additional_videos)
        
        formatted_text = f"""
🍽️ <b>{title}</b>

🏷️ Категория: {category}
🌍 Кухня: {area}

📋 <b>Ингредиенты:</b>
{ingredients_text}

📝 <b>Инструкция:</b>
{instructions}

🔗 <a href="{recipe.get('strSource', '')}">Подробнее</a>{video_text}
        """.strip()
        
        return {
            'title': title,
            'image': image,
            'text': formatted_text,
            'recipe_id': recipe.get('idMeal'),
            'source_url': recipe.get('strSource', '')
        }
