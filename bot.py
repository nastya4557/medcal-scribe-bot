 
import time
import requests

TELEGRAM_TOKEN = "8960972074:AAG-q3VRgP94-GiNVz-iD_vEVOU4w-u3El0"
DIFY_API_KEY = "app-coVP0lmtD5O1tMEbj1yrfpAq"
DIFY_URL = "https://api.dify.ai/v1/chat-messages"

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

if __name__ == "__main__":
    main()