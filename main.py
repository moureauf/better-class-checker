import json
import requests
from bs4 import BeautifulSoup

def send_telegram_alert(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, json=payload)

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
    print(f"Checking: {site['name']}")
    r = requests.get(site["url"], timeout=15)
    r.raise_for_status()
    entries = parse_cards(r.text)

    for watch in site["watch"]:
        found = next((e for e in entries
                      if e["title"] == watch["title"] and e["time"] == watch["time"]), None)
        if not found:
            print(f"❌ Not found: {watch['title']} at {watch['time']}")
            continue

        if found["spaces"] is not None and found["spaces"] >= watch["min_spaces"]:
            msg = f"🏊 Space available!\n{site['name']}\n{found['title']}\n{found['time']}\nSpaces: {found['spaces']}\n{site['url']}"
            send_telegram_alert(bot_token, chat_id, msg)
        else:
            print(f"🛑 {watch['title']} at {watch['time']}: {found['spaces']} spaces")

if __name__ == "__main__":
    with open("config.json") as f:
        config = json.load(f)

    bot_token = config["telegram"]["bot_token"]
    chat_id = config["telegram"]["chat_id"]

    for site in config["urls"]:
        check_site(site, bot_token, chat_id)
