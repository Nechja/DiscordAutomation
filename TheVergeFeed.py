import feedparser
import json
import time
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

def get_mongo_collection(collection_name):
    client = MongoClient('localhost', 27017) 
    db = client.NewsFeeds  # your database name
    return db[collection_name]

def update_last_seen_in_db(feed_name, last_seen_entry_id):
    feed_info_collection = get_mongo_collection(collection_name)
    query = {"name": feed_name}
    new_values = {"$set": {"last_seen": last_seen_entry_id}}
    feed_info_collection.update_one(query, new_values)


def fetch_new_entries(url, last_seen_entry_id):
    feed = feedparser.parse(url)
    new_entries = []

    for entry in feed.entries:
        entry_id = entry.get("id", entry.link)  # Using link as a fallback identifier
        if entry_id != last_seen_entry_id:
            # Extracting image URL and summary from the content
            content = entry.content[0].value if entry.content else ''
            soup = BeautifulSoup(content, 'html.parser')
            img_tag = soup.find('img')
            image_url = img_tag['src'] if img_tag else None
            p_tag = img_tag.find_next('p') if img_tag else None
            summary = p_tag.get_text() if p_tag else ''

            # Adding extracted data to the entry
            entry.image_url = image_url
            entry.summary_text = summary

            new_entries.append(entry)
        else:
            break

    return new_entries

def load_feed_info():
    feed_info_collection = get_mongo_collection("Verge")
    return list(feed_info_collection.find({}))
    
def send_discord_message(webhook_url, feed_name, feed_icon, color, tags, image, entry, summary):
    data = {
        "username": feed_name,
        "avatar_url": feed_icon,
        "embeds": [
            {
            "title": entry.title,
            "url": entry.link,
            "description": summary,
            "color": color,
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

collection_name = "Verge"
get_mongo_collection(collection_name)

feed_info = load_feed_info()
for feed in feed_info:
    feed_name = feed['name']
    feed_icon = feed['icon']
    feed_url = feed['address']
    feed_color = feed['color']
    webhook = feed['webhook']

    last_seen_entry_id = feed['last_seen']
    new_entries = fetch_new_entries(feed_url, last_seen_entry_id)

    if new_entries:
        last_entry_id = new_entries[0].get("id", new_entries[0].link)
        update_last_seen_in_db(feed_name, last_entry_id)


        for entry in new_entries:
            tags = ""
            image = entry.image_url  # Using the extracted image URL
            summary = entry.summary_text
            time.sleep(1)
            print(f"Sending new entry: {entry.title}")
            send_discord_message(webhook, feed_name, feed_icon, feed_color, tags, image, entry, summary)

