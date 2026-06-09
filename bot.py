import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
import handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():
    """Главная функция запуска бота"""
    logger.info("🟢 Запуск бота...")
    
    # Инициализируем базу данных
    init_db()
    logger.info("🟢 База данных инициализирована")
    
    # Подключаем обработчики
    dp.include_router(handlers.router)
    logger.info("🟢 Обработчики подключены")
    
    # Проверяем подключение к Telegram
    try:
        me = await bot.get_me()
        logger.info(f"✅ Бот успешно запущен: @{me.username}")
        logger.info(f"✅ ID бота: {me.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        logger.error("❌ Проверь интернет и токен")
        return
    
    # Запускаем поллинг
    logger.info("🟢 Запускаем поллинг...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)