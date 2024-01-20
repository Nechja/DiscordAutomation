import feedparser
import json
import time
import requests
from bs4 import BeautifulSoup

def save_last_seen_entry(feed_name, last_seen_entry_id):
    with open(f"last_seen_{feed_name}.txt", "w") as file:
        file.write(last_seen_entry_id)

def load_last_seen_entry(feed_name):
    try:
        with open(f"last_seen_{feed_name}.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

def fetch_new_entries(url, last_seen_entry_id):
    feed = feedparser.parse(url)
    new_entries = []

    for entry in feed.entries:
        entry_id = entry.get("id", entry.link)  # Using link as a fallback identifier
        if entry_id != last_seen_entry_id:
            new_entries.append(entry)
        else:
            break

    return new_entries

def load_feed_info():
    try:
        with open("Tumblr.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    
def send_discord_message(webhook_url, feed_name, feed_icon, color, tags, image, entry):
    try:
        title = entry.title
    except AttributeError:
        title = feed_name



    data = {
        "username": feed_name,
        "avatar_url": feed_icon,
        "embeds": [
            {
            "title": title, 
            "url": entry.link,
            "description": entry.summary,
            "color": color,
            "fields": [
                {
                    "name": "Tags",
                    "value": tags
                }
            ],
            "image": {
                "url": image
            }
            }

        ]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
    if response.status_code == 204:
        print("Message sent successfully")
    else:
        print(f"Failed to send message: {response.status_code}")

def fetch_preview(url):
    try:
        response = requests.get(url)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')

        title_tag = soup.find('title')
        first_image_url = None
        if title_tag:
            first_image_tag = title_tag.find_next('img')
            if first_image_tag and first_image_tag.get('src'):
                first_image_url = first_image_tag['src']

        if not first_image_url:
            first_image_url = None

        return first_image_url
    except Exception as e:
        return str(e)


feed_info = load_feed_info()
for feed in feed_info:
    feed_name = feed['name']
    feed_icon = feed['icon']
    feed_url = feed['address']
    feed_color = feed['color']
    webhook = feed['webhook']

    last_seen_entry_id = load_last_seen_entry(feed_name)
    new_entries = fetch_new_entries(feed_url, last_seen_entry_id)

    if new_entries:
        last_entry_id = new_entries[0].get("id", new_entries[0].link)
        save_last_seen_entry(feed_name, last_entry_id)

        for entry in new_entries:
            tags = ""
            image = fetch_preview(entry.link)
            if entry.tags:
                for tag in entry.tags:
                    tags += tag.term + ", "
                tags = tags[:-2]
            time.sleep(1)
            #print(f"Sending new entry: {entry.title}")
            send_discord_message(webhook, feed_name, feed_icon, feed_color, tags, image, entry)

