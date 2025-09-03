import requests
import re
from config import VK_API_TOKEN, MAX_VIDEO_RESULTS

class VideoSearch:
    def __init__(self):
        self.vk_token = VK_API_TOKEN
    
    def search_youtube_videos(self, query):
        """Поиск видео на YouTube через поиск по ссылкам"""
        # YouTube не предоставляет бесплатный API для поиска
        # Поэтому мы будем использовать поиск по ссылкам из TheMealDB
        return []
    
    def search_vk_videos(self, query):
        """Поиск видео на VK"""
        if not self.vk_token:
            return []
        
        try:
            # VK API для поиска видео
            url = "https://api.vk.com/method/video.search"
            params = {
                'access_token': self.vk_token,
                'q': f"{query} рецепт",
                'count': MAX_VIDEO_RESULTS,
                'v': '5.131'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'response' in data and 'items' in data['response']:
                videos = []
                for item in data['response']['items']:
                    video_info = {
                        'title': item.get('title', ''),
                        'url': f"https://vk.com/video{item['owner_id']}_{item['id']}",
                        'platform': 'VK',
                        'duration': item.get('duration', 0)
                    }
                    videos.append(video_info)
                return videos
            else:
                return []
                
        except requests.RequestException as e:
            print(f"Ошибка VK API: {e}")
            return []
    
    def search_rutube_videos(self, query):
        """Поиск видео на Rutube через веб-скрапинг"""
        try:
            # Rutube не предоставляет публичный API, поэтому используем поиск по сайту
            search_url = f"https://rutube.ru/search/?text={query}%20рецепт"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Ищем ссылки на видео в HTML с более точным паттерном
            video_links = re.findall(r'href="(/video/[a-zA-Z0-9_-]+)"', response.text)
            
            videos = []
            for link in video_links[:MAX_VIDEO_RESULTS]:
                video_url = f"https://rutube.ru{link}"
                video_info = {
                    'title': f"Рецепт {query} на Rutube",
                    'url': video_url,
                    'platform': 'Rutube',
                    'duration': 0
                }
                videos.append(video_info)
            
            return videos
            
        except requests.RequestException as e:
            print(f"Ошибка Rutube поиска: {e}")
            return []
    
    def search_all_videos(self, recipe_name):
        """Поиск видео на всех платформах"""
        all_videos = []
        
        # Поиск на VK
        vk_videos = self.search_vk_videos(recipe_name)
        all_videos.extend(vk_videos)
        
        # Поиск на Rutube
        rutube_videos = self.search_rutube_videos(recipe_name)
        all_videos.extend(rutube_videos)
        
        return all_videos
    
    def format_video_links(self, videos):
        """Форматирование ссылок на видео для отображения"""
        if not videos:
            return ""
        
        video_text = "\n\n🎥 <b>Видеорецепты:</b>\n"
        
        for i, video in enumerate(videos[:3], 1):  # Показываем максимум 3 видео
            platform_icon = {
                'VK': '🔵',
                'Rutube': '🔴',
                'YouTube': '🔴'
            }.get(video['platform'], '📹')
            
            video_text += f"{i}. {platform_icon} <a href=\"{video['url']}\">{video['platform']} - {video['title']}</a>\n"
        
        return video_text
