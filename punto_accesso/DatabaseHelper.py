import json
import mysql.connector as mysql


class Street:
    def __init__(self, db_data):
        self.id = db_data[0]
        self.name = db_data[1]
        self.__ipAddress = db_data[2]
        self.length = db_data[3]

    def to_dict(self):
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_') and not callable(key)}

    def getIpAddress(self):
        return self.__ipAddress


class Database:
    def __init__(self):
        json_data_file = open("config.json")
        config = json.load(json_data_file)
        self.db = mysql.connect(**config["mysql"])

    def getStreets(self):
        cursor = self.db.cursor()
        query = "SELECT * FROM streets"
        cursor.execute(query)
        streets = []
        for db_data in cursor.fetchall():
            streets.append(Street(db_data))

        return streets
