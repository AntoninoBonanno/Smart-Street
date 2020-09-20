import os
import json
from datetime import datetime
import mysql.connector as mysql


class DB_Street:
    """
    Oggetto che rappresenta la strada mappata nel DB
    """

    def __init__(self, db_data):
        self.id = db_data[0]
        self.name = db_data[1]
        # attributo privato, non viene mostrato quando converto in dizionario l'oggetto
        self.__ipAddress = db_data[2]
        self.length = db_data[3]
        self.available = db_data[4]

    def to_dict(self):
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_') and not callable(key)}

    def getIpAddress(self):
        if ":" not in self.__ipAddress:
            return None, None

        host = self.__ipAddress.split(":")
        return host[0], host[1]  # host, port


class DB_Route:
    """
    Oggetto che rappresenta il percorso mappato nel DB
    """

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
        config_path = os.path.join(
            os.path.dirname(__file__), "../../config.json")

        json_data_file = open(config_path, 'r')
        config = json.load(json_data_file)

        print("Effettuo la connessione con il DB")
        self.db = mysql.connect(**config["mysql"])

    def close(self):
        print("Chiudo la connessione con il DB")
        self.db.close()

    def getStreets(self, id: int = None, ipAddress: str = None) -> [DB_Street]:
        """
        Funzione che restituisce le strade dal DB

        Args:
            id (int, optional): Se viene passato un id, effettua la ricerca sull'id specificato. Defaults to None.
            ipAddress (str, optional): Se viene passato ipAddress, effettua la ricerca sull'ipAddress specificato. Defaults to None.
        Returns:
            [DB_Street]: lista delle strade recuperate
        """

        cursor = self.db.cursor()
        query = "SELECT * FROM `streets`"
        values = None
        if(id is not None):
            query += " WHERE `id` = %s"
            values = (id,)

        if(ipAddress is not None):
            if (id is not None):
                query += " AND `ip_address` = %s"
                values = (id, ipAddress)
            else:
                query += " WHERE `ip_address` = %s"
                values = (ipAddress,)
        cursor.execute(query, values)

        streets = []
        for db_data in cursor.fetchall():
            streets.append(DB_Street(db_data))

        return streets

    def upsertStreet(self, name: str, ip_address: str, length: int, available: bool = True, id: int = None) -> DB_Street:
        """
        Funzione che esegue l'upsert della strada (inserimento o aggornamento) sul DB

        Args:
            name (str): nome della strada
            ip_address (str): indirizzo ip della strada
            length (int): lunghezza in km della strada
            available (bool, optional): se la strada è disponibile. Defaults to True.
            id (int, optional): Id della strada da aggiornare, se non viene passato viene creata una nuova strada. Defaults to None.

        Returns:
            DB_Street: La strada appena creata
        """

        if id is None:
            streets = self.getStreets(ipAddress=ip_address)
            if streets:
                id = streets[0].id

        cursor = self.db.cursor()
        if id is not None:
            query = "UPDATE `streets` SET `name` = %s, `ip_address` = %s, `length` = %s, `available` = %s, `updated_at` = %s WHERE (`id` = %s);"
            values = (name, ip_address, length, available, datetime.now(), id)
        else:
            query = "INSERT INTO `streets` (`name`, `ip_address`, `length`, `available`) VALUES (%s, %s, %s, %s);"
            values = (name, ip_address, length, available)

        cursor.execute(query, values)
        self.db.commit()

        streets = self.getStreets(cursor.lastrowid)
        if not streets:
            return None
        return streets[0]

    def getRoutes(self, id: int = None) -> [DB_Route]:
        """
        Funzione che restituisce i percorsi dal DB

        Args:
            id (int, optional): Se viene passato un id, effettua la ricerca sull'id specificato . Defaults to None.

        Returns:
            [DB_Route]: lista dei percorsi recuperati
        """

        cursor = self.db.cursor()
        query = "SELECT * FROM `routes`"
        values = None
        if(id is not None):
            query += " WHERE `id` = %s"
            values = (id,)
        cursor.execute(query, values)

        routes = []
        for db_data in cursor.fetchall():
            routes.append(DB_Route(db_data))

        return routes

    def upsertRoute(self, car_id: str, car_ip: str, route_list: list = None, current_index: int = -1, current_street_position: int = None, id: int = None) -> DB_Route:
        """
        Funzione che esegue l'upsert del percorso (inserimento o aggornamento) sul DB

        Args:
            car_id (str): l'id della macchina (targa) da associare il percorso
            car_ip (str): l'ip attuale della macchina
            route_list (list, optional): Lista di strade che formano il porcorso, obligatorio alla creazione, non è possibile aggiornarla. Defaults to None.
            current_index (int, optional): Indice della lista dove è attualmente la macchina, obligatoria quando si fa l'aggiornamento. Defaults to None.
            current_street_position (int, optional): Posizione attuale della macchina sulla strada dove è attualmente la macchina, obligatoria quando si fa l'aggiornamento. Defaults to None.
            id (int, optional): Id del percorso da aggiornare, se non viene passato viene creata un nuovo percorso. Defaults to None.

        Raises:
            Exception: Quando non vengono passati i parametri corretti per l'operazione da fare

        Returns:
            DB_Route: Il percorso appena creato
        """

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

    def checkRoute(self, car_id: str) -> DB_Route:
        """
        Verifica se esiste un percorso per la macchina indicata

        Args:
            car_id (str): id della macchina (targa) da controllare

        Returns:
            DB_Route: None se non esiste il percorso, altrimenti il percorso attuale della macchina
        """

        cursor = self.db.cursor()
        query = "SELECT * FROM `routes` WHERE `car_id` = %s AND `finished_at` is null LIMIT 1"
        cursor.execute(query, (car_id,))

        db_data = cursor.fetchone()
        if not db_data:
            return None

        return DB_Route(db_data)
