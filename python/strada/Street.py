import os
import sys

import json
import socket
import argparse
from threading import Thread
from random import randrange
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))) + "/utility")

import Auth
import segnali
from DatabaseHelper import Database


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


class Street:
    def __init__(self, name: str, maxSpeed: int, lenght: int, signals_quantity: list, ipAddress: str = None, port: int = 0):
        self.__db = Database()  # istauro la connessione con il db

        if ipAddress is None:
            hostname = socket.gethostname()
            ipAddress = socket.gethostbyname(hostname)

        # inizializzo la socket
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__s.bind((ipAddress, port))
        self.__s.listen(5)

        self.__ipAddress, self.__port = self.__s.getsockname()
        DB_Street = self.__db.upsertStreet(
            name=name, ip_address=f"{self.__ipAddress}:{self.__port}", length=lenght)  # aggiorno il database
        if DB_Street is None:
            raise Exception("Street save on DB error")

        self.__id = DB_Street.id  # l'id della strada è l'id del db

        self.__threadCount = 0
        self.__lenght = lenght  # metri
        self.__maxSpeed = maxSpeed  # limite massimo che si può raggiungere nella strada
        self.__signals = self.__createSignals(
            signals_quantity, 20, 5)  # creo i segnali nella strada

    def __createSignals(self, signals_quantity: list, step: int, time_semaphore: int):
        """[summary]

        Args:
            signals_quantity (list): [description]
            step (int): [description]
            time_semaphore (int): [description]

        Returns:
            [type]: [description]
        """

        street_signal = list()
        stop = segnali.Stop()

        # limito sin da subito a non superare il limite massimo della strada
        street_signal.append((segnali.SpeedLimit(self.__maxSpeed, True), 20))

        for i in signals_quantity:  # tuple (nome segnale, quantità)
            for count in range(i[1]):
                while True:
                    position = randrange(50, self.__lenght, step)
                    if(position not in (j[1] for j in street_signal) and position < (self.__lenght - stop.getDelta())):
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

        street_signal.append((stop, self.__lenght))  # stop fine strada
        return street_signal

    def __findSignal(self, client_position: float):
        """[summary]

        Args:
            client_position (float): [description]

        Returns:
            [type]: [description]
        """

        # signal[0] è il segnale, signal[1] è la sua posizione nella strada
        if client_position >= self.__lenght:
            stop = self.__signals[-1]
            return stop[0], stop[1]

        for signal in self.__signals:
            if ((signal[1] - client_position < signal[0].delta) and (signal[1] - client_position > 0)):
                return signal[0], signal[1]
        return None, None

    def __checkAuth(self, car_ip: str, car_id: str = None, token_client: str = None):
        """[summary]

        Args:
            car_ip (str): [description]
            car_id (str, optional): [description]. Defaults to None.
            token_client (str, optional): [description]. Defaults to None.

        Raises:
            Exception: [description]

        Returns:
            [type]: [description]
        """
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

        token_client = Auth.decode_token(token_client)
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
            self.__db.upsertRoute(car_id, car_ip, id=DB_Route.id)
            return DB_Route

        if current_index + 1 >= len_route_list or DB_Route.route_list[current_index + 1] != self.__id:
            raise Exception(
                "Non sei autorizzato, Token non valido per questa strada")

        # ho autenticato l'utente e aggiorno la route
        self.__db.upsertRoute(car_id, car_ip, current_index=(
            current_index + 1), current_street_position=0, id=DB_Route.id)

        return DB_Route

    def __comeBackAction(self, car_id: str, car_ip: str, client_speed: int, DB_Route, client_position: float = None):
        """[summary]

        Args:
            car_id (str): [description]
            car_ip (str): [description]
            client_speed (int): [description]
            DB_Route ([type]): [description]
            client_position (float, optional): [description]. Defaults to None.

        Raises:
            Exception: [description]

        Returns:
            [type]: [description]
        """

        if DB_Route is None:
            raise Exception("Errore, dati non corretti o vuoti")

        old_position = DB_Route.current_street_position
        if(client_position <= old_position):
            client_position = old_position
        else:
            self.__db.upsertRoute(
                car_id, car_ip, current_street_position=client_position, id=DB_Route.id)

        signal, signal_position = self.__findSignal(client_position)
        if signal is None:
            return None, client_position, "Niente in strada, vai come una scheggia!!"

        name_signal = signal.getName()
        distance = signal_position - client_position

        if name_signal == "stop" and distance < 3:
            if DB_Route.current_index >= len(DB_Route.route_list):
                # il percorso è finito
                self.__db.upsertRoute(
                    car_id, car_ip, finished_at=datetime.now(), id=DB_Route.id)
                return {"action": "end"}, client_position, f"Congratulazioni sei arrivato a destinazione"

            nextStreet = self.__db.getStreets(
                DB_Route.route_list[DB_Route.current_index + 1])[0]

            host, port = nextStreet.getIpAddress()
            if not host:
                raise Exception("Errore recupero indirizzo strada successiva")
            token = Auth.create_token(
                DB_Route.id, nextStreet.id)  # creo il token

            action = {
                "action": "next",
                "host": host,
                "port": port,
                "access_token": token.decode('UTF-8')
            }
            return action, client_position, f"Procedi con l'host e port indicato per poter raggiungere {nextStreet.name}"

        action = {
            "signal": name_signal,
            "action": signal.getAction() if name_signal != "speed_limit" else signal.getAction(client_speed),
            "distance": distance,
            "speed_limit": signal.getSpeed() if name_signal == "speed_limit" else None
        }

        limit = action['speed_limit'] if name_signal == "speed_limit" else 'prescrizione precedente'
        return action, client_position, (f"Fra {distance:.2f}m incontri il segnale {name_signal}, l'azione che devi eseguire e' {action['action']}. Limite: {limit}")

    @threaded
    def __manageCar(self, client, client_address):
        """[summary]

        Args:
            client ([type]): [description]
            client_address ([type]): [description]
        """

        self.__threadCount += 1
        car_ip = f"{client_address[0]}:{client_address[1]}"

        client.send(json.dumps({
            "status": "success",
            "message": "Welcome to the Server"
        }).encode())

        try:
            while True:
                # è bloccante, va avanti solo se riceve data
                data = client.recv(1024).decode()

                data_decoded = json.loads(data)  # data è json
                car_id = data_decoded['targa'] if 'targa' in data_decoded else None
                access_token = data_decoded['access_token'] if 'access_token' in data_decoded else None

                DB_Route = self.__checkAuth(car_ip, car_id, access_token)

                # qui siamo autenticati
                if 'speed' in data_decoded:
                    pos = data_decoded['position'] if 'position' in data_decoded else None
                    speed = data_decoded['speed']

                    action, position, message = self.__comeBackAction(
                        car_id, car_ip, speed, client_position=pos, DB_Route=DB_Route)
                    client.send(json.dumps({
                        "status": "success",
                        "message": message,
                        "action": action,
                        "position": position
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
        """[summary]
        """

        print(f"Street is listening on {self.__ipAddress}:{self.__port}")
        while True:
            client, client_address = self.__s.accept()
            print(f'Connected to Car: {client_address[0]}:{client_address[1]}')
            handle = self.__manageCar(client, client_address)

        self.__s.close()


def arg_tuple_parse(arg_list):
    """[summary]

    Args:
        arg_list ([type]): [description]

    Raises:
        Exception: [description]

    Returns:
        [type]: [description]
    """
    if arg_list is None:
        return [('semaphore', 2), ('speed_limit', 3)]

    list_signal = []
    for i in arg_list:
        field_args = i.split(',')
        if(len(field_args) == 2):
            list_signal.append(tuple((field_args[0], int(field_args[1]))))
        else:
            raise Exception("Errore formattazione dati")

    return list_signal


if __name__ == '__main__':

    '''
    Esempio Argomenti:
    -ip 10.11.45.36             --> indirizzo ip del server strada
    -p 8888                     --> porta server strada
    -l 100                      --> lunghezza della strada espressa in metri
    -s 90                       --> velocità massima nella strada espressa in km
    -n ss189                    --> nome della strada
    -st stop,2 speed_limit,2    --> lista con nome segnali che devono essere presenti sulla strada e numero.

    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', '--ip-address', type=str, default=None)
    parser.add_argument('-p', '--port', type=int, default=8000)
    parser.add_argument('-l', '--st-lenght', type=int, default=1000)
    parser.add_argument('-s', '--speed', type=int, default=120)
    parser.add_argument('-n', '--name', type=str, default="road1")
    parser.add_argument('-st', '--sig-type', nargs='+', type=str)
    args = parser.parse_args()

    if((args.st_lenght > 100) or (args.speed < 50)):
        street = Street(args.name, args.speed, args.st_lenght,
                        arg_tuple_parse(args.sig_type), args.ip_address, args.port)

        street.run()
    else:
        print("Dati inseriti non sono corretti")
