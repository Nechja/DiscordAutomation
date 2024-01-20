import feedparser
import json
import time
import re
import requests
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from datetime import datetime

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
    
def load_pass_info():
    try:
        with open("WSDotPasses.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    
class HTMLContainer:
    pass
    

def parse_html_passes(data_string):
    name = re.search(r'<strong>(.*?)</strong>', data_string).group(1)
    datetime_str = re.search(r'<strong>.*?</strong><br />(.*?)<br', data_string).group(1)
    temperature = re.search(r'<strong>Temperature:</strong>&nbsp;(.*?)&deg;F', data_string).group(1)
    directions = re.findall(r'<strong>(Eastbound|Westbound|Northbound|Southbound)</strong><br />(.*?)<br', data_string)
    conditions = re.search(r'<strong>Conditions:</strong><br />(.*?)<br', data_string).group(1)
    weather = re.search(r'<strong>Weather:</strong><br />(.*?)<br', data_string).group(1)

    # Convert datetime string to datetime object
    datetime_obj = datetime.strptime(datetime_str, '%m/%d/%Y %I:%M %p')

    # Organizing data into a dictionary
    extracted_data = {
        "Name": name,
        "Datetime": datetime_obj,
        "Temperature": temperature + "°F",
        "Directions": directions,
        "Conditions": conditions,
        "Weather": weather
    }
    return extracted_data
    
def send_discord_message_passes(webhook_url, feed_name, feed_icon, color, tags, entry, waPass, summery):
    try:
        title = entry.title
    except AttributeError:
        title = feed_name

    desc = f"{summery['Directions'][0][1]} \n {summery['Conditions']}"
    formated_pic = f"{waPass['Camera']}?a={int(time.time())}"
    formated_username = f"WSDoT: {waPass['Pass']} - Elevation: {waPass['Elevation']}"

    if 'closed' in entry.summary.lower():
        status = "Closed"
    else:
        status = "Open"

    data = {
        "username": formated_username,
        "avatar_url": feed_icon,
        "embeds": [
            {
            "title": title, 
            "url": entry.link,
            "description": desc,
            "color": color,
            "fields": [
                {
                    "name": "Temperature",
                    "value": summery['Temperature'],
                    "inline": True
                },
                {
                    "name": "Weather",
                    "value": summery['Weather'],
                    "inline": True
                },
                {
                    "name": "Status",
                    "value": status,
                    "inline": True
                }
            ],
            "image": {
                "url": formated_pic
            },
            "footer": {
                "text": f"Last Updated{summery['Datetime'].strftime('%m/%d/%Y %I:%M %p')} PST",
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


def find_partial_match(passes_list, title):
    pass_name = title.split(' ')[0]
    for pass_info in passes_list:
        if pass_name in pass_info['Pass']:
            return pass_info
    return None 

passes = load_pass_info()

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
            waPass = find_partial_match(passes, entry.title)
            if waPass is not None:
                print(f"Sending new entry: {entry.title}")
                summery = parse_html_passes(entry.summary)
                send_discord_message_passes(webhook, feed_name, feed_icon, feed_color, tags, entry, waPass, summery)
            

