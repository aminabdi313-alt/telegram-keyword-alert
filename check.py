import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import os
import json
import re

RSS_URL = "https://rsshub.ddns.net/telegram/channel/nasrnews"
KEYWORDS = ["صادراتی", "کفش"]

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "state.json"


def normalize(text):
    text = text.replace("ي", "ی")
    return re.sub(r"\s+", " ", text).strip().lower()


def send_telegram(message):
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message
    }).encode()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    urllib.request.urlopen(
        urllib.request.Request(url, data=data),
        timeout=30
    )


def get_feed():
    request = urllib.request.Request(
        RSS_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def main():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except FileNotFoundError:
        state = []

    xml_data = get_feed()
    root = ET.fromstring(xml_data)

    items = root.findall(".//item")

    new_items = []

    for item in items:
        guid = item.findtext("guid") or item.findtext("link") or ""
        title = item.findtext("title") or ""
        description = item.findtext("description") or ""

        if guid in state:
            continue

        text = normalize(title + " " + description)

        if all(normalize(keyword) in text for keyword in KEYWORDS):
            new_items.append((title, item.findtext("link") or ""))

        state.append(guid)

    if new_items:
        for title, link in reversed(new_items):
            message = f"🔔 پست جدید پیدا شد!\n\n{title}\n\n{link}"
            send_telegram(message)

    state = state[-500:]

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
