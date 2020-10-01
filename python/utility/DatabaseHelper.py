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
        self.length = db_data[3]  # lunghezza in metri della strada
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
        self.connected = db_data[7]
        self.finished_at = db_data[8]
        self.updated_at = db_data[9]


class DB_Signal:
    """
    Oggetto che rappresenta un segnale mappato nel DB
    """

    def __init__(self, db_data):
        self.id = db_data[0]
        self.street_id = db_data[1]
        self.name = db_data[2]
        self.position = db_data[3]
        self.action = db_data[4]


class Database:
    def __init__(self):
        config_path = os.path.join(
            os.path.dirname(__file__), "../../config.json")

        json_data_file = open(config_path, 'r')
        self.__config = json.load(json_data_file)
        self.db = None
        self.cursor = None

    def connect(self):
        """
        Effettua la connessione con il database

        Returns:
            cursore del database
        """
        if (self.db is None or self.db.is_connected() == False):
            self.db = mysql.connect(**self.__config["mysql"])
            self.cursor = self.db.cursor()

    def close(self):
        """
        Chiude la connessione con il database
        """
        if (self.db is not None and self.db.is_connected() == True):
            self.cursor.close()
            self.db.close()

    def getStreets(self, id: int = None, ipAddress: str = None, available: bool = None) -> [DB_Street]:
        """
        Funzione che restituisce le strade dal DB

        Args:
            id (int, optional): Se viene passato un id, effettua la ricerca sull'id specificato. Defaults to None.
            ipAddress (str, optional): Se viene passato ipAddress, effettua la ricerca sull'ipAddress specificato. Defaults to None.
            available (bool, optional): Se viene passato, ricerca se le strade sono available oppure no. Defaults to True.
        Returns:
            [DB_Street]: lista delle strade recuperate
        """

        self.connect()

        query = ""
        values = None
        if id is not None:
            query += " WHERE `id` = %s"
            values = (id,)

        if ipAddress is not None:
            if id is not None:
                query += " AND `ip_address` = %s"
                values = (id, ipAddress)
            else:
                query += " WHERE `ip_address` = %s"
                values = (ipAddress,)

        if available is not None:
            query += (" AND `available` = %s" if query !=
                      "" else " WHERE `available` = %s")
            values = (available,) if values is None else (*values, available)

        self.cursor.execute("SELECT * FROM `streets`" + query, values)

        streets = []
        for db_data in self.cursor.fetchall():
            streets.append(DB_Street(db_data))

        self.close()
        return streets

    def upsertStreet(self, name: str, ip_address: str, length: int, available: bool = True, id: int = None) -> DB_Street:
        """
        Funzione che esegue l'upsert della strada (inserimento o aggornamento) sul DB

        Args:
            name (str): nome della strada
            ip_address (str): indirizzo ip della strada
            length (int): lunghezza in m della strada
            available (bool, optional): se la strada è disponibile. Defaults to True.
            id (int, optional): Id della strada da aggiornare, se non viene passato viene creata una nuova strada. Defaults to None.

        Returns:
            DB_Street: La strada appena creata
        """

        if id is None:
            # se esiste già una strada con lo stesso ip, la aggiorno
            streets = self.getStreets(ipAddress=ip_address)
            if streets:
                id = streets[0].id

        self.connect()

        if id is not None:
            query = "UPDATE `streets` SET `name` = %s, `ip_address` = %s, `length` = %s, `available` = %s, `updated_at` = %s WHERE (`id` = %s);"
            values = (name, ip_address, length, available, datetime.now(), id)
        else:
            query = "INSERT INTO `streets` (`name`, `ip_address`, `length`, `available`) VALUES (%s, %s, %s, %s);"
            values = (name, ip_address, length, available)

        self.cursor.execute(query, values)
        self.db.commit()

        last_id = id or self.cursor.lastrowid
        self.close()

        streets = self.getStreets(last_id)
        if not streets:
            return None
        return streets[0]

    def getRoutes(self, id: int = None, car_id: str = None, finished: bool = None, connected: bool = None) -> [DB_Route]:
        """
        Funzione che restituisce i percorsi dal DB

        Args:
            id (int, optional): Se viene passato un id, effettua la ricerca sull'id specificato. Defaults to None.
            car_id (str, optional): Se viene passato un car_id, effettua la ricerca sul car_id specificato. Defaults to None.
            finished (bool, optional): Se viene passato True, ricerca le route completate. Defaults to None.
            connected (bool, optional): Se viene passato True, ricerca le route che hanno i client connessi. Defaults to None.

        Returns:
            [DB_Route]: lista dei percorsi recuperati
        """

        self.connect()

        query = ""
        values = None
        if id is not None:
            query += " WHERE `id` = %s"
            values = (id,)

        if car_id is not None:
            if query == "":
                query += " WHERE `car_id` = %s"
                values = (car_id,)
            else:
                query += " AND `car_id` = %s"
                values = (id, car_id)

        if finished is not None:
            query += (" WHERE `finished_at` is " if query ==
                      "" else " AND `finished_at` is ")
            query += "not null" if finished == True else "null"

        if connected is not None:
            if query == "":
                query += " WHERE `connected` = %s"
                values = (connected,)
            else:
                query += " AND `connected` = %s"
                values = (*values, connected)

        self.cursor.execute("SELECT * FROM `routes`" + query, values)

        routes = []
        for db_data in self.cursor.fetchall():
            routes.append(DB_Route(db_data))

        self.close()
        return routes

    def upsertRoute(self, car_id: str, car_ip: str, route_list: list = None, current_index: int = None, current_street_position: float = None, finished_at: datetime = None, connected: bool = None, id: int = None) -> DB_Route:
        """
        Funzione che esegue l'upsert del percorso (inserimento o aggornamento) sul DB

        Args:
            car_id (str): l'id della macchina (targa) da associare il percorso
            car_ip (str): l'ip attuale della macchina
            route_list (list, optional): Lista di strade che formano il porcorso, non può essere aggiornata. Defaults to None.
            current_index (int, optional): Indice della lista dove è attualmente la macchina, obligatoria quando si fa l'aggiornamento. Defaults to None.
            current_street_position (int, optional): Posizione attuale della macchina sulla strada dove è attualmente la macchina, obligatoria quando si fa l'aggiornamento. Defaults to None.
            finished_at (datetime, optional): Data di fine della route. Defaults to None.
            connected (bool, optional): Flag se il client è connesso oppure no. Defaults to None.
            id (int, optional): Id del percorso da aggiornare, se non viene passato viene creata un nuovo percorso. Defaults to None.

        Raises:
            Exception: Quando non vengono passati i parametri corretti per l'operazione da fare

        Returns:
            DB_Route: Il percorso appena creato
        """

        self.connect()
        if id is not None:
            values = (car_ip,)
            query = ""
            if current_index is not None:
                query += "`current_index` = %s, "
                values = (*values, current_index)

            if current_street_position is not None:
                query += "`current_street_position` = %s, "
                values = (*values, current_street_position)

            if finished_at is not None:
                query += "`finished_at` = %s, "
                values = (*values, finished_at)

            if connected is not None:
                query += "`connected` = %s, "
                values = (*values, connected)

            query = f"UPDATE `routes` SET `car_ip` = %s, {query} `updated_at` = %s WHERE (`id` = %s AND `car_id` = %s);"
            values = (*values, datetime.now(), id, car_id)
        else:
            if(route_list is None):
                raise Exception(
                    "route_list non può essere None se stai creando una route")

            query = "INSERT INTO `routes` (`car_id`, `car_ip`, `route_list`, `destination`) VALUES (%s, %s, %s, %s);"
            values = (car_id, car_ip, json.dumps(
                route_list), route_list[-1])

        self.cursor.execute(query, values)
        self.db.commit()

        last_id = id or self.cursor.lastrowid
        self.close()

        routes = self.getRoutes(last_id)
        if not routes:
            return None

        return routes[0]

    def getSignals(self, street_id: int) -> [DB_Signal]:
        """
        Funzione che restituisce i segnali dal DB

        Args:
            street_id (int): Id della strada di cui si vogliono recuperare i segnali

        Returns:
            [DB_Signal]: lista dei segnali recuperati
        """
        self.connect()
        self.cursor.execute(
            "SELECT * FROM `signals` WHERE `street_id` = %s", (street_id,))

        signals = []
        for db_data in self.cursor.fetchall():
            signals.append(DB_Signal(db_data))

        self.close()
        return signals

    def upsertSignal(self, street_id: int, name: str, position: float, action: str = "", id: int = None):
        """
        Funzione che esegue l'upsert del segnale (inserimento o aggornamento) sul DB

        Args:
            street_id (int): Id della strada di cui si vuole salvare il segnale
            name (str): nome/tipo del segnale
            position (float): posizione del segnale sulla strada
            action (str): azione che viene eseguita dal segnale
            id (int, optional): Id del segnale da aggiornare, se non viene passato viene creato un nuovo segnale. Defaults to None.
        """

        self.connect()
        if id is not None:
            query = f"UPDATE `signals` SET `name` = %s, `position` = %s, `action` = %s, `updated_at` = %s WHERE (`id` = %s AND `street_id` = %s);"
            values = (name, position, action, datetime.now(), id, street_id)
        else:
            query = "INSERT INTO `signals` (`street_id`, `name`, `position`, `action`) VALUES (%s, %s, %s, %s);"
            values = (street_id, name, position, action)

        self.cursor.execute(query, values)
        self.db.commit()

        last_id = id or self.cursor.lastrowid
        self.close()

    def deleteSignals(self, street_id: int):
        """
        Funzione che elimina i segnali dal DB

        Args:
            street_id (int): Id della strada di cui si vogliono eliminare i segnali
        """

        self.connect()
        self.cursor.execute(
            "DELETE FROM `signals` WHERE `street_id` = %s", (street_id,))
        self.db.commit()
        self.close()
