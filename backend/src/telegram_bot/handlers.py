"""
Обработчики команд и сообщений Telegram бота
"""
import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .api_client import APIClient
from .user_storage import UserStorage

logger = logging.getLogger(__name__)


class BotHandlers:
    """Класс с обработчиками команд и сообщений бота"""
    
    def __init__(self, api_client: APIClient, user_storage: UserStorage):
        self.api_client = api_client
        self.user_storage = user_storage
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        
        # Создаем клавиатуру
        keyboard = [
            [KeyboardButton("📋 Главное меню"), KeyboardButton("ℹ️ Помощь")],
        ]
        if self.user_storage.is_authenticated(user_id):
            keyboard.insert(0, [KeyboardButton("👤 Профиль"), KeyboardButton("💰 Баланс")])
        else:
            keyboard.insert(0, [KeyboardButton("🔐 Авторизоваться"), KeyboardButton("📝 Регистрация")])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        welcome_text = """
🤖 *Добро пожаловать в Formula2LaTeX Bot!*

Я помогу вам распознавать математические формулы и конвертировать их в LaTeX код.

*Возможности:*
• 🔐 Регистрация и авторизация
• 📸 Загрузка изображений с формулами
• 🔄 Распознавание формул в LaTeX
• 💰 Управление балансом кредитов
• 📊 История ваших запросов

*Как начать:*
1. Зарегистрируйтесь или авторизуйтесь
2. Загрузите изображение с формулой
3. Получите LaTeX код!

Используйте кнопки меню ниже для навигации 👇
"""
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
🆘 *Помощь по использованию бота*

*Основные команды:*
• `/start` - Запуск бота и главное меню
• `/help` - Эта справка
• `/profile` - Информация о профиле
• `/balance` - Проверка баланса
• `/history` - История задач
• `/logout` - Выход из аккаунта

*Как использовать:*
1️⃣ *Регистрация/Авторизация*
   - Нажмите "📝 Регистрация" для создания аккаунта
   - Или "🔐 Авторизоваться" для входа

2️⃣ *Распознавание формул*
   - Просто отправьте изображение с формулой
   - Выберите модель распознавания
   - Получите LaTeX код

3️⃣ *Управление балансом*
   - Проверяйте баланс кредитов
   - Просматривайте историю транзакций

4️⃣ *История*
   - Просматривайте все ваши задачи
   - Получайте детали по каждой задаче

*Поддерживаемые форматы изображений:*
📸 PNG, JPG, JPEG, GIF

*Нужна дополнительная помощь?*
Обратитесь к администратору системы.
"""
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /menu или кнопки Главное меню"""
        user_id = update.effective_user.id
        
        if self.user_storage.is_authenticated(user_id):
            keyboard = [
                [InlineKeyboardButton("📸 Распознать формулу", callback_data="recognize")],
                [InlineKeyboardButton("👤 Профиль", callback_data="profile"),
                 InlineKeyboardButton("💰 Баланс", callback_data="balance")],
                [InlineKeyboardButton("📊 История задач", callback_data="history"),
                 InlineKeyboardButton("🔧 Модели", callback_data="models")],
                [InlineKeyboardButton("🚪 Выйти", callback_data="logout")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("📝 Регистрация", callback_data="register"),
                 InlineKeyboardButton("🔐 Авторизоваться", callback_data="login")],
                [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "📋 *Главное меню*\n\nВыберите действие:" if self.user_storage.is_authenticated(user_id) else "🔐 *Для использования бота необходимо авторизоваться*"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def register_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало процесса регистрации"""
        user_id = update.effective_user.id
        
        if self.user_storage.is_authenticated(user_id):
            await update.callback_query.answer("Вы уже авторизованы!")
            return
        
        await self.user_storage.set_current_step(user_id, "register_email")
        
        await update.callback_query.edit_message_text(
            "📝 *Регистрация*\n\nВведите ваш email адрес:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def login_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало процесса авторизации"""
        user_id = update.effective_user.id
        
        if self.user_storage.is_authenticated(user_id):
            await update.callback_query.answer("Вы уже авторизованы!")
            return
        
        await self.user_storage.set_current_step(user_id, "login_email")
        
        await update.callback_query.edit_message_text(
            "🔐 *Авторизация*\n\nВведите ваш email адрес:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def profile_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик просмотра профиля"""
        user_id = update.effective_user.id
        
        if not self.user_storage.is_authenticated(user_id):
            await update.callback_query.answer("Необходимо авторизоваться!")
            return
        
        token = self.user_storage.get_jwt_token(user_id)
        user_info = await self.api_client.get_user_info(token)
        
        if user_info:
            text = f"""
👤 *Профиль пользователя*

📧 Email: `{user_info.email}`
🆔 ID: `{user_info.id}`
✅ Статус: Авторизован
"""
        else:
            text = "❌ Ошибка получения информации о профиле"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def balance_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик просмотра баланса"""
        user_id = update.effective_user.id
        
        if not self.user_storage.is_authenticated(user_id):
            await update.callback_query.answer("Необходимо авторизоваться!")
            return
        
        token = self.user_storage.get_jwt_token(user_id)
        wallet = await self.api_client.get_wallet(token)
        
        if wallet:
            text = f"""
💰 *Баланс кошелька*

💳 Текущий баланс: `{wallet.balance}` кредитов
🆔 ID кошелька: `{wallet.id}`

💡 *Информация:*
• Каждое распознавание формулы тратит кредиты
• Стоимость зависит от выбранной модели
• Для пополнения баланса обратитесь к администратору
"""
        else:
            text = "❌ Ошибка получения информации о балансе"
        
        keyboard = [
            [InlineKeyboardButton("📊 История транзакций", callback_data="transactions")],
            [InlineKeyboardButton("🔙 Назад", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def logout_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выхода из системы"""
        user_id = update.effective_user.id
        
        await self.user_storage.logout_user(user_id)
        
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "🚪 *Вы успешно вышли из системы*\n\nДля продолжения работы необходимо авторизоваться заново.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def text_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        current_step = self.user_storage.get_current_step(user_id)
        
        # Обработка кнопок клавиатуры
        if text == "📋 Главное меню":
            await self.menu_command(update, context)
            return
        elif text == "ℹ️ Помощь":
            await self.help_command(update, context)
            return
        elif text == "🔐 Авторизоваться":
            # Имитируем callback_query для совместимости
            class FakeCallbackQuery:
                def __init__(self, update):
                    self.message = update.message
                    self.edit_message_text = self.message.reply_text
                    self.answer = lambda x: None
                
            update.callback_query = FakeCallbackQuery(update)
            await self.login_start(update, context)
            return
        elif text == "📝 Регистрация":
            class FakeCallbackQuery:
                def __init__(self, update):
                    self.message = update.message
                    self.edit_message_text = self.message.reply_text
                    self.answer = lambda x: None
                
            update.callback_query = FakeCallbackQuery(update)
            await self.register_start(update, context)
            return
        elif text == "👤 Профиль":
            if not self.user_storage.is_authenticated(user_id):
                await update.message.reply_text("🔐 Необходимо авторизоваться!")
                return
            
            token = self.user_storage.get_jwt_token(user_id)
            user_info = await self.api_client.get_user_info(token)
            
            if user_info:
                text_msg = f"""
👤 *Профиль пользователя*

📧 Email: `{user_info.email}`
🆔 ID: `{user_info.id}`
✅ Статус: Авторизован
"""
            else:
                text_msg = "❌ Ошибка получения информации о профиле"
            
            await update.message.reply_text(text_msg, parse_mode=ParseMode.MARKDOWN)
            return
        elif text == "💰 Баланс":
            if not self.user_storage.is_authenticated(user_id):
                await update.message.reply_text("🔐 Необходимо авторизоваться!")
                return
            
            token = self.user_storage.get_jwt_token(user_id)
            wallet = await self.api_client.get_wallet(token)
            
            if wallet:
                text_msg = f"""
💰 *Баланс кошелька*

💳 Текущий баланс: `{wallet.balance}` кредитов
🆔 ID кошелька: `{wallet.id}`

💡 *Для пополнения баланса обратитесь к администратору*
"""
            else:
                text_msg = "❌ Ошибка получения информации о балансе"
            
            await update.message.reply_text(text_msg, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Обработка multi-step процессов
        if current_step == "register_email":
            await self._handle_register_email(update, context, text)
        elif current_step == "register_password":
            await self._handle_register_password(update, context, text)
        elif current_step == "login_email":
            await self._handle_login_email(update, context, text)
        elif current_step == "login_password":
            await self._handle_login_password(update, context, text)
        else:
            # Неизвестное сообщение
            await update.message.reply_text(
                "🤔 Не понимаю команду. Используйте кнопки меню или /help для справки."
            )
    
    async def _handle_register_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE, email: str):
        """Обработка ввода email при регистрации"""
        user_id = update.effective_user.id
        
        # Простая валидация email
        if "@" not in email or "." not in email:
            await update.message.reply_text("❌ Неверный формат email. Попробуйте еще раз:")
            return
        
        await self.user_storage.set_temp_data(user_id, {"email": email})
        await self.user_storage.set_current_step(user_id, "register_password")
        
        await update.message.reply_text("📝 Теперь введите пароль (минимум 6 символов):")
    
    async def _handle_register_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE, password: str):
        """Обработка ввода пароля при регистрации"""
        user_id = update.effective_user.id
        
        if len(password) < 6:
            await update.message.reply_text("❌ Пароль должен содержать минимум 6 символов. Попробуйте еще раз:")
            return
        
        temp_data = self.user_storage.get_temp_data(user_id)
        email = temp_data["email"]
        
        # Попытка регистрации
        user = await self.api_client.register(email, password)
        
        if user:
            await update.message.reply_text(
                f"✅ *Регистрация успешна!*\n\nВаш аккаунт создан: `{email}`\n\nТеперь войдите в систему.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Ошибка регистрации. Возможно, email уже используется.")
        
        await self.user_storage.set_current_step(user_id, None)
        await self.user_storage.clear_temp_data(user_id)
    
    async def _handle_login_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE, email: str):
        """Обработка ввода email при авторизации"""
        user_id = update.effective_user.id
        
        if "@" not in email or "." not in email:
            await update.message.reply_text("❌ Неверный формат email. Попробуйте еще раз:")
            return
        
        await self.user_storage.set_temp_data(user_id, {"email": email})
        await self.user_storage.set_current_step(user_id, "login_password")
        
        await update.message.reply_text("🔐 Введите пароль:")
    
    async def _handle_login_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE, password: str):
        """Обработка ввода пароля при авторизации"""
        user_id = update.effective_user.id
        
        temp_data = self.user_storage.get_temp_data(user_id)
        email = temp_data["email"]
        
        # Попытка авторизации
        token = await self.api_client.login(email, password)
        
        if token:
            await self.user_storage.authenticate_user(user_id, email, token)
            
            await update.message.reply_text(
                f"✅ *Авторизация успешна!*\n\nДобро пожаловать, `{email}`!\n\nТеперь вы можете использовать все функции бота.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Неверный email или пароль. Попробуйте еще раз.")
        
        await self.user_storage.set_current_step(user_id, None)
        await self.user_storage.clear_temp_data(user_id)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на inline кнопки"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "menu":
            await self.menu_command(update, context)
        elif data == "register":
            await self.register_start(update, context)
        elif data == "login":
            await self.login_start(update, context)
        elif data == "profile":
            await self.profile_handler(update, context)
        elif data == "balance":
            await self.balance_handler(update, context)
        elif data == "logout":
            await self.logout_handler(update, context)
        elif data == "help":
            await self.help_command(update, context)
        elif data == "recognize":
            await self._start_recognition(update, context)
        elif data == "history":
            await self._show_history(update, context)
        elif data == "models":
            await self._show_models(update, context)
        elif data == "transactions":
            await self._show_transactions(update, context)
        elif data.startswith("model_"):
            await self._select_model(update, context, data.split("_")[1])
    
    async def _start_recognition(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало процесса распознавания"""
        user_id = update.effective_user.id
        
        if not self.user_storage.is_authenticated(user_id):
            await update.callback_query.answer("Необходимо авторизоваться!")
            return
        
        await update.callback_query.edit_message_text(
            "📸 *Распознавание формулы*\n\nОтправьте изображение с математической формулой, и я распознаю её в LaTeX код!",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показ истории задач"""
        user_id = update.effective_user.id
        
        if not self.user_storage.is_authenticated(user_id):
            await update.callback_query.answer("Необходимо авторизоваться!")
            return
        
        token = self.user_storage.get_jwt_token(user_id)
        tasks = await self.api_client.get_tasks(token)
        
        if not tasks:
            text = "📊 *История задач*\n\n📭 У вас пока нет выполненных задач."
        else:
            text = "📊 *История задач*\n\n"
            for i, task in enumerate(tasks[:5], 1):  # Показываем только последние 5
                status_emoji = "✅" if task.status == "done" else "❌"
                text += f"{i}. {status_emoji} {task.created_at[:19]} - {task.credits_charged} кредитов\n"
            
            if len(tasks) > 5:
                text += f"\n... и еще {len(tasks) - 5} задач"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_models(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показ доступных моделей"""
        models = await self.api_client.get_models()
        
        if not models:
            text = "🔧 *Модели ML*\n\n❌ Нет доступных моделей."
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="menu")]]
        else:
            text = "🔧 *Доступные модели ML*\n\n"
            keyboard = []
            for model in models:
                text += f"• {model.name} - {model.credit_cost} кредитов\n"
                keyboard.append([InlineKeyboardButton(
                    f"{model.name} ({model.credit_cost} кред.)",
                    callback_data=f"model_{model.id}"
                )])
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_transactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показ истории транзакций"""
        user_id = update.effective_user.id
        
        token = self.user_storage.get_jwt_token(user_id)
        transactions = await self.api_client.get_transactions(token)
        
        if not transactions:
            text = "📊 *История транзакций*\n\n📭 У вас пока нет транзакций."
        else:
            text = "📊 *История транзакций*\n\n"
            for i, txn in enumerate(transactions[:5], 1):
                type_emoji = "➕" if txn.type == "top_up" else "➖"
                text += f"{i}. {type_emoji} {txn.amount} → {txn.post_balance}\n   {txn.created_at[:19]}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="balance")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _select_model(self, update: Update, context: ContextTypes.DEFAULT_TYPE, model_id: str):
        """Выбор модели для распознавания"""
        user_id = update.effective_user.id
        
        await self.user_storage.set_temp_data(user_id, {"selected_model_id": model_id})
        
        await update.callback_query.edit_message_text(
            "✅ *Модель выбрана!*\n\nТеперь отправьте изображение с математической формулой для распознавания.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def photo_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик загрузки фотографий"""
        user_id = update.effective_user.id
        
        if not self.user_storage.is_authenticated(user_id):
            await update.message.reply_text("🔐 Необходимо авторизоваться для распознавания формул!")
            return
        
        # Получаем информацию о модели
        temp_data = self.user_storage.get_temp_data(user_id)
        if not temp_data or "selected_model_id" not in temp_data:
            # Предлагаем выбрать модель
            models = await self.api_client.get_models()
            if models:
                keyboard = []
                for model in models:
                    keyboard.append([InlineKeyboardButton(
                        f"{model.name} ({model.credit_cost} кред.)",
                        callback_data=f"model_{model.id}"
                    )])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "🔧 *Выберите модель для распознавания:*",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            else:
                await update.message.reply_text("❌ Нет доступных моделей для распознавания.")
                return
        
        model_id = temp_data["selected_model_id"]
        
        # Получаем файл
        photo = update.message.photo[-1]  # Берем фото в максимальном разрешении
        file = await context.bot.get_file(photo.file_id)
        
        # Скачиваем файл
        file_content = await file.download_as_bytearray()
        filename = f"formula_{photo.file_id}.jpg"
        
        # Отправляем сообщение о начале обработки
        processing_msg = await update.message.reply_text("🔄 Обрабатываю изображение...")
        
        try:
            # Отправляем на распознавание
            token = self.user_storage.get_jwt_token(user_id)
            task = await self.api_client.predict(token, model_id, bytes(file_content), filename)
            
            if task:
                if task.status == "done" and task.output_data:
                    result_text = f"""
✅ *Распознавание завершено!*

📸 Загруженное изображение обработано
💰 Списано кредитов: `{task.credits_charged}`

🔤 *LaTeX код:*
```latex
{task.output_data}
```

🆔 ID задачи: `{task.id}`
"""
                else:
                    result_text = f"""
❌ *Ошибка распознавания*

💰 Списано кредитов: `{task.credits_charged}`
📝 Ошибка: {task.error_message or "Неизвестная ошибка"}

🆔 ID задачи: `{task.id}`
"""
            else:
                result_text = "❌ Ошибка при обработке изображения. Возможно, недостаточно кредитов или проблема с API."
            
            await processing_msg.edit_text(result_text, parse_mode=ParseMode.MARKDOWN)
            
            # Очищаем временные данные
            await self.user_storage.clear_temp_data(user_id)
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            await processing_msg.edit_text("❌ Произошла ошибка при обработке изображения.")
    
    async def document_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик загрузки документов (изображений)"""
        user_id = update.effective_user.id
        
        if not self.user_storage.is_authenticated(user_id):
            await update.message.reply_text("🔐 Необходимо авторизоваться для распознавания формул!")
            return
        
        document = update.message.document
        
        # Проверяем, что это изображение
        if not document.mime_type or not document.mime_type.startswith('image/'):
            await update.message.reply_text("❌ Поддерживаются только изображения (PNG, JPG, JPEG, GIF).")
            return
        
        # Проверяем размер файла (максимум 20MB)
        if document.file_size > 20 * 1024 * 1024:
            await update.message.reply_text("❌ Размер файла слишком большой. Максимум 20MB.")
            return
        
        # Аналогично обработке фото
        temp_data = self.user_storage.get_temp_data(user_id)
        if not temp_data or "selected_model_id" not in temp_data:
            # Предлагаем выбрать модель
            models = await self.api_client.get_models()
            if models:
                keyboard = []
                for model in models:
                    keyboard.append([InlineKeyboardButton(
                        f"{model.name} ({model.credit_cost} кред.)",
                        callback_data=f"model_{model.id}"
                    )])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "🔧 *Выберите модель для распознавания:*",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                return
        
        model_id = temp_data["selected_model_id"]
        
        # Получаем файл
        file = await context.bot.get_file(document.file_id)
        file_content = await file.download_as_bytearray()
        
        # Отправляем сообщение о начале обработки
        processing_msg = await update.message.reply_text("🔄 Обрабатываю изображение...")
        
        try:
            # Отправляем на распознавание
            token = self.user_storage.get_jwt_token(user_id)
            task = await self.api_client.predict(token, model_id, bytes(file_content), document.file_name)
            
            if task:
                if task.status == "done" and task.output_data:
                    result_text = f"""
✅ *Распознавание завершено!*

📁 Файл: `{document.file_name}`
💰 Списано кредитов: `{task.credits_charged}`

🔤 *LaTeX код:*
```latex
{task.output_data}
```

🆔 ID задачи: `{task.id}`
"""
                else:
                    result_text = f"""
❌ *Ошибка распознавания*

💰 Списано кредитов: `{task.credits_charged}`
📝 Ошибка: {task.error_message or "Неизвестная ошибка"}

🆔 ID задачи: `{task.id}`
"""
            else:
                result_text = "❌ Ошибка при обработке изображения. Возможно, недостаточно кредитов или проблема с API."
            
            await processing_msg.edit_text(result_text, parse_mode=ParseMode.MARKDOWN)
            
            # Очищаем временные данные
            await self.user_storage.clear_temp_data(user_id)
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            await processing_msg.edit_text("❌ Произошла ошибка при обработке изображения.")