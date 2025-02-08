from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import time
import signal
import os
from datetime import datetime

# Настройки
MEETING_URL = "https://meet.wb.ru/platformPlanning"
USERNAME = "AutoBot"
RECORD_DURATION = 20 # Время записи в секундах (30 минут)

# Путь для сохранения аудио
OUTPUT_DIR = "/home/ubuntu/audio_recoder/voice"

# Проверка наличия директории для сохранения
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Пути к Chrome, Chromedriver и FFmpeg
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
FFMPEG_PATH = "/usr/bin/ffmpeg"  # Путь к ffmpeg

# Проверка наличия FFmpeg
if not os.path.isfile(FFMPEG_PATH):
    raise FileNotFoundError(f"❌ FFmpeg не найден по пути: {FFMPEG_PATH}")

# Настройка опций для Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")

# Устройство для записи аудио
AUDIO_DEVICE_NAME = 'hw:0,1'  # Изменено на другое устройство

# Функция для начала записи аудио
def start_audio_recording():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"meeting_audio_{timestamp}.mp3")
    print(f"🎙️ Инициализация записи аудио... Файл будет сохранён в {output_file}")
    try:
        process = subprocess.Popen([
            FFMPEG_PATH, '-f', 'alsa', '-i', AUDIO_DEVICE_NAME, '-t', str(RECORD_DURATION),
            '-af', 'volumedetect', output_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process, output_file
    except FileNotFoundError:
        print("❌ FFmpeg не найден. Проверьте путь к файлу.")
        return None, None
    except Exception as e:
        print(f"❌ Ошибка при запуске записи: {e}")
        return None, None

# Функция для остановки записи аудио
def stop_audio_recording(process):
    print("🛑 Остановка записи аудио...")
    if process and process.poll() is None:
        try:
            process.terminate()
            stdout, stderr = process.communicate()
            print(f"🔍 Лог FFmpeg STDOUT:\n{stdout.decode()}")
            print(f"🔍 Лог FFmpeg STDERR:\n{stderr.decode()}")
            process.wait(timeout=5)
            print("✅ Запись успешно завершена.")
        except Exception as e:
            print(f"❌ Ошибка при остановке записи: {e}")
    else:
        print("⚠️ Процесс записи уже завершён.")

# Основная функция
def join_and_record(meeting_url, username):
    driver = None
    try:
        print(f"🚀 Подключение к встрече: {meeting_url}")
        service = Service(executable_path=CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(meeting_url)

        wait = WebDriverWait(driver, 30)

        # Ввод имени
        print("🔍 Ожидание поля для ввода имени...")
        name_input = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='premeeting-name-input']")))
        name_input.send_keys(username)
        print("✅ Имя введено.")

        # Нажатие кнопки "Принять"
        print("🔍 Ожидание кнопки 'Принять'...")
        consent_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="videoconference_page"]/div[4]/div[1]/div/div/div[1]/div[2]/div/div')))
        consent_button.click()
        print("✅ Правила приняты.")

        # Ожидание подключения к встрече
        print("⏳ Ожидание подключения к встрече...")
        time.sleep(10)  # Время на подключение к конференции

        # Начало записи
        recording_process, output_file = start_audio_recording()
        if recording_process:
            time.sleep(RECORD_DURATION)
            stop_audio_recording(recording_process)
            print(f"✅ Запись завершена. Файл сохранён как {output_file}")
        else:
            print("⚠️ Запись не была начата из-за ошибки.")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        if driver:
            driver.quit()
            print("🚪 Браузер закрыт.")

# Запуск
if __name__ == "__main__":
    join_and_record(MEETING_URL, USERNAME)
