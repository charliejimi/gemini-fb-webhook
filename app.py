import os
import requests
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

# 讀取環境變數
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN")

# 初始化 Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Facebook webhook 驗證
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == FB_VERIFY_TOKEN:
        return challenge
    return "Unauthorized", 403

# 接收 Facebook 訊息並回應
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):
            sender_id = messaging["sender"]["id"]
            if "message" in messaging and "text" in messaging["message"]:
                user_msg = messaging["message"]["text"]

                # 呼叫 Gemini 回應
                response = model.generate_content(user_msg)
                reply_text = response.text.strip()

                # 傳送回 Facebook
                send_message(sender_id, reply_text)

    return "OK", 200

def send_message(recipient_id, message):
    url = "https://graph.facebook.com/v12.0/me/messages"
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message},
        "messaging_type": "RESPONSE",
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    app.run(port=os.environ.get("PORT"))
