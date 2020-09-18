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
        self.destination = db_data[6]


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

    def upsertStreet(self, name: str, ip_address: str, length: int, available: bool = True, id: int = None) -> Street:
        cursor = self.db.cursor()
        if id is not None:
            query = "UPDATE `streets` SET `name` = %s, `ip_address` = %s, `length` = %s `updated_at` = %s WHERE (`id` = %s);"
            values = (name, ip_address, length, datetime.now(), id)
        else:
            query = "INSERT INTO `streets` (`name`, `ip_address`, `length`, `available`) VALUES (%s, %s, %s, %s);"
            values = (name, ip_address, length, available)

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
                    "current_index non può essere None se stai aggiornando una route")
            if(current_street_position is None):
                raise Exception(
                    "current_street_position non può essere None se stai aggiornando una route")

            query = "UPDATE `routes` SET `car_ip` = %s, `current_index` = %s, `current_street_position` = %s,  `finished_at` = %s, `updated_at` = %s WHERE (`id` = %s AND `car_id` = %s);"
            finished_at = datetime.now() if current_index == len(route_list) - 1 else None
            values = (car_ip, current_index, current_street_position,
                      finished_at, datetime.now(), id, car_id)
        else:
            if(route_list is None):
                raise Exception(
                    "route_list non può essere None se stai creando una nuova route")

            query = "INSERT INTO `routes` (`car_id`, `car_ip`, `route_list`, `destination`) VALUES (%s, %s, %s, %s);"
            values = (car_id, car_ip, json.dumps(
                route_list), route_list[-1])

        cursor.execute(query, values)
        self.db.commit()

        routes = self.getRoutes(cursor.lastrowid)
        if not routes:
            return None
        return routes[0]

    def checkRoute(self, car_id: str) -> Route:
        cursor = self.db.cursor()
        query = "SELECT * FROM `routes` WHERE `car_id` = %s AND `finished_at` = null LIMIT 1"
        cursor.execute(query, (car_id,))

        db_data = cursor.fetchone()
        if not db_data:
            return None

        return Route(db_data)
