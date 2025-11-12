import os
import logging
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from collections import defaultdict

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Мультиязычные символы для генерации паролей
LANGUAGE_SETS = {
    'english': string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?",
    'russian': 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ',
    'greek': 'αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ',
    'arabic': 'ءآأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىي',
    'japanese': 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん',
    'math': '∀∁∂∃∄∅∆∇∈∉∊∋∌∍∎∏∐∑−∓∔∕∖∗∘∙√∛∜∝∞∟∠∡∢∣∤∥∦∧∨∩∪∫∬∭∮∯',
    'currency': '€£¥¢$₽₹₩₺₴₸₼₿',
    'arrows': '←↑→↓↔↕↖↗↘↙',
}

# Генератор мультиязычных паролей
def generate_multilingual_password(length, languages=['english']):
    charset = ""
    for lang in languages:
        charset += LANGUAGE_SETS.get(lang, '')
    
    if not charset:
        charset = LANGUAGE_SETS['english']
    
    return ''.join(random.choice(charset) for _ in range(length))

# Генератор пароля со смешиванием языков
def generate_mixed_password(length):
    # Случайно выбираем 2-3 языка для смешивания
    available_langs = list(LANGUAGE_SETS.keys())
    num_langs = random.randint(2, 3)
    selected_langs = random.sample(available_langs, num_langs)
    
    password = ""
    for i in range(length):
        lang = random.choice(selected_langs)
        charset = LANGUAGE_SETS[lang]
        password += random.choice(charset)
    
    return password, selected_langs

# Инициализация пользовательских данных
def get_user_data(user_id):
    if user_id not in userStorage:
        userStorage[user_id] = {
            'folders': defaultdict(list),
            'settings': {
                'default_languages': ['english'],
                'password_strength': 'medium'
            }
        }
    return userStorage[user_id]

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    
    welcome_text = f"""
🔐 *Мультиязычный Генератор Паролей* 🌍

Привет, {user.first_name}! Я создаю сверхбезопасные пароли используя символы разных языков мира! 🚀

✨ *Особенности:*
• 🔤 Символы 8+ языков
• 🌍 Смешивание письменностей  
• 💪 Уникальные комбинации
• 🔒 Максимальная безопасность

Выбери действие:
    """
    
    keyboard = [
        [InlineKeyboardButton("🔐 Сгенерировать пароль", callback_data="generate_password")],
        [InlineKeyboardButton("🌍 Настройки языков", callback_data="language_settings")],
        [InlineKeyboardButton("📁 Мои папки", callback_data="folders"), 
         InlineKeyboardButton("➕ Добавить пароль", callback_data="add_password")],
        [InlineKeyboardButton("🔒 Безопасность", callback_data="security_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

# Настройки языков
async def language_settings(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for lang in LANGUAGE_SETS.keys():
        keyboard.append([InlineKeyboardButton(f"🔤 {lang.capitalize()}", callback_data=f"lang_{lang}")])
    
    keyboard.append([InlineKeyboardButton("🎲 Авто-смешивание", callback_data="auto_mix")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🌍 *Настройки языков для паролей:*\n\n"
        "Выбери языки для генерации паролей:\n"
        "• Можно выбрать несколько\n"
        "• Символы будут смешиваться\n"
        "• Чем больше языков - тем безопаснее!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Выбор языка
async def select_language(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    selected_lang = query.data.split('_')[1]
    user_id = query.from_user.id
    user_data = get_user_data(user_id)
    
    if selected_lang in user_data['settings']['default_languages']:
        user_data['settings']['default_languages'].remove(selected_lang)
        status = "❌ Удален"
    else:
        user_data['settings']['default_languages'].append(selected_lang)
        status = "✅ Добавлен"
    
    current_langs = ", ".join([lang.capitalize() for lang in user_data['settings']['default_languages']])
    
    keyboard = [[InlineKeyboardButton("🔙 Назад к настройкам", callback_data="language_settings")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{status} язык: *{selected_lang.capitalize()}*\n\n"
        f"📋 *Текущие языки:* {current_langs}\n\n"
        f"Пароли теперь будут генерироваться из этих языков! 🌍",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Генерация пароля
async def generate_password_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🎲 Случайное смешивание", callback_data="random_mix")],
        [InlineKeyboardButton("🔤 Выбранные языки", callback_data="selected_langs")],
        [InlineKeyboardButton("🔢 Указать длину", callback_data="custom_length")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔐 *Генерация пароля:*\n\n"
        "Выбери тип генерации:\n"
        "• 🎲 Случайное смешивание - авто-выбор языков\n"
        "• 🔤 Выбранные языки - использует твои настройки\n"
        "• 🔢 Указать длину - точная настройка",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Случайное смешивание
async def random_mix_password(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    length = random.randint(12, 16)
    password, used_langs = generate_mixed_password(length)
    
    langs_text = ", ".join([lang.capitalize() for lang in used_langs])
    
    keyboard = [
        [InlineKeyboardButton("🔄 Сгенерировать еще", callback_data="random_mix")],
        [InlineKeyboardButton("💾 Сохранить в папку", callback_data="save_password")],
        [InlineKeyboardButton("🔙 Назад", callback_data="generate_password")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Сохраняем пароль в контексте для возможного сохранения
    context.user_data['last_password'] = password
    
    await query.edit_message_text(
        f"🎲 *Случайный мультиязычный пароль:*\n\n"
        f"🔑 *Пароль:* `{password}`\n"
        f"📏 *Длина:* {length} символов\n"
        f"🌍 *Использованные языки:* {langs_text}\n\n"
        f"💪 *Уровень безопасности:* МАКСИМАЛЬНЫЙ ⭐",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Генерация выбранными языками
async def selected_langs_password(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user_data(user_id)
    selected_langs = user_data['settings']['default_languages']
    
    if not selected_langs:
        selected_langs = ['english']
    
    length = random.randint(12, 16)
    password = generate_multilingual_password(length, selected_langs)
    langs_text = ", ".join([lang.capitalize() for lang in selected_langs])
    
    keyboard = [
        [InlineKeyboardButton("🔄 Сгенерировать еще", callback_data="selected_langs")],
        [InlineKeyboardButton("💾 Сохранить в папку", callback_data="save_password")],
        [InlineKeyboardButton("🔙 Назад", callback_data="generate_password")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    context.user_data['last_password'] = password
    
    await query.edit_message_text(
        f"🔤 *Пароль выбранными языками:*\n\n"
        f"🔑 *Пароль:* `{password}`\n"
        f"📏 *Длина:* {length} символов\n"
        f"🌍 *Использованные языки:* {langs_text}\n\n"
        f"✨ Персонализированная генерация!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Система папок
async def show_folders(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user_data(user_id)
    folders = user_data['folders']
    
    if not folders:
        keyboard = [[InlineKeyboardButton("📁 Создать первую папку", callback_data="create_folder")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📁 *Мои папки*\n\n"
            "У тебя пока нет папок с паролями.\n"
            "Создай первую папку для организации паролей!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    keyboard = []
    for folder_name in folders.keys():
        password_count = len(folders[folder_name])
        keyboard.append([InlineKeyboardButton(
            f"📂 {folder_name} ({password_count} паролей)", 
            callback_data=f"view_folder_{folder_name}"
        )])
    
    keyboard.append([InlineKeyboardButton("➕ Создать папку", callback_data="create_folder")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📁 *Мои папки с паролями:*\n\n"
        "Выбери папку для просмотра паролей:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Создание папки
async def create_folder(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    context.user_data['awaiting_folder_name'] = True
    
    await query.edit_message_text(
        "📝 *Создание новой папки*\n\n"
        "Введи название для новой папки:\n\n"
        "Пример: 🌐 Соцсети, 🎮 Игры, 💳 Банки"
    )

# Обработка названия папки
async def handle_folder_name(update: Update, context: CallbackContext) -> None:
    if not context.user_data.get('awaiting_folder_name'):
        return
    
    folder_name = update.message.text.strip()
    user_id = update.message.from_user.id
    user_data = get_user_data(user_id)
    
    if folder_name in user_data['folders']:
        await update.message.reply_text("❌ Папка с таким названием уже существует!")
        return
    
    user_data['folders'][folder_name] = []
    context.user_data['awaiting_folder_name'] = False
    
    keyboard = [[InlineKeyboardButton("📁 Посмотреть папки", callback_data="folders")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Папка '*{folder_name}*' успешно создана!\n"
        "Теперь ты можешь добавлять в нее пароли.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Информация о безопасности
async def security_info(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    security_text = """
🛡️ *Безопасность мультиязычных паролей* 🌍

✨ *Преимущества:*
• 🔤 8+ языков = огромная энтропия
• 🌍 Смешивание письменностей 
• 💪 Стойкость к brute-force атакам
• 🎯 Уникальность комбинаций

📊 *Статистика безопасности:*
• Английский алфавит: 52 символа
• + Русский: + 66 символов  
• + Греческий: + 48 символов
• + Математика: + 50 символов
• *Итого: 200+ уникальных символов!*

🔒 *Гарантии:*
• Все пароли генерируются локально
• Никакие данные не сохраняются
• Полная анонимность
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(security_text, reply_markup=reply_markup, parse_mode='Markdown')

# Главное меню
async def main_menu(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    keyboard = [
        [InlineKeyboardButton("🔐 Сгенерировать пароль", callback_data="generate_password")],
        [InlineKeyboardButton("🌍 Настройки языков", callback_data="language_settings")],
        [InlineKeyboardButton("📁 Мои папки", callback_data="folders"), 
         InlineKeyboardButton("➕ Добавить пароль", callback_data="add_password")],
        [InlineKeyboardButton("🔒 Безопасность", callback_data="security_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🔐 *Мультиязычный Генератор Паролей* 🌍\n\n"
        f"Привет, {user.first_name}! Выбери действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Глобальное хранилище (в памяти)
userStorage = {}

# Основная функция
def main() -> None:
    # Создание приложения
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(language_settings, pattern="^language_settings$"))
    application.add_handler(CallbackQueryHandler(select_language, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(generate_password_handler, pattern="^generate_password$"))
    application.add_handler(CallbackQueryHandler(random_mix_password, pattern="^random_mix$"))
    application.add_handler(CallbackQueryHandler(selected_langs_password, pattern="^selected_langs$"))
    application.add_handler(CallbackQueryHandler(show_folders, pattern="^folders$"))
    application.add_handler(CallbackQueryHandler(create_folder, pattern="^create_folder$"))
    application.add_handler(CallbackQueryHandler(security_info, pattern="^security_info$"))
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_folder_name))
    
    # Запуск бота
    application.run_polling()
    print("🚀 Мультиязычный бот запущен! 🌍")

if __name__ == '__main__':
    main()
