from telebot.async_telebot import AsyncTeleBot
from telebot import types
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import asyncio
import time
import re

# Токен вашего бота
BOT_TOKEN = "8108601042:AAGT-oTHp7HvZ1Lk6-UaINeqOEwrTshNL08"

bot = AsyncTeleBot(BOT_TOKEN)


def pars():
    """
    Функция для парсинга данных с сайта.
    """
    data = []
    chrome_service = Service(ChromeDriverManager().install())
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Отключаем отображение браузера
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # Указываем путь к бинарному файлу Chrome вручную
    chrome_options.binary_location = "/usr/bin/google-chrome"  # Путь может отличаться в зависимости от вашей установки

    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    
    try:
        driver.get('https://kas.fyi/krc20-tokens?view=trending')
        time.sleep(5)  # Ждём загрузки страницы

        elements = driver.find_elements(By.CSS_SELECTOR, '.flex-grow-1')

        for element in elements:
            data.append(element.text)

    except Exception as e:
        print(f"Error while parsing: {e}")
    finally:
        driver.quit()

    clear_data = []
    for entry in data:
        entry = entry.replace("\n", " ").strip()
        if "Mints" in entry:
            match = re.match(r"^(.*?)(\d{1,3}(?: \d{3})*)\s*Mints$", entry)
            if match:
                name = match.group(1).strip()
                quantity = match.group(2).strip()
                clear_data.append([name, f"{quantity} Mints"])

    return clear_data


@bot.message_handler(commands=['start'])
async def menu(message):
    """
    Команда /start для запуска бота и бесконечного цикла проверки токенов.
    """
    await bot.send_message(message.chat.id, 'The bot is running. Version 1.1')
    previous_mints = {}  # Хранение данных о токенах

    while True:
        try:
            data = pars()
            result = []

            for entry in data:
                name = entry[0]
                mints_str = entry[1].replace(' ', '').replace('Mints', '')
                mints_int = int(mints_str)

                # Если токен новый
                if name not in previous_mints:
                    if mints_int > 10000:  # Новый токен с количеством больше 4000
                        result.append(f"🔥New KRC-20 - {name} {mints_int} mints!")
                    previous_mints[name] = mints_int
                else:
                    # Если токен уже существует и увеличился на 10,000
                    if mints_int >= previous_mints[name] + 10000:
                        result.append(f"🔥Hot KRC-20 - {name} {mints_int} mints in the last 15 minutes")
                    previous_mints[name] = mints_int  # Обновляем значение

            # Отправляем все сообщения
            for message_text in result:
                await bot.send_message(message.chat.id, message_text)

        except Exception as e:
            print(f"Error in main loop: {e}")

        await asyncio.sleep(100)  # Пауза перед следующим циклом


if __name__ == "__main__":
    try:
        asyncio.run(bot.polling(non_stop=True, interval=1, timeout=0))
    except KeyboardInterrupt:
        print("Bot stopped manually.")
