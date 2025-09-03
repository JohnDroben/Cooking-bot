import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
from config import TELEGRAM_TOKEN
from database import Database
from api_client import RecipeAPI
from keyboards import (
    get_main_menu_keyboard, 
    get_recipe_actions_keyboard, 
    get_search_options_keyboard,
    get_favorites_menu_keyboard,
    get_rating_keyboard,
    get_categories_keyboard,
    get_areas_keyboard,
    get_inline_main_menu_keyboard
)



# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация компонентов
db = Database()
api = RecipeAPI()

# Словарь для хранения состояний пользователей
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id
    
    # Добавляем пользователя в базу данных
    db.add_user(user_id, user.username, user.first_name, user.last_name)
    
    welcome_message = f"""
👋 Привет, {user.first_name}!

🍳 Я - бот для поиска рецептов! 

Что я умею:
• 🔍 Искать рецепты по названию или ингредиентам
• ❤️ Сохранять понравившиеся рецепты в избранное
• 📱 Показывать ваши сохраненные рецепты

Выберите действие:
    """.strip()
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if text == "🔍 Поиск рецептов":
        await show_search_options(update, context)
    elif text == "❤️ Мои рецепты":
        await show_favorites(update, context)
    elif user_id in user_states and user_states[user_id] == "waiting_for_search":
        await search_recipes(update, context, text)
    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки меню для навигации.",
            reply_markup=get_main_menu_keyboard()
        )

async def show_search_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать опции поиска"""
    user_id = update.effective_user.id
    user_states[user_id] = "search_options"
    
    message = """
🔍 <b>Поиск рецептов</b>

Выберите способ поиска:
• Напишите название блюда или ингредиенты
• Или выберите случайные рецепты
    """.strip()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=get_search_options_keyboard()
        )
    else:
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=get_search_options_keyboard()
        )

async def search_recipes(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """Поиск рецептов"""
    user_id = update.effective_user.id
    
    if not query:
        query = update.message.text
    
    await update.message.reply_text("🔍 Ищу рецепты...")
    
    # Поиск рецептов через API
    result = api.search_recipes(query)
    
    if "error" in result:
        await update.message.reply_text(f"❌ Ошибка: {result['error']}")
        return
    
    recipes = result.get('meals', [])
    
    if not recipes:
        await update.message.reply_text(
            "😔 Рецепты не найдены. Попробуйте другой запрос.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Показываем найденные рецепты
    for recipe in recipes:
        formatted_recipe = api.format_recipe_info(recipe)
        is_favorite = db.is_favorite_recipe(user_id, formatted_recipe['recipe_id'])
        rating = db.get_recipe_rating(user_id, formatted_recipe['recipe_id']) if is_favorite else 0
        
        if formatted_recipe['image']:
            await update.message.reply_photo(
                photo=formatted_recipe['image'],
                caption=formatted_recipe['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=get_recipe_actions_keyboard(
                    formatted_recipe['recipe_id'], 
                    is_favorite,
                    rating
                )
            )
        else:
            await update.message.reply_text(
                formatted_recipe['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=get_recipe_actions_keyboard(
                    formatted_recipe['recipe_id'], 
                    is_favorite,
                    rating
                )
            )
    
    user_states[user_id] = "search_results"

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать избранные рецепты"""
    user_id = update.effective_user.id
    user_states[user_id] = "favorites"
    
    favorites = db.get_favorite_recipes(user_id)
    
    if not favorites:
        message = "❤️ У вас пока нет избранных рецептов.\n\nНайдите интересные рецепты и добавьте их в избранное!"
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=get_favorites_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=get_favorites_menu_keyboard()
            )
        return
    
    message = f"❤️ <b>Ваши избранные рецепты</b> ({len(favorites)} шт.)\n\n"
    
    for i, recipe in enumerate(favorites, 1):
        rating = recipe.get('rating', 0)
        rating_stars = "⭐" * rating + "☆" * (5 - rating)
        message += f"{i}. {recipe['title']} {rating_stars}\n"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=get_favorites_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=get_favorites_menu_keyboard()
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data.startswith("add_favorite_"):
        recipe_id = int(data.split("_")[2])
        await add_to_favorites(update, context, recipe_id)
    
    elif data.startswith("remove_favorite_"):
        recipe_id = int(data.split("_")[2])
        await remove_from_favorites(update, context, recipe_id)
    
    elif data.startswith("rate_"):
        parts = data.split("_")
        recipe_id = int(parts[1])
        rating = int(parts[2])
        await rate_recipe(update, context, recipe_id, rating)
    
    elif data == "random_recipes":
        await get_random_recipes(update, context)
    
    elif data == "search_by_category":
        await show_categories(update, context)
    
    elif data == "search_by_area":
        await show_areas(update, context)
    
    elif data.startswith("category_"):
        category = data.split("_", 1)[1]
        await search_by_category(update, context, category)
    
    elif data.startswith("area_"):
        area = data.split("_", 1)[1]
        await search_by_area(update, context, area)
    
    elif data.startswith("more_videos_"):
        recipe_id = int(data.split("_")[2])
        await show_more_videos(update, context, recipe_id)
    
    elif data == "back_to_main":
        await back_to_main_menu(update, context)
    
    elif data == "back_to_search":
        await show_search_options(update, context)
    
    elif data == "back_to_favorites":
        await show_favorites(update, context)

async def add_to_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE, recipe_id):
    """Добавить рецепт в избранное"""
    user_id = update.effective_user.id
    
    # Получаем информацию о рецепте
    recipe_info = api.get_recipe_details(recipe_id)
    
    if "error" in recipe_info:
        await update.callback_query.edit_message_text(f"❌ Ошибка: {recipe_info['error']}")
        return
    
    # Добавляем в базу данных
    success = db.add_favorite_recipe(
        user_id,
        recipe_id,
        recipe_info.get('strMeal', ''),
        recipe_info.get('strMealThumb', ''),
        recipe_info.get('strSource', '')
    )
    
    if success:
        await update.callback_query.answer("✅ Рецепт добавлен в избранное!")
        # Обновляем клавиатуру с рейтингом 0
        await update.callback_query.edit_message_reply_markup(
            get_recipe_actions_keyboard(recipe_id, True, 0)
        )
    else:
        # Если рецепт уже в избранном, получаем его текущий рейтинг
        current_rating = db.get_recipe_rating(user_id, recipe_id)
        await update.callback_query.answer("⚠️ Рецепт уже в избранном!")
        # Обновляем клавиатуру с текущим рейтингом
        await update.callback_query.edit_message_reply_markup(
            get_recipe_actions_keyboard(recipe_id, True, current_rating)
        )

async def remove_from_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE, recipe_id):
    """Удалить рецепт из избранного"""
    user_id = update.effective_user.id
    
    success = db.remove_favorite_recipe(user_id, recipe_id)
    
    if success:
        await update.callback_query.answer("✅ Рецепт удален из избранного!")
        # Обновляем клавиатуру без рейтинга
        await update.callback_query.edit_message_reply_markup(
            get_recipe_actions_keyboard(recipe_id, False, 0)
        )
    else:
        await update.callback_query.answer("❌ Рецепт не найден в избранном!")

async def rate_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE, recipe_id, rating):
    """Оценить рецепт"""
    user_id = update.effective_user.id
    
    try:
        # Проверяем, что рецепт в избранном
        if not db.is_favorite_recipe(user_id, recipe_id):
            await update.callback_query.answer("❌ Сначала добавьте рецепт в избранное!")
            return
        
        # Обновляем рейтинг
        success = db.update_recipe_rating(user_id, recipe_id, rating)
        
        if success:
            await update.callback_query.answer(f"✅ Оценка {rating}⭐ установлена!")
            # Обновляем клавиатуру с новым рейтингом
            await update.callback_query.edit_message_reply_markup(
                get_recipe_actions_keyboard(recipe_id, True, rating)
            )
        else:
            await update.callback_query.answer("❌ Ошибка при установке рейтинга!")
    except Exception as e:
        logger.error(f"Ошибка при установке рейтинга: {e}")
        await update.callback_query.answer("❌ Ошибка при установке рейтинга!")

async def show_more_videos(update: Update, context: ContextTypes.DEFAULT_TYPE, recipe_id):
    """Показать дополнительные видео для рецепта"""
    user_id = update.effective_user.id
    
    # Получаем информацию о рецепте
    recipe_info = api.get_recipe_details(recipe_id)
    
    if "error" in recipe_info:
        await update.callback_query.answer("❌ Ошибка при получении рецепта!")
        return
    
    recipe_title = recipe_info.get('strMeal', 'Рецепт')
    
    try:
        # Пытаемся отредактировать сообщение
        await update.callback_query.edit_message_text("🎥 Ищу дополнительные видео...")
        edit_message = True
    except:
        # Если не удалось отредактировать (например, сообщение содержит только медиа), отправляем новое
        edit_message = False
        await update.callback_query.answer("🎥 Ищу дополнительные видео...")
    
    # Ищем видео на всех платформах
    videos = api.video_search.search_all_videos(recipe_title)
    
    if not videos:
        message = f"😔 Дополнительные видео для '{recipe_title}' не найдены."
        if edit_message:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=get_recipe_actions_keyboard(recipe_id, False, 0)
            )
        else:
            await update.callback_query.message.reply_text(
                message,
                reply_markup=get_recipe_actions_keyboard(recipe_id, False, 0)
            )
        return
    
    # Формируем сообщение с видео
    message = f"🎥 <b>Видеорецепты для '{recipe_title}':</b>\n\n"
    
    for i, video in enumerate(videos, 1):
        platform_icon = {
            'VK': '🔵',
            'Rutube': '🔴',
            'YouTube': '🔴'
        }.get(video['platform'], '📹')
        
        message += f"{i}. {platform_icon} <a href=\"{video['url']}\">{video['platform']} - {video['title']}</a>\n"
    
    message += f"\n🔙 <a href=\"#\">Назад к рецепту</a>"
    
    if edit_message:
        await update.callback_query.edit_message_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=get_recipe_actions_keyboard(recipe_id, False, 0)
        )
    else:
        await update.callback_query.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=get_recipe_actions_keyboard(recipe_id, False, 0)
        )

async def get_random_recipes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить случайные рецепты"""
    user_id = update.effective_user.id
    user_states[user_id] = "search_results"
    
    await update.callback_query.edit_message_text("🎲 Ищу случайные рецепты...")
    
    result = api.get_random_recipes(3)
    
    if "error" in result:
        await update.callback_query.edit_message_text(f"❌ Ошибка: {result['error']}")
        return
    
    recipes = result.get('meals', [])
    
    if not recipes:
        await update.callback_query.edit_message_text("😔 Не удалось найти рецепты.")
        return
    
    for recipe in recipes:
        formatted_recipe = api.format_recipe_info(recipe)
        is_favorite = db.is_favorite_recipe(user_id, formatted_recipe['recipe_id'])
        rating = db.get_recipe_rating(user_id, formatted_recipe['recipe_id']) if is_favorite else 0
        
        if formatted_recipe['image']:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=formatted_recipe['image'],
                caption=formatted_recipe['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=get_recipe_actions_keyboard(
                    formatted_recipe['recipe_id'], 
                    is_favorite,
                    rating
                )
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=formatted_recipe['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=get_recipe_actions_keyboard(
                    formatted_recipe['recipe_id'], 
                    is_favorite,
                    rating
                )
            )

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать категории рецептов"""
    await update.callback_query.edit_message_text("🏷️ Загружаю категории...")
    
    categories = api.get_categories()
    
    if "error" in categories:
        await update.callback_query.edit_message_text(f"❌ Ошибка: {categories['error']}")
        return
    
    if not categories:
        await update.callback_query.edit_message_text("😔 Категории не найдены.")
        return
    
    message = "🏷️ <b>Выберите категорию:</b>"
    await update.callback_query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=get_categories_keyboard(categories)
    )

async def show_areas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать кухни мира"""
    await update.callback_query.edit_message_text("🌍 Загружаю кухни мира...")
    
    areas = api.get_areas()
    
    if "error" in areas:
        await update.callback_query.edit_message_text(f"❌ Ошибка: {areas['error']}")
        return
    
    if not areas:
        await update.callback_query.edit_message_text("😔 Кухни не найдены.")
        return
    
    message = "🌍 <b>Выберите кухню мира:</b>"
    await update.callback_query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=get_areas_keyboard(areas)
    )

async def search_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category):
    """Поиск рецептов по категории"""
    user_id = update.effective_user.id
    user_states[user_id] = "search_results"
    
    await update.callback_query.edit_message_text(f"🏷️ Ищу рецепты в категории '{category}'...")
    
    recipes = api.get_recipes_by_category(category)
    
    if "error" in recipes:
        await update.callback_query.edit_message_text(f"❌ Ошибка: {recipes['error']}")
        return
    
    if not recipes:
        await update.callback_query.edit_message_text("😔 Рецепты не найдены в этой категории.")
        return
    
    # Получаем полную информацию о рецептах
    full_recipes = []
    for recipe in recipes[:5]:  # Ограничиваем до 5 рецептов
        recipe_details = api.get_recipe_details(recipe['idMeal'])
        if "error" not in recipe_details:
            full_recipes.append(recipe_details)
    
    if not full_recipes:
        await update.callback_query.edit_message_text("😔 Не удалось загрузить рецепты.")
        return
    
    # Отправляем рецепты
    for recipe in full_recipes:
        formatted_recipe = api.format_recipe_info(recipe)
        is_favorite = db.is_favorite_recipe(user_id, formatted_recipe['recipe_id'])
        rating = db.get_recipe_rating(user_id, formatted_recipe['recipe_id']) if is_favorite else 0
        
        if formatted_recipe['image']:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=formatted_recipe['image'],
                caption=formatted_recipe['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=get_recipe_actions_keyboard(
                    formatted_recipe['recipe_id'], 
                    is_favorite,
                    rating
                )
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=formatted_recipe['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=get_recipe_actions_keyboard(
                    formatted_recipe['recipe_id'], 
                    is_favorite,
                    rating
                )
            )

async def search_by_area(update: Update, context: ContextTypes.DEFAULT_TYPE, area):
    """Поиск рецептов по кухне"""
    user_id = update.effective_user.id
    user_states[user_id] = "search_results"
    
    await update.callback_query.edit_message_text(f"🌍 Ищу рецепты кухни '{area}'...")
    
    recipes = api.get_recipes_by_area(area)
    
    if "error" in recipes:
        await update.callback_query.edit_message_text(f"❌ Ошибка: {recipes['error']}")
        return
    
    if not recipes:
        await update.callback_query.edit_message_text("😔 Рецепты не найдены в этой кухне.")
        return
    
    # Получаем полную информацию о рецептах
    full_recipes = []
    for recipe in recipes[:5]:  # Ограничиваем до 5 рецептов
        recipe_details = api.get_recipe_details(recipe['idMeal'])
        if "error" not in recipe_details:
            full_recipes.append(recipe_details)
    
    if not full_recipes:
        await update.callback_query.edit_message_text("😔 Не удалось загрузить рецепты.")
        return
    
    # Отправляем рецепты
    for recipe in full_recipes:
        formatted_recipe = api.format_recipe_info(recipe)
        is_favorite = db.is_favorite_recipe(user_id, formatted_recipe['recipe_id'])
        rating = db.get_recipe_rating(user_id, formatted_recipe['recipe_id']) if is_favorite else 0
        
        if formatted_recipe['image']:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=formatted_recipe['image'],
                caption=formatted_recipe['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=get_recipe_actions_keyboard(
                    formatted_recipe['recipe_id'], 
                    is_favorite,
                    rating
                )
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=formatted_recipe['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=get_recipe_actions_keyboard(
                    formatted_recipe['recipe_id'], 
                    is_favorite,
                    rating
                )
            )

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🏠 Главное меню",
            reply_markup=get_inline_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "🏠 Главное меню",
            reply_markup=get_main_menu_keyboard()
        )

def main():
    """Запуск бота"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN не настроен!")
        return
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

if __name__ == '__main__':
    main()
