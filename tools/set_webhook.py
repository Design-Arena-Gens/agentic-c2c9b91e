import os
import sys
from urllib.parse import urljoin

import requests


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python tools/set_webhook.py https://your-domain/api/telegram_bot")
        sys.exit(1)

    webhook_url = sys.argv[1].rstrip("/")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(2)

    endpoint = urljoin(f"https://api.telegram.org/bot{token}/", "setWebhook")
    response = requests.post(endpoint, json={"url": webhook_url}, timeout=10)
    response.raise_for_status()
    data = response.json()
    print(f"Webhook set: {data}")


if __name__ == "__main__":
    main()
