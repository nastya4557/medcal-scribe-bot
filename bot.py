import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

TELEGRAM_TOKEN = "8960972074:AAG-q3VRgP94-GiNVz-iD_vEVOU4w-u3El0"
DIFY_API_KEY = "app-coVP0lmtD5O1tMEbj1yrfpAq"
DIFY_URL = "https://api.dify.ai/v1/chat-messages"

# Простейший веб-сервер, чтобы Render видел открытый порт на бесплатном тарифе
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")
    
    def log_message(self, format, *args):
        # Отключаем лишний лог HTTP-запросов в консоли
        pass

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

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
        response = requests.post(DIFY_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("answer", "Ошибка: пустой ответ от Dify.")
        else:
            return f"Ошибка API Dify: {response.status_code}"
    except Exception as e:
        return f"Ошибка соединения: {e}"

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def main():
    offset = 0
    print("Medical Scribe бот запущен и готов к работе...")
    while True:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=30"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                updates = response.json().get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        user_id = update["message"]["from"]["id"]
                        
                        print(f"Получено сообщение: {text[:30]}...")
                        
                        # Отправляем текст в Dify и получаем готовую SOAP-ноту
                        answer = send_to_dify(text, user_id)
                        
                        # Пересылаем ответ обратно в Telegram
                        send_telegram_message(chat_id, answer)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if name == "main":
    # Запускаем веб-сервер в фоновом потоке для Render
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Запускаем основного Telegram-бота
    main()