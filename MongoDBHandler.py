from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from pymongo.errors import PyMongoError

class MongoDBHandler:
    def __init__(self, uri, db_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.feeds = self.db.feeds
        self.entries = self.db.entries
        self.passes = self.db.passes
        print(f"Connected to MongoDB database: {db_name}")

    def get_feed_info(self):
        try:
            return list(self.feeds.find({}))
            print(f"Found {len(feeds)} feeds in the database.")
        except:
            print("Failed to get feed info")
    
    def get_passes(self):
        try:
            return list(self.passes.find({}))
        except:
            print("Failed to get passes")

    def get_last_posted_entry_datetime(self, feed_name):
        entry = self.entries.find_one({"feed_name": feed_name}, sort=[("datetime", -1)])
        return entry['datetime'] if entry else None

    def save_new_entry(self, feed_name, entry_datetime):
        self.entries.insert_one({"feed_name": feed_name, "datetime": entry_datetime})

    def test_connection(self):
        try:
            self.client.admin.command('ismaster')
            return True
        except:
            return False
        
    def print_all_data(self):
        print("Data in MongoDB:")
        collection_names = self.db.list_collection_names()
        print(f"Collections in the database: {collection_names}")

        for collection_name in collection_names:
            print(f"\nData in collection '{collection_name}':")
            collection = self.db[collection_name]
            document_count = collection.count_documents({})
            print(f"Total documents in '{collection_name}': {document_count}")

            if document_count > 0:
                for document in collection.find().limit(10):  # Limit to 10 documents for readability
                    print(document)
            else:
                print("No documents found in this collection.")
        

    def update_last_posted_entry_datetime(self, id, current_datetime):
        try:
            query = {'_id': ObjectId(id)}  # Convert string to ObjectId
            new_values = {"$set": {'Last_Posted': current_datetime}}
            result = self.passes.update_one(query, new_values)

            if result.matched_count == 0:
                print("No document found with the provided id.")
            elif result.modified_count == 0:
                print("The document was found but not modified.")
            else:
                print("Document updated successfully.")
        except PyMongoError as e:
            print(f"An error occurred: {e}")