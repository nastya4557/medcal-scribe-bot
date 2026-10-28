import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

TELEGRAM_TOKEN = "8960972074:AAG-q3VRgP94-GiNVz-iD_vEVOU4w-u3El0"
DIFY_API_KEY = "app-coVP0lmtD5O1tMEbj1yrfpAq"
DIFY_URL = "https://api.dify.ai/v1/chat-messages"

# 1. Веб-сервер для поддержания жизни на Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")
    
    def log_message(self, format, *args):
        pass

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    print(f"Веб-сервер успешно запущен на порту {port}", flush=True)
    server.serve_forever()

# 2. Логика Telegram-бота и Dify
def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}", flush=True)

def send_to_dify(query, user_id):
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {},
        "query": query,
        "response_mode": "blocking",
        "user": str(user_id)
    }
    try:
        print(f"Отправка запроса в Dify (ожидание до 60 сек)...", flush=True)
        # Увеличили тайм-аут до 60 секунд для надежной генерации длинных текстов
        response = requests.post(DIFY_URL, json=payload, headers=headers, timeout=60)
        print(f"Ответ Dify статус: {response.status_code}", flush=True)
        if response.status_code == 200:
            data = response.json()
            return data.get("answer", "Ошибка: пустой ответ от Dify.")
        else:
            return f"Ошибка API Dify: {response.status_code}"
    except Exception as e:
        print(f"Ошибка при запросе к Dify: {e}", flush=True)
        return "⚠️ Превышено время ожидания ответа от ИИ. Попробуйте отправить текст еще раз."

def telegram_bot_loop():
    offset = 0
    print(">>> TELEGRAM БОТ УСПЕШНО ЗАПУЩЕН В ФОНЕ <<<", flush=True)
    time.sleep(2)
    while True:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=10"
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                updates = response.json().get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        user_id = update["message"]["from"]["id"]
                        
                        print(f"📥 НОВОЕ СООБЩЕНИЕ: {text[:30]}...", flush=True)
                        
                        # Сразу отправляем статус пользователю
                        send_telegram_message(chat_id, "⏳ Обрабатываю медицинский кейс, формирую SOAP-ноту...")
                        
                        # Получаем ответ от Dify
                        answer = send_to_dify(text, user_id)
                        
                        # Отправляем готовый результат
                        send_telegram_message(chat_id, answer)
        except Exception as e:
            print(f"⚠️ Ошибка цикла getUpdates: {e}", flush=True)
            time.sleep(3)

# 3. Главная точка входа
if __name__ == "__main__":
    bot_thread = threading.Thread(target=telegram_bot_loop, daemon=True)
    bot_thread.start()
    
    run_web_server()