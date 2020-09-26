import os
import sys

import json
import socket
import argparse
from threading import Thread
from random import randrange

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))) + "/utility")

import segnali
import Auth as auth
from DatabaseHelper import Database


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


class Street:
    def __init__(self, name: str, maxSpeed: int, lenght: int, signal_type: list, ipAddress: str = None, port: int = 0):
        self.__db = Database()

        if ipAddress is None:
            hostname = socket.gethostname()
            ipAddress = socket.gethostbyname(hostname)

        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__s.bind((ipAddress, port))
        self.__s.listen(5)

        self.__ipAddress, self.__port = self.__s.getsockname()
        DB_Street = self.__db.upsertStreet(
            name=name, ip_address=f"{self.__ipAddress}:{self.__port}", length=lenght)
        if DB_Street is None:
            raise Exception("Street save on DB error")

        self.__id = DB_Street.id  # strada istanziata nel database e restituzione del database
        self.__available = DB_Street.available

        self.__threadCount = 0
        self.__lenght = lenght
        self.__maxSpeed = maxSpeed
        self.__signal_type = signal_type  # tuple (segnale,posizione)
        self.__signals = self.__create_signal(5, 5, 10)

        for i in self.__signals:
            if i[0].getName() == "semaphore":
                i[0].run()

    def __create_signal(self, step: int, stop_dist: int, time_semaphore: int):
        street_signal = list()

        for i in self.__signal_type:
            for count in range(i[1]):
                while True:
                    position = randrange(0, self.__lenght, step)
                    if(position not in (j[1] for j in street_signal) and position < (self.__lenght - stop_dist)):
                        break

                if (i[0] == "speed_limit"):
                    street_signal.append(
                        (segnali.SpeedLimit(self.__maxSpeed), position))
                if (i[0] == "stop"):
                    street_signal.append((segnali.Stop(), position))
                if (i[0] == "semaphore"):
                    street_signal.append(
                        (segnali.Semaforo(time_semaphore), position))

        # stop fine strada
        street_signal.append((segnali.Stop(), self.__lenght))
        return street_signal

    def __checkAuth(self, car_ip: str, car_id: str = None, token_client: str = None):
        if car_id is None:
            raise Exception("Targa passata non valida.")

        if token_client is None:
            # verificare se è già autenticato
            DB_Route = self.__db.getRoutes(car_id=car_id, finished=False)
            if not DB_Route or DB_Route[0].car_ip != car_ip:
                raise Exception(
                    "Non sei autorizzato, richiedi un nuovo token al punto di accesso")

            DB_Route = DB_Route[0]
            current_index = DB_Route.current_index
            if current_index < 0 or len(current_index >= DB_Route.route_list) or DB_Route.route_list[current_index] != self.__id:
                raise Exception(
                    "Non sei autorizzato ad accedere in questa strada.")

            return DB_Route.current_street_position, DB_Route.updated_at

        token_client = auth.decode_token(token_client)
        if token_client is None:
            raise Exception(
                "Token scaduto o non valido, richiedi un nuovo token al punto di accesso")

        # il token decodificato è un dizionario
        street_id_token = token_client['street_id']
        route_id_token = token_client['route_id']

        if street_id_token != self.__id:
            raise Exception(
                "Non sei autorizzato, Token non valido per questa strada")

        DB_Route = self.__db.getRoutes(route_id_token)
        if not DB_Route or DB_Route[0].car_id != car_id:
            raise Exception(
                "Non sei autorizzato, il token inviato non corrisponde alla tua targa")

        DB_Route = DB_Route[0]
        current_index = DB_Route.current_index
        len_route_list = len(DB_Route.route_list)
        if current_index >= 0 and current_index < len_route_list and DB_Route.route_list[current_index] == self.__id and DB_Route.current_street_position < self.__lenght:
            #  è già autenticato
            self.__db.upsertRoute(car_id, car_ip, DB_Route.route_list,
                                  current_index, DB_Route.current_street_position, DB_Route.id)
            return DB_Route.current_street_position, DB_Route.updated_at

        if current_index + 1 >= len_route_list or DB_Route.route_list[current_index + 1] != self.__id:
            raise Exception(
                "Non sei autorizzato, Token non valido per questa strada")

        # ho autenticato l'utente e aggiorno la route
        self.__db.upsertRoute(
            car_id, car_ip, DB_Route.route_list, current_index + 1, 0, DB_Route.id)

        return DB_Route.current_street_position, DB_Route.updated_at

    @threaded
    def __manageCar(self, client, client_address):
        self.__threadCount += 1
        car_ip = f"{client_address[0]}:{client_address[1]}"

        client.send(json.dumps({
            "status": "success",
            "message": "Welcome to the Server"
        }).encode())

        try:

            while True:
                data = client.recv(2048).decode()
                if not data:
                    # fare controlli
                    continue

                data_decoded = json.loads(data)  # data è json
                car_id = data_decoded['targa'] if 'targa' in data_decoded else None
                access_token = data_decoded['access_token'] if 'access_token' in data_decoded else None

                old_position, old_timestamp = self.__checkAuth(
                    car_ip, car_id, access_token)

                # qui siamo autenticati
                if 'speed' in data_decoded:
                    pos = data_decoded['position']
                    speed = data_decoded['speed']

                    client.send(json.dumps({
                        "status": "success",
                        "message": "messaggio",
                        "actions": [{
                            "speed": "azione dello speed",
                            "position": 0
                        }]
                    }).encode())

        except Exception as e:
            print(e)
            client.send(json.dumps({
                "status": "error", "message": str(e)
            }).encode())

        client.close()
        self.__threadCount -= 1

    def run(self):
        print(f"Street is listening on {self.__ipAddress}:{self.__port}")
        while True:
            client, client_address = self.__s.accept()
            print(f'Connected to Car: {client_address[0]}:{client_address[1]}')
            handle = self.__manageCar(client, client_address)

        self.__s.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', '--ip-address', type=str, default=None)
    parser.add_argument('-p', '--port', type=int, default=8000)
    parser.add_argument('-l', '--st-lenght', type=int, default=50)
    parser.add_argument('-s', '--speed', type=int, default=50)
    parser.add_argument('-n', '--name', type=str, default="road1")
    parser.add_argument('-st', '--sig-type', nargs='+', type=str)
    args = parser.parse_args()

    print("Your args are:  ", args)
    sig_type = [('stop', 1), ('speed_limit', 2)]  # args.sig_type
    street = Street(args.name, args.speed, args.st_lenght,
                    sig_type, args.ip_address, args.port)
    street.run()
