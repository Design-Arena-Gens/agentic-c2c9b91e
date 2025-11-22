import json
import os
import time
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict

import requests


TELEGRAM_API_BASE = "https://api.telegram.org"


def _call_telegram(method: str, payload: Dict[str, Any]) -> requests.Response:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable not set")
    url = f"{TELEGRAM_API_BASE}/bot{token}/{method}"
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response


def _handle_message(message: Dict[str, Any]) -> None:
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if not text:
        _call_telegram(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "I currently respond to text messages only.",
            },
        )
        return

    match text.lower():
        case "/start":
            reply = (
                "مرحباً! أنا بوت تجريبي مكتوب بلغة بايثون.\n"
                "أرسل أي سؤال لأقوم بالرد بمعلومة عن الوقت أو الصدفة."
            )
        case "/help":
            reply = (
                "الأوامر المتاحة:\n"
                "/start – بدء المحادثة\n"
                "/help – عرض هذه الرسالة\n"
                "/time – الحصول على الوقت الحالي\n"
                "/dice – رمي نرد افتراضي"
            )
        case "/time":
            reply = f"الوقت الحالي (UTC): {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}"
        case "/dice":
            reply = f"🎲 نتيجة رمي النرد: {int(time.time()) % 6 + 1}"
        case _:
            reply = f"لقد استقبلت رسالتك: {text}"

    _call_telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": reply,
        },
    )


class handler(BaseHTTPRequestHandler):
    """Minimal webhook handler compatible with Vercel's Python runtime."""

    def _set_headers(self, status_code: int = 200) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802 (name required by BaseHTTPRequestHandler)
        content_length = int(self.headers.get("content-length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(b'{"error":"invalid json"}')
            return

        message = payload.get("message") or payload.get("edited_message")
        if not message:
            self._set_headers(200)
            self.wfile.write(b'{"status":"ignored"}')
            return

        try:
            _handle_message(message)
        except Exception as exc:  # pylint: disable=broad-except
            self._set_headers(500)
            error = json.dumps({"error": str(exc)}).encode()
            self.wfile.write(error)
            return

        self._set_headers(200)
        self.wfile.write(b'{"status":"ok"}')

    def do_GET(self) -> None:  # noqa: N802 (name required by BaseHTTPRequestHandler)
        self._set_headers(200)
        info = {
            "status": "running",
            "message": "Telegram bot webhook alive",
        }
        self.wfile.write(json.dumps(info).encode())
