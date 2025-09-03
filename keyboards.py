from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    """Главное меню с двумя основными действиями (ReplyKeyboardMarkup)"""
    keyboard = [
        [KeyboardButton("🔍 Поиск рецептов")],
        [KeyboardButton("❤️ Мои рецепты")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_inline_main_menu_keyboard():
    """Главное меню с двумя основными действиями (InlineKeyboardMarkup)"""
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск рецептов", callback_data="search_recipes")],
        [InlineKeyboardButton("❤️ Мои рецепты", callback_data="my_recipes")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_recipe_actions_keyboard(recipe_id, is_favorite=False, rating=0):
    """Клавиатура для действий с рецептом"""
    keyboard = []
    
    if is_favorite:
        keyboard.append([
            InlineKeyboardButton("❌ Убрать из избранного", callback_data=f"remove_favorite_{recipe_id}")
        ])
        # Добавляем кнопки рейтинга для избранных рецептов
        rating_row = []
        for i in range(1, 6):
            star = "⭐" if i <= rating else "☆"
            rating_row.append(InlineKeyboardButton(star, callback_data=f"rate_{recipe_id}_{i}"))
        keyboard.append(rating_row)
    else:
        keyboard.append([
            InlineKeyboardButton("❤️ Добавить в избранное", callback_data=f"add_favorite_{recipe_id}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔍 Найти похожие", callback_data=f"similar_{recipe_id}")
    ])
    
    keyboard.append([
        InlineKeyboardButton("🎥 Больше видео", callback_data=f"more_videos_{recipe_id}")
    ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 Назад к поиску", callback_data="back_to_search")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_favorite_recipe_keyboard(recipe_id):
    """Клавиатура для избранного рецепта"""
    keyboard = [
        [InlineKeyboardButton("❌ Удалить из избранного", callback_data=f"remove_favorite_{recipe_id}")],
        [InlineKeyboardButton("🔙 Назад к избранному", callback_data="back_to_favorites")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_search_options_keyboard():
    """Клавиатура с опциями поиска"""
    keyboard = [
        [InlineKeyboardButton("🎲 Случайные рецепты", callback_data="random_recipes")],
        [InlineKeyboardButton("🏷️ По категориям", callback_data="search_by_category")],
        [InlineKeyboardButton("🌍 По кухням мира", callback_data="search_by_area")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_favorites_menu_keyboard():
    """Клавиатура для меню избранного"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_rating_keyboard(recipe_id):
    """Клавиатура для оценки рецепта"""
    keyboard = []
    rating_row = []
    for i in range(1, 6):
        rating_row.append(InlineKeyboardButton(f"{i}⭐", callback_data=f"rate_{recipe_id}_{i}"))
    keyboard.append(rating_row)
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_recipe")])
    return InlineKeyboardMarkup(keyboard)

def get_categories_keyboard(categories):
    """Клавиатура с категориями"""
    keyboard = []
    for category in categories[:12]:  # Ограничиваем количество кнопок
        keyboard.append([
            InlineKeyboardButton(category['strCategory'], callback_data=f"category_{category['strCategory']}")
        ])
    keyboard.append([InlineKeyboardButton("🔙 Назад к поиску", callback_data="back_to_search")])
    return InlineKeyboardMarkup(keyboard)

def get_areas_keyboard(areas):
    """Клавиатура с кухнями мира"""
    keyboard = []
    for area in areas[:12]:  # Ограничиваем количество кнопок
        keyboard.append([
            InlineKeyboardButton(area['strArea'], callback_data=f"area_{area['strArea']}")
        ])
    keyboard.append([InlineKeyboardButton("🔙 Назад к поиску", callback_data="back_to_search")])
    return InlineKeyboardMarkup(keyboard)
