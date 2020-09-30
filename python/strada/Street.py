from DatabaseHelper import Database  # contiene funzioni per gestire il db

import segnali  # contiene le classi con i segnali
import Auth  # contiene funzioni per gestire l'autenticazione
import os
import sys

import json
import socket
import argparse
from threading import Thread
from random import randrange
from datetime import datetime
import time

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))) + "/utility")

'''
def threaded(fn):
    # questa funzione ci serve per far si che la funzione managecar sia un thread
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper
'''


class Street:

    def __init__(self, name: str, maxSpeed: int, lenght: int, signals_quantity: list, ipAddress: str = None, port: int = 0):
        """funzione di inizializzazione dell'oggetto strada 

        Args:
            name (str): nome della strada
            maxSpeed (int): massima velocità raggiungibile nella strada
            lenght (int): lunghezza della strada espressa in metri 
            signals_quantity (list): lista di tuple contente nome del segnale e quantità 
            ipAddress (str, optional): indirizzo ip della strada ,default None
            port (int, optional): porta. Defaults to 0.

        Raises:
            Exception: [description]
        """
        self.__db = Database()  # istauro la connessione con il db

        if ipAddress is None:
            # se l'indirizzo ip è nullo l'indirizzo ip della strada diventa quello del localhost
            hostname = socket.gethostname()
            ipAddress = socket.gethostbyname(hostname)

        # inizializzo la socket.
        # Con Socket AF_INET indichiamo di lavorare con indirizzi ipv4, con SOCK stream indichiamo il tipo di socket ovvero TCP
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind assegna un ip e un numero di porta alla socket
        self.__s.bind((ipAddress, port))
        # listen ascolta le connessioni in entrata
        self.__s.listen(5)

        self.__ipAddress, self.__port = self.__s.getsockname()

        # aggiorno il database
        DB_Street = self.__db.upsertStreet(
            name=name, ip_address=f"{self.__ipAddress}:{self.__port}", length=lenght)

        if DB_Street is None:
            raise Exception("Street save on DB error")

        # l'id della strada viene generato dal db
        self.__id = DB_Street.id

        self.__connectedClient = {}

        self.__lenght = lenght  # metri
        self.__maxSpeed = maxSpeed  # limite massimo che si può raggiungere nella strada

        # creo i segnali nella strada
        self.__signals = self.__createSignals(
            signals_quantity, 20, 5)

    def __createSignals(self, signals_quantity: list, step: int, time_semaphore: int):
        """questa funzione permette di creare i segnali nella strada

        Args:
            signals_quantity (list): lista di tuple contente nome del segnale e quantità
            step (int): offeset per calcolo posizioni segnali
            time_semaphore (int): durata semaforo

        Returns:
            [type]: [description]
        """

        street_signal = list()
        stop = segnali.Stop()

        # limito sin da subito a non superare il limite massimo della strada
        street_signal.append((segnali.SpeedLimit(self.__maxSpeed, True), 20))

        # signals_ quantiti è una lista di tuple (nome segnale, quantità)
        for i in signals_quantity:
            for count in range(i[1]):
                while True:
                    # la posizione del segnale viene scelta randomicamente. Il parametro step è un offset
                    position = randrange(50, self.__lenght, step)
                    # controlliamo che non ci siano altri segnali presenti alla posizione calcolata, inoltre ci accertiamo che il segnale non venga posizionato vicino lo stop di fine strada
                    if(position not in (j[1] for j in street_signal) and position < (self.__lenght - stop.getDelta())):
                        break

                if (i[0] == "speed_limit"):
                    street_signal.append(
                        (segnali.SpeedLimit(self.__maxSpeed), position))

                if (i[0] == "semaphore"):
                    # se il segnale è un semaforo runniamo il thread semaforo
                    street_signal.append(
                        (segnali.Semaforo(time_semaphore), position))
                    street_signal[-1][0].start()

                print(
                    "Il segnale ", street_signal[-1][0].getName(), "è nella posizione ", position)

        # alla lista contenente tutti i segnali presenti nella strada aggiungiamo uno stop di fine strada
        street_signal.append((stop, self.__lenght))
        return street_signal

    def __findSignal(self, client_position: float):
        """questa funzione, data in input la posizione del client, controlla se nelle vicinanze esistono segnali ed eventualmente restituisce nome e posizione del segnale

        Args:
            client_position (float): posizione del client nella strada

        Returns:
            [type]: nome del segnale e posizione del segnale
        """

        # signal[0] è il segnale, signal[1] è la sua posizione nella strada
        if client_position >= self.__lenght:
            stop = self.__signals[-1]
            # ogni entry di signals è una tupla
            return stop[0], stop[1]

        for signal in self.__signals:
            # ogni segnale ha un delta, cioè un intervallo entro il quale deve essere segnalato, quindi controlliamo che la sottrazione tra il segnale e la posizione del client sia minore del delta
            if ((signal[1] - client_position <= signal[0].delta) and (signal[1] - client_position > 0)):
                return signal[0], signal[1]
        return None, None

    def __checkAuth(self, car_ip: str, car_id: str = None, token_client: str = None):
        """questa funzione serve a verificare che il client sia già autenticato

        Args:
            car_ip (str): indirizzo ip del client
            car_id (str, optional): targa della macchina. Defaults to None.
            token_client (str, optional): token del client . Defaults to None.

        Raises:
            Exception: [description]

        Returns:
            [type]: [description]
        """

        # se la targa della macchina è nulla viene generata una eccezione
        if car_id is None:
            raise Exception("Targa passata non valida.")

        if token_client is None:
            # il token viene generato la prima volta, nel momento il cui il client è autenticato, nel db viene aggiornata la route, cioè associamo una certa route ad un client
            # andiamo a recuperare tutte le route relative al client che non sono state completate, cioè dove il client non è arrivato a destinazione
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
        # stiamo supponendo che ovviamente il client si trova all'istante di tempo t sempre associato ad una sola strada
        DB_Route = DB_Route[0]
        # current index ci informa in quale "punto" della route si trova attualmente la macchina
        current_index = DB_Route.current_index

        len_route_list = len(DB_Route.route_list)
        if current_index >= 0 and current_index < len_route_list and DB_Route.route_list[current_index] == self.__id and DB_Route.current_street_position < self.__lenght:
            #  è già autenticato quindi aggiorniamo la route
            self.__db.upsertRoute(
                car_id, car_ip, connected=True, id=DB_Route.id)
            return DB_Route

        if current_index + 1 >= len_route_list or DB_Route.route_list[current_index + 1] != self.__id:
            # gli id delle strade partono da 1 mentre current_index da 0
            raise Exception(
                "Non sei autorizzato, Token non valido per questa strada")

        # ho autenticato l'utente e aggiorno la route
        self.__db.upsertRoute(car_id, car_ip, current_index=(
            current_index + 1), current_street_position=0, connected=True, id=DB_Route.id)

        return DB_Route

    def __comeBackAction(self, car_id: str, car_ip: str, client_speed: int, DB_Route, client_position: float = None):
        """questa funzione si occupa di inviare i comandi al client

        Args:
            car_id (str): targa del client
            car_ip (str): ip del client
            client_speed (int): velocità corrente del client
            DB_Route ([type]): contiene tutte le informazioni sulla route del client
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
            # se il client ci passa una posizione maggiore di quella presente nel db allora dobbiamo aggiornarla nel db
            self.__db.upsertRoute(
                car_id, car_ip, current_street_position=client_position, id=DB_Route.id)

        for clients in self.__connectedClient:
            if clients == car_id:
                continue
            # connectedClient contiene tutti i client connessi, è un dizionario con targa e posizione
            position_next = self.__connectedClient[clients]
            # tra un  client ed un altro deve esserci un offset di 30 metri
            if position_next > client_position and position_next - client_position <= 30:
                action = {
                    "signal": "auto",
                    "action": "fermati",
                    "distance": position_next - client_position,
                    "speed_limit": None
                }
                return action, client_position, f"Fra {action['distance']:.2f}m c'è una macchina, l'azione che devi eseguire e' {action['action']}."

        signal, signal_position = self.__findSignal(client_position)
        if signal is None:
            return None, client_position, "Niente in strada, vai come una scheggia!!"

        name_signal = signal.getName()
        distance = signal_position - client_position

        if name_signal == "stop" and distance < 1:
            # assumendo che ogni strada finisce con uno stop, se vale la condizione posta sopra il percorso è finito
            if DB_Route.current_index >= len(DB_Route.route_list)-1:
                # quindi aggiorniamo il db
                self.__db.upsertRoute(
                    car_id, car_ip, finished_at=datetime.now(), id=DB_Route.id)
                return {"action": "end"}, client_position, f"Congratulazioni sei arrivato a destinazione"
            # individuiamo la prossima strada da percorrere

            nextStreet = self.__db.getStreets(
                DB_Route.route_list[DB_Route.current_index + 1])[0]
            # individuiamo l'ip e la porta della prossima strada
            host, port = nextStreet.getIpAddress()

            if not host:
                raise Exception("Errore recupero indirizzo strada successiva")

            # viene creato il token da restituire al client per autenticarsi in un'altra strada
            token = Auth.create_token(
                DB_Route.id, nextStreet.id)

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

    def __manageCar(self, client, client_address):
        """funzione per gestire il client 
        Args:
            client ([type]): 
            client_address ([type]): ip del client
        """
        car_ip = f"{client_address[0]}:{client_address[1]}"

        try:
            while True:
                # recv è bloccante, va avanti solo se riceve data
                data = client.recv(1024).decode()
                # data è json, quindi viene fatto il decode
                data_decoded = json.loads(data)
                car_id = data_decoded['targa'] if 'targa' in data_decoded else None

                access_token = data_decoded['access_token'] if 'access_token' in data_decoded else None

                DB_Route = self.__checkAuth(car_ip, car_id, access_token)

                # qui siamo autenticati
                if 'position' in data_decoded:
                    pos = data_decoded['position']
                    speed = data_decoded['speed'] if 'speed' in data_decoded else None

                    # comeBackAction restituisce le azioni da fare, dati in ingresso i dati del client
                    action, position, message = self.__comeBackAction(
                        car_id, car_ip, speed, client_position=pos, DB_Route=DB_Route)

                    self.__connectedClient[car_id] = position
                    client.send(json.dumps({
                        "status": "success",
                        "message": message,
                        "action": action,
                        "position": position
                    }).encode())
                else:
                    if access_token is not None:
                        # in questo caso è la prima volta che il client entra nella strada
                        client.send(json.dumps({
                            "status": "success",
                            "message": "Welcome to the Server"
                        }).encode())

        except socket.error:
            print("Errore: Client disconnesso - forse è morto")
        except Exception as e:
            client.send(json.dumps({
                "status": "error", "message": str(e)
            }).encode())

        # locals() restituisce tutte le variabili locali che sono state istanziate
        if 'car_id' in locals() and car_id in self.__connectedClient:
            # con del eliminiamo il car_id che si è disconnesso
            del self.__connectedClient[car_id]
            if 'DB_Route' in locals():
                self.__db.upsertRoute(
                    car_id, car_ip, connected=False, id=DB_Route.id)

        client.close()

    def run(self):
        """funzione per mettere in run il server strada
        """

        print(f"Street is listening on {self.__ipAddress}:{self.__port}")
        while True:
            client, client_address = self.__s.accept()
            print(
                f'Connesso con la macchina: {client_address[0]}:{client_address[1]}')
            print(
                f'Macchine attualmente connesse: {len(self.__connectedClient) + 1 }')

            t1 = Thread(target=self.__manageCar,
                        args=(client, client_address))
            t1.start()

        self.__s.close()


def arg_tuple_parse(arg_list):
    """Funzione per fare il Parse  di tuple per argsparse 

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

    min_street_lenght = 100
    min_speed = 50
    try:
        while True:
            if((args.st_lenght > min_street_lenght) or (args.speed < min_speed)):
                street = Street(args.name, args.speed, args.st_lenght,
                                arg_tuple_parse(args.sig_type), args.ip_address, args.port)

                street.run()
            else:
                print("Dati inseriti non sono corretti")
            time.sleep(1)
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
