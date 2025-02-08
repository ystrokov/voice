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

# Настройки
MEETING_URL = "https://meet.wb.ru/platformPlanning"
USERNAME = "AutoBot"
RECORD_DURATION = 25  # Время записи в секундах (30 минут)

# Путь для сохранения аудио
OUTPUT_DIR = "voice"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "meeting_audio.mp3")

# Проверка наличия директории для сохранения
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Пути к Chromedriver и FFmpeg
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
FFMPEG_PATH = "/usr/bin/ffmpeg"  # Путь к ffmpeg

# Проверка наличия FFmpeg
if not os.path.isfile(FFMPEG_PATH):
    raise FileNotFoundError(f"❌ FFmpeg не найден по пути: {FFMPEG_PATH}")

# Настройка опций для Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")  # Запуск браузера в фоновом режиме без графического интерфейса
chrome_options.add_argument("--no-sandbox")  # Отключение песочницы для повышения совместимости
chrome_options.add_argument("--disable-dev-shm-usage")  # Использование диска вместо /dev/shm для предотвращения ошибок в ограниченной среде
chrome_options.add_argument("--disable-gpu")  # Отключение использования GPU для рендеринга
chrome_options.add_argument("--window-size=1920,1080")  # Установка размера окна браузера
chrome_options.add_argument("--use-fake-ui-for-media-stream")  # Автоматическое разрешение доступа к микрофону и камере
chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")  # Разрешение автоматического воспроизведения медиа без взаимодействия пользователя
chrome_options.add_argument("--alsa-output-device=hw:0,0")  # Указание устройства вывода звука на ALSA (для захвата аудио)

# Устройство для записи аудио
AUDIO_DEVICE_NAME = 'hw:0,0'  # Использование устройства hw:0,0

# Функция для начала записи аудио
def start_audio_recording():
    print(f"🎙️ Инициализация записи аудио... Файл будет сохранён в {OUTPUT_FILE}")
    try:
        process = subprocess.Popen([
            FFMPEG_PATH, '-f', 'alsa', '-i', AUDIO_DEVICE_NAME, '-t', str(RECORD_DURATION),
            OUTPUT_FILE
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except FileNotFoundError:
        print("❌ FFmpeg не найден. Проверьте путь к файлу.")
        return None
    except Exception as e:
        print(f"❌ Ошибка при запуске записи: {e}")
        return None

# Функция для остановки записи аудио
def stop_audio_recording(process):
    print("🛑 Остановка записи аудио...")
    if process and process.poll() is None:
        try:
            process.terminate()
            stdout, stderr = process.communicate()
            print(f"🔍 Лог FFmpeg STDOUT:\n{stdout.decode()}")
            print(f"🔍 Лог FFmpeg STDERR:\n{stderr.decode()}")
            if os.path.exists(OUTPUT_FILE):
                print(f"✅ Файл успешно сохранён: {OUTPUT_FILE}")
            else:
                print(f"❌ Файл не был сохранён: {OUTPUT_FILE}")
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
        recording_process = start_audio_recording()
        if recording_process:
            time.sleep(RECORD_DURATION)
            stop_audio_recording(recording_process)
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
