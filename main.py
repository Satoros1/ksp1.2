import os
import ssl
import requests
from telebot.async_telebot import AsyncTeleBot
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

# Настройка прокси
proxy = "89.213.255.244:46990"
proxy_auth = "28VM8Q1D:1BPQ1ALQ"

# Устанавливаем прокси для HTTP/HTTPS
os.environ['HTTP_PROXY'] = f'http://{proxy}'
os.environ['HTTPS_PROXY'] = f'https://{proxy}'

# Отключаем проверку hostname для SSL-соединений
ssl._create_default_https_context = ssl._create_unverified_context

# Запросы через прокси для теста (необходимо для загрузки нужных данных)
def test_proxy_connection():
    proxies = {
        'http': f'http://{proxy}',
        'https': f'https://{proxy}'
    }
    try:
        response = requests.get('https://www.google.com', proxies=proxies, timeout=5, verify=False)  # Отключаем проверку SSL
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Proxy connection test failed: {e}")
        return False

# Проверка подключения через прокси
if not test_proxy_connection():
    print("Proxy setup failed. Check your proxy settings.")
    exit()

def pars():
    """
    Функция для парсинга данных с сайта.
    """
    data = []

    # Установка ChromeDriver через webdriver-manager
    chrome_driver_path = ChromeDriverManager().install()  # Он будет скачан через прокси, если прокси настроен

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Отключаем отображение браузера
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    # Настроим прокси для WebDriver
    chrome_options.add_argument(f'--proxy-server=http://{proxy}')
    
    # Если прокси требует авторизации
    chrome_options.add_argument(f'--proxy-auth={proxy_auth}')

    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)

    try:
        driver.get('https://kas.fyi/krc20-tokens?view=trending')
        time.sleep(5)  # Ждем загрузки страницы

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
