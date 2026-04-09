from pymongo import MongoClient


class MongoDB:
    def __init__(self, uri):
        self.client = MongoClient(uri)
        db_name = uri.rsplit("/", 1)[-1] if "/" in uri and uri.rsplit("/", 1)[-1] else "women_safety_db"
        self.db = self.client[db_name]

    @property
    def users(self):
        return self.db["users"]

    @property
    def contacts(self):
        return self.db["contacts"]

    @property
    def alerts(self):
        return self.db["alerts"]

    @property
    def incidents(self):
        return self.db["incidents"]
