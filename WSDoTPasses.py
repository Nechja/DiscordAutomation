import feedparser
import json
import time
import re
import requests
from datetime import datetime


class FeedManager:
    def __init__(self, feed_info_filename, pass_info_filename):
        self.feed_info = self.load_json_data(feed_info_filename)
        self.passes = self.load_json_data(pass_info_filename)

    @staticmethod
    def load_json_data(filename):
        try:
            with open(filename, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    @staticmethod
    def save_last_seen_entry(feed_name, last_seen_entry_id):
        with open(f"last_seen_{feed_name}.txt", "w") as file:
            file.write(last_seen_entry_id)

    @staticmethod
    def load_last_seen_entry(feed_name):
        try:
            with open(f"last_seen_{feed_name}.txt", "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            return None


class FeedParser:
    @staticmethod
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


class PassParser:
    @staticmethod
    def parse_html_passes(data_string):
        data = {
            "Name": re.search(r'<strong>(.*?)</strong>', data_string).group(1),
            "Datetime": datetime.strptime(re.search(r'<strong>.*?</strong><br />(.*?)<br', data_string).group(1), '%m/%d/%Y %I:%M %p'),
            "Temperature": re.search(r'<strong>Temperature:</strong>&nbsp;(.*?)&deg;F', data_string).group(1) + "°F",
            "Directions": re.findall(r'<strong>(Eastbound|Westbound|Northbound|Southbound)</strong><br />(.*?)<br', data_string),
            "Conditions": re.search(r'<strong>Conditions:</strong><br />(.*?)<br', data_string).group(1),
            "Weather": re.search(r'<strong>Weather:</strong><br />(.*?)<br', data_string).group(1)
        }
        return data

    @staticmethod
    def find_partial_match(passes_list, title):
        pass_name = title.split(' ')[0]
        for pass_info in passes_list:
            if pass_name in pass_info['Pass']:
                return pass_info
        return None


class DiscordNotifier:
    @staticmethod
    def send_discord_message_passes(webhook_url, feed_name, feed_icon, color, tags, entry, wa_pass, summary):
        try:
            title = entry.title
        except AttributeError:
            title = feed_name

        desc = f"{summary['Directions'][0][1]} \n {summary['Conditions']}"
        formatted_pic = f"{wa_pass['Camera']}?a={int(time.time())}"
        formatted_username = f"WSDoT: {wa_pass['Pass']} - Elevation: {wa_pass['Elevation']}"
        status = "Closed" if 'closed' in entry.summary.lower() else "Open"

        data = {
            "username": formatted_username,
            "avatar_url": feed_icon,
            "embeds": [{
                "title": title,
                "url": entry.link,
                "description": desc,
                "color": color,
                "fields": [
                    {"name": "Temperature", "value": summary['Temperature'], "inline": True},
                    {"name": "Weather", "value": summary['Weather'], "inline": True},
                    {"name": "Status", "value": status, "inline": True}
                ],
                "image": {"url": formatted_pic},
                "footer": {"text": f"Last Updated{summary['Datetime'].strftime('%m/%d/%Y %I:%M %p')} PST"}
            }]
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
        if response.status_code == 204:
            print("Message sent successfully")
        else:
            print(f"Failed to send message: {response.status_code}")


# Main Execution
def main():
    feed_manager = FeedManager("WSDoTFeed.json", "WSDotPasses.json")
    feed_parser = FeedParser()
    pass_parser = PassParser()
    notifier = DiscordNotifier()

    for feed in feed_manager.feed_info:
        feed_name, feed_icon, feed_url, feed_color, webhook = feed['name'], feed['icon'], feed['address'], feed['color'], feed['webhook']
        last_seen_entry_id = feed_manager.load_last_seen_entry(feed_name)
        new_entries = feed_parser.fetch_new_entries(feed_url, last_seen_entry_id)

        if new_entries:
            last_entry_id = new_entries[0].get("id", new_entries[0].link)
            feed_manager.save_last_seen_entry(feed_name, last_entry_id)

            for entry in new_entries:
                tags = ""
                wa_pass = pass_parser.find_partial_match(feed_manager.passes, entry.title)
                if wa_pass is not None:
                    print(f"Sending new entry: {entry.title}")
                    summary = pass_parser.parse_html_passes(entry.summary)
                    notifier.send_discord_message_passes(webhook, feed_name, feed_icon, feed_color, tags, entry, wa_pass, summary)


if __name__ == "__main__":
    main()
