import json
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env (for local dev)
load_dotenv()

def send_telegram_alert(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Alert sent: {message}")
    except Exception as e:
        print(f"❌ Failed to send Telegram alert: {e}")

def normalize(text):
    return " ".join(text.strip().split())

def parse_cards(html):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(".card-content")
    entries = []

    for card in cards:
        title_el = card.select_one("h3")
        details = card.find_all("p")

        if not title_el or len(details) < 2:
            continue

        title = normalize(title_el.text)
        time = normalize(details[0].text)
        spaces_text = normalize(details[-1].text)

        try:
            spaces = int(spaces_text.split(":")[-1])
        except:
            spaces = None

        entries.append({
            "title": title,
            "time": time,
            "spaces": spaces
        })

    return entries

def check_site(site, bot_token, chat_id):
    print(f"\n🔍 Checking: {site['name']}")
    try:
        r = requests.get(site["url"], timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to load {site['url']}: {e}")
        return

    entries = parse_cards(r.text)

    for watch in site["watch"]:
        found = next((e for e in entries
                      if e["title"] == watch["title"] and e["time"] == watch["time"]), None)

        if not found:
            print(f"⚠️ Not found: {watch['title']} at {watch['time']}")
            continue

        if found["spaces"] is not None and found["spaces"] >= watch["min_spaces"]:
            msg = (
                f"🏊 Space available!\n"
                f"{site['name']}\n"
                f"{found['title']}\n"
                f"{found['time']}\n"
                f"Spaces: {found['spaces']}\n"
                f"{site['url']}"
            )
            send_telegram_alert(bot_token, chat_id, msg)
        else:
            print(f"⛔ {watch['title']} at {watch['time']}: {found['spaces']} spaces")

if __name__ == "__main__":
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in environment.")
        exit(1)

    try:
        with open("config.json") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config.json: {e}")
        exit(1)

    for site in config["urls"]:
        check_site(site, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
