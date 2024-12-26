import logging
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sys
import signal
import os
from dotenv import load_dotenv
from cloud_assistant import CloudAssistant
from cloud_pricing import CloudPricing
from yc_client import YandexCloudClient
import asyncio
import atexit
import psutil
import os.path

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настраиваем логирование в файл и консоль
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_debug.log', encoding='utf-8', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Инициализация клиента Yandex Cloud
yc_client = YandexCloudClient()

# Конфигурация YandexGPT API
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# Инициализация облачного ассистента и калькулятора цен
cloud_assistant = CloudAssistant(YANDEX_API_KEY, YANDEX_FOLDER_ID)
pricing = CloudPricing()

async def get_yandex_response(prompt: str) -> str:
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "modelUri": "gpt://b1girnbllj1ftb09con0/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 2000
        },
        "messages": [
            {
                "role": "user",
                "text": prompt
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["result"]["alternatives"][0]["message"]["text"]

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение"""
    welcome_message = (
        "👋 Привет! Я ваш ассистент по Yandex Cloud.\n\n"
        "🔹 Я помогу вам:\n"
        "- Выбрать подходящие сервисы\n"
        "- Рассчитать стоимость услуг\n"
        "- Получить примеры кода и конфигураций\n"
        "- Ответить на вопросы по документации\n\n"
        "Используйте /help для просмотра доступных команд."
    )
    await update.message.reply_text(welcome_message)

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет список доступных команд"""
    help_text = (
        "🔷 Доступные команды:\n\n"
        "📊 Основные команды:\n"
        "/services - Обзор сервисов Yandex Cloud\n"
        "/calculate_vm - Расчет стоимости виртуальной машины\n"
        "/pricing - Информация о ценах\n"
        "/databases - Список доступных баз данных\n\n"
        "🛠 Дополнительные возможности:\n"
        "/examples - Примеры кода и конфигураций\n"
        "/optimize - Рекомендации по оптимизации\n"
        "/diagnose - Диагностика проблем\n"
        "/premium - Информация о премиум возможностях\n\n"
        "💬 Просто напишите свой вопрос, и я постараюсь помочь!"
    )
    await update.message.reply_text(help_text)

# Обработчик команды расчета стоимости VM
async def calculate_vm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды расчета стоимости VM"""
    try:
        # Получаем параметры из сообщения
        args = context.args
        if len(args) != 3:
            await update.message.reply_text(
                "❌ Пожалуйста, укажите параметры в формате:\n"
                "/calculate_vm [cpu] [ram] [disk]\n"
                "Например: /calculate_vm 2 4 100"
            )
            return

        cpu = int(args[0])
        ram = int(args[1])
        disk = int(args[2])

        # Рассчитываем стоимость
        calculation = pricing.calculate_vm_cost(cpu, ram, disk)
        
        # Форматируем ответ
        message = pricing.format_price_message(calculation)
        
        await update.message.reply_text(message)

    except ValueError:
        await update.message.reply_text(
            "❌ Ошибка в параметрах. Используйте целые числа.\n"
            "Например: /calculate_vm 2 4 100"
        )
    except Exception as e:
        logger.error(f"Ошибка при расчете стоимости VM: {str(e)}")
        await update.message.reply_text("Извините, произошла ошибка при расчете.")

# Обработчик команды получения информации о ценах
async def get_pricing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды получения информации о ценах"""
    try:
        args = context.args
        if not args:
            message = """
            🏷️ Доступная информация о ценах:

            Используйте команды:
            • /pricing compute - цены на виртуальные машины
            • /pricing storage - цены на хранилище
            • /pricing database - цены на базы данных

            Для расчета стоимости VM используйте:
            /calculate_vm [cpu] [ram] [disk]
            """
        else:
            service = args[0].lower()
            message = pricing.get_pricing_info(service)
            
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка при получении информации о ценах: {str(e)}")
        await update.message.reply_text("Извините, произошла ошибка при получении информации о ценах.")

# Обработчик команды получения рекомендаций по сервисам
async def recommend_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды получения рекомендаций по сервисам"""
    help_text = """
    🎯 Для получения рекомендаций, опишите ваши требования:

    • Тип проекта (веб-приложение, база данных, etc.)
    • Ожидаемая нагрузка
    • Требования к данным
    • Бюджет

    Например:
    "Нужен сервис для веб-приложения с трафиком 1000 пользователей в день"
    """
    await update.message.reply_text(help_text)

# Обработчик команды получения списка баз данных
async def list_databases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает и отображает список баз данных в Yandex Cloud"""
    try:
        databases = yc_client.list_databases()
        if not databases.databases:
            await update.message.reply_text("Базы данных не найдены в вашем каталоге.")
            return

        response = "Список баз данных в Yandex Cloud:\n\n"
        for db in databases.databases:
            response += f"📁 ID: {db.id}\n"
            response += f"📌 Имя: {db.name}\n"
            response += f"📍 Статус: {db.status}\n"
            response += f"🔧 Тип: {db.type}\n"
            response += "-------------------\n"

        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Ошибка при получении списка баз данных: {str(e)}")
        await update.message.reply_text("Произошла ошибка при получении списка баз данных. Проверьте логи для деталей.")

# Обработчик команды получения примеров кода
async def get_examples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Предоставляет примеры кода для различных сервисов"""
    examples_text = (
        "🔍 Выберите категорию примеров:\n\n"
        "1. Compute Cloud (VM)\n"
        "2. Object Storage\n"
        "3. Managed Databases\n"
        "4. Serverless Functions\n"
        "5. API Gateway\n\n"
        "Отправьте номер категории или опишите ваш сценарий использования."
    )
    await update.message.reply_text(examples_text)

# Обработчик команды оптимизации
async def optimize_resources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Предоставляет рекомендации по оптимизации ресурсов"""
    optimize_text = (
        "🔧 Рекомендации по оптимизации:\n\n"
        "1. Анализ использования ресурсов\n"
        "2. Оптимизация затрат\n"
        "3. Производительность\n"
        "4. Безопасность\n\n"
        "Опишите, какой аспект вас интересует."
    )
    await update.message.reply_text(optimize_text)

# Обработчик команды диагностики
async def diagnose_issues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помогает диагностировать проблемы"""
    diagnose_text = (
        "🔍 Диагностика проблем:\n\n"
        "Опишите проблему, с которой вы столкнулись:\n"
        "- Проблемы с подключением\n"
        "- Ошибки развертывания\n"
        "- Проблемы с производительностью\n"
        "- Ошибки в логах\n\n"
        "Я помогу определить причину и предложу решение."
    )
    await update.message.reply_text(diagnose_text)

# Обработчик команды премиум возможностей
async def premium_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о премиум возможностях"""
    premium_text = (
        "⭐️ Премиум возможности:\n\n"
        "1. Приоритетная поддержка 24/7\n"
        "2. Консультации с экспертами\n"
        "3. Готовые решения и шаблоны\n"
        "4. Расширенная диагностика\n"
        "5. Персональные рекомендации\n\n"
        "Для получения доступа обратитесь к администратору."
    )
    await update.message.reply_text(premium_text)

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    message_text = update.message.text.lower()
    
    # Проверяем, спрашивает ли пользователь о командах
    if "команд" in message_text:
        await help_command(update, context)
        return
    
    try:
        # Проверяем, является ли сообщение запросом о конкретном сервисе
        if "сервис" in message_text or "service" in message_text:
            service_name = message_text.replace("сервис", "").replace("service", "").strip()
            service_info = cloud_assistant.get_service_info(service_name)
            response = f"""
            📦 {service_info['name']}
            
            📝 Описание: {service_info['description']}
            
            ✨ Возможности:
            {chr(10).join(['• ' + f for f in service_info.get('features', [])])}
            
            🎯 Примеры использования:
            {chr(10).join(['• ' + u for u in service_info.get('use_cases', [])])}
            """
        else:
            # Используем YandexGPT для остальных запросов
            response = await get_yandex_response(message_text)
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        await update.message.reply_text("Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже.")

def is_bot_running():
    """Проверяет, запущен ли уже экземпляр бота"""
    pid_file = "bot.pid"
    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            old_pid = int(f.read().strip())
            if psutil.pid_exists(old_pid):
                try:
                    process = psutil.Process(old_pid)
                    if "python" in process.name().lower():
                        return True
                except psutil.NoSuchProcess:
                    pass
    return False

def save_pid():
    """Сохраняет PID текущего процесса"""
    with open("bot.pid", "w") as f:
        f.write(str(os.getpid()))

def cleanup():
    """Очищает PID файл при завершении"""
    try:
        os.remove("bot.pid")
    except:
        pass

def run_bot():
    """Запускает бота в отдельном процессе"""
    if is_bot_running():
        logger.error("Бот уже запущен")
        return

    save_pid()
    atexit.register(cleanup)

    # Получаем токен из переменных окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("calculate_vm", calculate_vm))
    application.add_handler(CommandHandler("pricing", get_pricing))
    application.add_handler(CommandHandler("services", recommend_services))
    application.add_handler(CommandHandler("databases", list_databases))
    application.add_handler(CommandHandler("examples", get_examples))
    application.add_handler(CommandHandler("optimize", optimize_resources))
    application.add_handler(CommandHandler("diagnose", diagnose_issues))
    application.add_handler(CommandHandler("premium", premium_features))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    def signal_handler(signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logger.info("Получен сигнал завершения, останавливаем бота...")
        asyncio.create_task(application.stop())
        cleanup()
        sys.exit(0)

    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        cleanup()
        sys.exit(1)

if __name__ == '__main__':
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
    finally:
        cleanup()
