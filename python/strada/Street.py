import os
import sys

import json
import socket
import argparse
from threading import Thread
from datetime import datetime
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
    def __init__(self, name: str, maxSpeed: int, lenght: int, signals_quantity: list, ipAddress: str = None, port: int = 0):
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
        self.__signals = self.__createSignals(signals_quantity, 5, 5, 10)

    def __createSignals(self, signals_quantity: list, step: int, stop_dist: int, time_semaphore: int):
        street_signal = list()

        for i in signals_quantity:  # tuple (nome segnale, quantità)
            for count in range(i[1]):
                while True:
                    position = randrange(5, self.__lenght, step)
                    if(position not in (j[1] for j in street_signal) and position < (self.__lenght - stop_dist)):
                        break

                if (i[0] == "speed_limit"):
                    street_signal.append(
                        (segnali.SpeedLimit(self.__maxSpeed), position))
                if (i[0] == "semaphore"):
                    street_signal.append(
                        (segnali.Semaforo(time_semaphore), position))
                    street_signal[-1][0].start()

                print(
                    "Il segnale ", street_signal[-1][0].getName(), "è nella posizione ", position)

        # stop fine strada
        street_signal.append((segnali.Stop(), self.__lenght))
        return street_signal

    def __findSignal(self, client_position: float):
        # signal[0] è il segnale, signal[1] è la sua posizione nella strada
        for signal in self.__signals:
            if ((signal[1] - client_position < signal[0].delta) and (signal[1] - client_position > 0)):
                return signal[0], signal[1]
        return None, None

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
            if current_index < 0 or current_index >= len(DB_Route.route_list) or DB_Route.route_list[current_index] != self.__id:
                raise Exception(
                    "Non sei autorizzato ad accedere in questa strada.")

            return DB_Route

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
            return DB_Route

        if current_index + 1 >= len_route_list or DB_Route.route_list[current_index + 1] != self.__id:
            raise Exception(
                "Non sei autorizzato, Token non valido per questa strada")

        # ho autenticato l'utente e aggiorno la route
        self.__db.upsertRoute(
            car_id, car_ip, DB_Route.route_list, current_index + 1, 0, DB_Route.id)

        return DB_Route

    def __comeBackAction(self, car_id: str, car_ip: str, client_speed: int, DB_Route, client_position: float = None):

        new_date_time = (datetime.now() - DB_Route.updated_at).seconds

        if DB_Route is None:
            raise Exception("Errore, dati non corretti o vuoti")

        old_position = DB_Route.current_street_position
        new_position = ((client_speed / 3.6) * new_date_time) + old_position
        if client_position is not None and new_position != client_position:
            # il client si trova in una posizione diversa, teoricamente il confronto delle posizioni deve sempre coincidere
            new_position = client_position

        if(new_position != old_position):
            self.__db.upsertRoute(car_id=car_id, car_ip=car_ip, route_list=DB_Route.route_list,
                                  current_index=DB_Route.current_index, current_street_position=new_position)

        signal, signal_position = self.__findSignal(new_position)
        if signal is None:
            return new_position, None, "Niente in strada, vai come una scheggia!!"

        name_signal = signal.getName()
        action = {
            "signal": name_signal,
            "action": signal.getAction() if name_signal != "speed_limit" else signal.getAction(client_speed),
            "distance": signal_position - new_position,
            "speed_limit": signal.getSpeed() if name_signal == "speed_limit" else None
        }
        return new_position, action, f"Fra {action['distance']} m incontri il segnale {name_signal}, l'azione che devi eseguire è {action['action']}"

    @threaded
    def __manageCar(self, client, client_address):
        self.__threadCount += 1
        car_ip = f"{client_address[0]}:{client_address[1]}"

        client.send(json.dumps({
            "status": "success",
            "message": "Welcome to the Server"
        }).encode())

        try:
            last_recv_datetime = datetime.now()
            while True:
                data = client.recv(2048).decode()
                if not data:
                    if (last_recv_datetime - datetime.now()).seconds > 10:
                        raise Exception("Macchina disconnessa")
                    continue

                last_recv_datetime = datetime.now()
                data_decoded = json.loads(data)  # data è json
                car_id = data_decoded['targa'] if 'targa' in data_decoded else None
                access_token = data_decoded['access_token'] if 'access_token' in data_decoded else None

                DB_Route = self.__checkAuth(car_ip, car_id, access_token)

                # qui siamo autenticati
                if 'speed' in data_decoded:
                    pos = data_decoded['position'] if 'position' in data_decoded else None
                    speed = data_decoded['speed']

                    newPos, action, message = self.__comeBackAction(
                        car_id, car_ip, speed, client_position=pos, DB_Route=DB_Route)
                    client.send(json.dumps({
                        "status": "success",
                        "message": message,
                        "action": action,
                        "position": newPos
                    }).encode())
        except socket.error:
            print("Errore: Client disconnesso - forse è morto")
        except Exception as e:
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

   # print("Your args are:  ", args)
    sig_type = [('semaphore', 2), ('speed_limit', 3)]  # args.sig_type
    street = Street(args.name, args.speed, args.st_lenght,
                    sig_type, args.ip_address, args.port)
    street.run()
