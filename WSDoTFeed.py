import feedparser
import json
import time
import requests
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome

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
        with open("WSDoTFeed.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    
class HTMLContainer:
    pass
    
def parse_html(html_string):
    # Parse the HTML
    soup = BeautifulSoup(html_string, 'html.parser')

    # Find all div elements
    divs = soup.find_all('div')

    # Assigning each div to a specific field in HTMLContainer
    html = HTMLContainer()
    html.impact = divs[0].get_text() if len(divs) > 0 else ""
    html.desc = divs[1].get_text() if len(divs) > 1 else ""
    html.date = divs[2].get_text() if len(divs) > 2 else ""

    return html;
    
def send_discord_message_road(webhook_url, feed_name, feed_icon, color, tags, image, entry):


    html = parse_html(entry.summary)

    if html.impact != "Low":
        data = {
            "username": feed_name,
            "avatar_url": feed_icon,
            "embeds": [
                {
                "title": entry.title,
                "url": entry.link,
                "description": html.desc,
                "color": color,
                "fields": [
                    {
                        "name": "Impact",
                        "value": html.impact
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the first <img> tag with class 'flat-camera-image'

        camera_image_div = soup.find('div', class_='flat-camera-image')
        img_tag = camera_image_div.find('img') if camera_image_div else None
        image_url = img_tag['src'] if img_tag else None

        return image_url
    except Exception as e:
        return str(e)
    
def send_discord_message_passes(webhook_url, feed_name, feed_icon, color, tags, image, entry):
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
            time.sleep(1)
            print(f"Sending new entry: {entry.title}")
            if feed_name == "WSDoT Highway Alerts":
                send_discord_message_road(webhook, feed_name, feed_icon, feed_color, tags, image, entry)
            else:
                send_discord_message_passes(webhook, feed_name, feed_icon, feed_color, tags, image, entry)

