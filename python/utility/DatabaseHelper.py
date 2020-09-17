import json
from datetime import datetime
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


class Route:
    def __init__(self, db_data):
        self.id = db_data[0]
        self.car_id = db_data[1]
        self.car_ip = db_data[2]
        self.route_list = json.loads(db_data[3])
        self.current_index = db_data[4]
        self.current_street_position = db_data[5]


class Database:
    def __init__(self):
        json_data_file = open("config.json")
        config = json.load(json_data_file)

        print("Effettuo la connessione con il DB")
        self.db = mysql.connect(**config["mysql"])

    def close(self):
        print("Chiudo la connessione con il DB")
        self.db.close()

    def getStreets(self, id: int = None) -> [Street]:
        cursor = self.db.cursor()
        query = "SELECT * FROM `streets`"
        values = None
        if(id is not None):
            query += " WHERE `id` = %s"
            values = (id,)
        cursor.execute(query, values)

        streets = []
        for db_data in cursor.fetchall():
            streets.append(Street(db_data))

        return streets

    def upsertStreet(self, name: str, ip_address: str, length: int, id: int = None) -> Street:
        cursor = self.db.cursor()
        if id is not None:
            query = "UPDATE `streets` SET `name` = %s, `ip_address` = %s, `length` = %s `updated_at` = %s WHERE (`id` = %s);"
            values = (name, ip_address, length, datetime.now(), id)
        else:
            query = "INSERT INTO `streets` (`name`, `ip_address`, `length`) VALUES (%s, %s, %s);"
            values = (name, ip_address, length)

        cursor.execute(query, values)
        self.db.commit()

        streets = self.getStreets(cursor.lastrowid)
        if not streets:
            return None
        return streets[0]

    def getRoutes(self, id: int = None) -> [Route]:
        cursor = self.db.cursor()
        query = "SELECT * FROM `routes`"
        values = None
        if(id is not None):
            query += " WHERE `id` = %s"
            values = (id,)
        cursor.execute(query, values)

        routes = []
        for db_data in cursor.fetchall():
            routes.append(Route(db_data))

        return routes

    def upsertRoute(self, car_id: str, car_ip: str, route_list: list = None, current_index: int = None, current_street_position: int = None, id: int = None) -> Route:

        cursor = self.db.cursor()
        if id is not None:
            if(current_index is None):
                raise Exception(
                    "current_index non può essere None se stai aggiuornando una route")
            if(current_street_position is None):
                raise Exception(
                    "current_street_position non può essere None se stai aggiuornando una route")

            query = "UPDATE `routes` SET `car_ip` = %s, `current_index` = %s, `current_street_position` = %s, `updated_at` = %s WHERE (`id` = %s AND `car_id` = %s);"
            values = (car_ip, current_index, current_street_position,
                      datetime.now(), id, car_id)
        else:
            if(route_list is None):
                raise Exception(
                    "route_list non può essere None se stai creando una nuova route")

            query = "INSERT INTO `routes` (`car_id`, `car_ip`, `route_list`) VALUES (%s, %s, %s);"
            values = (car_id, car_ip, json.dumps(route_list))

        cursor.execute(query, values)
        self.db.commit()

        streets = self.getStreets(cursor.lastrowid)
        if not streets:
            return None
        return streets[0]
