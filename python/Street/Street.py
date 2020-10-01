import os
import sys

import time
import json
import socket
import argparse
import threading
from random import randrange
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))) + "/utility")

import Auth  # contiene funzioni per gestire l'autenticazione
import Segnali  # contiene le classi con i segnali
# contiene funzioni per gestire il db
from DatabaseHelper import Database, DB_Route

running = True


class Street:

    def __init__(self, name: str, maxSpeed: int, lenght: int, signals_quantity: list, ipAddress: str = None, port: int = 0):
        """
        Funzione di inizializzazione dell'oggetto strada

        Args:
            name (str): nome della strada
            maxSpeed (int): massima velocità raggiungibile nella strada
            lenght (int): lunghezza della strada espressa in metri
            signals_quantity (list): lista di tuple contente nome del segnale e quantità
            ipAddress (str, optional): indirizzo ip della strada, default None
            port (int, optional): porta. Defaults to 0.

        Raises:
            Exception: Errore inizializzazione
        """
        self.__db = Database()  # istauro la connessione con il db

        self.name = name
        self.lenght = lenght  # metri
        self.ipAddress = f"{ipAddress}:{port}"
        self.maxSpeed = maxSpeed  # limite massimo che si può raggiungere nella strada

        # aggiorno il database
        DB_Street = self.__db.upsertStreet(
            name=self.name, ip_address=self.ipAddress, length=self.lenght)

        if DB_Street is None:
            raise Exception("Errore salvataggio strada sul DB")

        # l'id della strada viene generato dal db
        self.__id = DB_Street.id

        # connectedClient contiene tutti i client connessi, è un dizionario con targa e posizione
        self.connectedClient = {}
        self.__lock = threading.Lock()

        # creo i segnali nella strada
        self.__signals = self.__createSignals(signals_quantity, 50, 5)

    def __createSignals(self, signals_quantity: list, step: int, time_semaphore: int) -> list:
        """
        Questa funzione permette di creare i segnali nella strada

        Args:
            signals_quantity (list): lista di tuple contente nome del segnale e quantità
            step (int): offeset per calcolo posizioni segnali
            time_semaphore (int): durata semaforo

        Returns:
            list: Lista dei segnali generati
        """

        self.__db.deleteSignals(self.__id)

        street_signal = list()
        stop = Segnali.Stop()

        # limito sin da subito a non superare il limite massimo della strada
        sl = Segnali.SpeedLimit(self.maxSpeed, True)
        street_signal.append((sl, 20))
        self.__db.upsertSignal(self.__id, sl.getName(), 20, sl.getSpeed())

        # signals_quantity è una lista di tuple (nome segnale, quantità)
        for i in signals_quantity:
            for count in range(i[1]):
                while True:
                    # la posizione del segnale viene scelta randomicamente. Il parametro step è un offset
                    position = randrange(50, self.lenght, step)
                    # controlliamo che non ci siano altri segnali presenti alla posizione calcolata, inoltre ci accertiamo che il segnale non venga posizionato vicino lo stop di fine strada
                    if(position not in (j[1] for j in street_signal) and position < (self.lenght - stop.getDelta())):
                        break

                if (i[0] == "speed_limit"):
                    sl = Segnali.SpeedLimit(self.maxSpeed)
                    street_signal.append((sl, position))

                    self.__db.upsertSignal(
                        self.__id, sl.getName(), position, sl.getSpeed())

                if (i[0] == "semaphore"):
                    # se il segnale è un semaforo runniamo il thread semaforo
                    sm = Segnali.Semaforo(time_semaphore)
                    street_signal.append((sm, position))
                    street_signal[-1][0].start()

                    self.__db.upsertSignal(self.__id, sm.getName(), position)

                print(
                    "Il segnale ", street_signal[-1][0].getName(), "è nella posizione ", position)

        # alla lista contenente tutti i segnali presenti nella strada aggiungiamo uno stop di fine strada
        street_signal.append((stop, self.lenght))
        self.__db.upsertSignal(self.__id, stop.getName(),
                               self.lenght, stop.getAction())
        return street_signal

    def __findSignal(self, client_position: float) -> tuple:
        """
        Questa funzione, data in input la posizione del client, controlla se nelle vicinanze esistono segnali ed eventualmente restituisce nome e posizione del segnale

        Args:
            client_position (float): posizione del client nella strada

        Returns:
            tuple: nome del segnale e posizione del segnale o None, None
        """

        # signal[0] è il segnale, signal[1] è la sua posizione nella strada
        # Se il client ha superato la lunghezza della strada restituisco lo stop
        if client_position >= self.lenght:
            stop = self.__signals[-1]
            # ogni entry di signals è una tupla
            return stop[0], stop[1]

        for signal in self.__signals:
            # ogni segnale ha un delta, cioè un intervallo entro il quale deve essere segnalato, quindi controlliamo che la sottrazione tra il segnale e la posizione del client sia minore del delta
            if ((signal[1] - client_position <= signal[0].delta) and (signal[1] - client_position > 0)):
                return signal[0], signal[1]
        return None, None

    def __checkAuth(self, car_ip: str, car_id: str = None, token_client: str = None) -> DB_Route:
        """
        Questa funzione serve a verificare che il client sia già autenticato, eventualmente viene autenticato

        Args:
            car_ip (str): indirizzo ip del client
            car_id (str, optional): targa della macchina. Defaults to None.
            token_client (str, optional): token del client . Defaults to None.

        Raises:
            Exception: Autenticazione fallita

        Returns:
            DB_Route: La route del client
        """

        # se la targa della macchina è nulla viene generata una eccezione
        if car_id is None:
            raise Exception("Targa passata non valida.")

        if token_client is None:
            # sto verificando se il client ha già effetuato l'autenticazione in questa strada

            # il token viene generato la prima volta, nel momento il cui il client è autenticato, nel db viene aggiornata la route, cioè associamo una certa route ad un client
            # andiamo a recuperare tutte le route relative al client che non sono state completate, cioè dove il client non è arrivato a destinazione, esisterà una sola route di questo tipo
            self.__lock.acquire()
            DB_Route = self.__db.getRoutes(car_id=car_id, finished=False)
            self.__lock.release()

            if not DB_Route or DB_Route[0].car_ip != car_ip:
                raise Exception(
                    "Non sei autorizzato, richiedi un nuovo token al punto di accesso")

            # stiamo supponendo che ovviamente il client si trova all'istante di tempo t sempre associato ad una sola strada
            DB_Route = DB_Route[0]
            current_index = DB_Route.current_index
            # Se la strada indicata nella route non è quella corrente genero un eccezione
            if current_index < 0 or current_index >= len(DB_Route.route_list) or DB_Route.route_list[current_index] != self.__id:
                raise Exception(
                    "Non sei autorizzato ad accedere in questa strada.")

            return DB_Route

        # se mi viene passato un token
        token_client = Auth.decode_token(token_client)
        if token_client is None:
            raise Exception(
                "Token scaduto o non valido, richiedi un nuovo token al punto di accesso")

        # il token decodificato è un dizionario
        street_id_token = token_client['street_id']
        route_id_token = token_client['route_id']

        # se l'id nel token è diverso dall'id della strada genero un eccezione
        if street_id_token != self.__id:
            raise Exception(
                "Non sei autorizzato, Token non valido per questa strada")

        # recupero la route e la verifico
        self.__lock.acquire()
        DB_Route = self.__db.getRoutes(route_id_token)
        self.__lock.release()

        if not DB_Route or DB_Route[0].car_id != car_id:
            raise Exception(
                "Non sei autorizzato, il token inviato non corrisponde alla tua targa")
        # stiamo supponendo che ovviamente il client si trova all'istante di tempo t sempre associato ad una sola strada
        DB_Route = DB_Route[0]
        # current index ci informa in quale "punto" della route (strada) si trova attualmente la macchina
        current_index = DB_Route.current_index

        len_route_list = len(DB_Route.route_list)
        if current_index >= 0 and current_index < len_route_list and DB_Route.route_list[current_index] == self.__id and DB_Route.current_street_position < self.lenght:
            #  è già autenticato quindi aggiorniamo la route
            self.__lock.acquire()
            self.__db.upsertRoute(
                car_id, car_ip, connected=True, id=DB_Route.id)
            self.__lock.release()
            return DB_Route

        # se non era già autenticato, controllo che la strada successiva della route è quella corrente
        if current_index + 1 >= len_route_list or DB_Route.route_list[current_index + 1] != self.__id:
            raise Exception(
                "Non sei autorizzato, Token non valido per questa strada")

        # ho autenticato l'utente e aggiorno la route
        self.__lock.acquire()
        self.__db.upsertRoute(car_id, car_ip, current_index=(
            current_index + 1), current_street_position=0, connected=True, id=DB_Route.id)
        self.__lock.release()

        return DB_Route

    def __comeBackAction(self, car_id: str, car_ip: str, client_speed: int, route: DB_Route, client_position: float = None) -> tuple:
        """
        Questa funzione si occupa di inviare i comandi al client

        Args:
            car_id (str): targa del client
            car_ip (str): ip del client
            client_speed (int): velocità corrente del client
            route (DB_Route): contiene tutte le informazioni sulla route del client
            client_position (float, optional): posizione corrente del client. Defaults to None.

        Raises:
            Exception: Errori generici

        Returns:
            tuple: azione da eseguire, posizione, messaggio
        """

        if route is None:
            raise Exception("Errore, dati non corretti o vuoti")

        old_position = route.current_street_position
        if(client_position <= old_position):
            client_position = old_position
        else:
            # se il client ci passa una posizione maggiore di quella presente nel db allora dobbiamo aggiornarla nel db
            self.__lock.acquire()
            self.__db.upsertRoute(
                car_id, car_ip, current_street_position=client_position, id=route.id)
            self.__lock.release()

        for clients in self.connectedClient:
            if clients == car_id:
                continue
            # connectedClient contiene tutti i client connessi, è un dizionario con targa e posizione
            position_next = self.connectedClient[clients]
            # tra un  client ed un altro deve esserci un offset di 30 metri
            if position_next > client_position and position_next - client_position <= 30:

                # comunico l'azione di fermarsi perchè c'è un auto di fronte
                action = {
                    "signal": "auto",
                    "action": "fermati",
                    "distance": position_next - client_position,
                    "speed_limit": None
                }
                return action, client_position, f"Fra {action['distance']:.2f}m c'e' una macchina, l'azione che devi eseguire e' {action['action']}."

        # recupero i segnali prossimi alla client position
        signal, signal_position = self.__findSignal(client_position)
        if signal is None:
            return None, client_position, "Niente in strada, vai come una scheggia!!"

        name_signal = signal.getName()
        distance = signal_position - client_position

        if name_signal == "stop" and distance < 1:
            # assumiamo che ogni strada finisce con uno stop, se vale la condizione posta sopra la strada è finita
            if route.current_index >= len(route.route_list) - 1:
                # se non ci sono più strade successive, il percorso è finito
                self.__lock.acquire()
                self.__db.upsertRoute(
                    car_id, car_ip, finished_at=datetime.now(), id=route.id)
                self.__lock.release()
                return {"action": "end"}, client_position, f"Congratulazioni sei arrivato a destinazione"

            # individuiamo la prossima strada da percorrere
            self.__lock.acquire()
            nextStreet = self.__db.getStreets(
                route.route_list[route.current_index + 1])[0]
            self.__lock.release()
            # individuiamo l'ip e la porta della prossima strada
            host, port = nextStreet.getIpAddress()

            if not host:
                raise Exception("Errore recupero indirizzo strada successiva")

            # viene creato il token da restituire al client per autenticarsi in un'altra strada
            token = Auth.create_token(
                route.id, nextStreet.id)

            action = {
                "action": "next",
                "host": host,
                "port": port,
                "access_token": token.decode('UTF-8')
            }
            return action, client_position, f"Procedi con l'host e port indicato per poter raggiungere {nextStreet.name}"

        # restituisco l'azione da eseguire per il segnale vicino
        action = {
            "signal": name_signal,
            "action": signal.getAction() if name_signal != "speed_limit" else signal.getAction(client_speed),
            "distance": distance,
            "speed_limit": signal.getSpeed() if name_signal == "speed_limit" else None
        }

        limit = action['speed_limit'] if name_signal == "speed_limit" else 'prescrizione precedente'
        return action, client_position, (f"Fra {distance:.2f}m incontri il segnale {name_signal}, l'azione che devi eseguire e' {action['action']}. Limite: {limit}")

    def manageCar(self, client, client_address):
        """
        Funzione per gestire il client

        Args:
            client: connessione socket
            client_address: ip e porta del client
        """
        car_ip = f"{client_address[0]}:{client_address[1]}"

        try:
            while running:
                # recv è bloccante, va avanti solo se riceve data
                data = client.recv(1024).decode()
                # data è json, quindi viene fatto il decode
                data_decoded = json.loads(data)
                car_id = data_decoded['targa'] if 'targa' in data_decoded else None
                access_token = data_decoded['access_token'] if 'access_token' in data_decoded else None

                # verifico l'autenticazione
                route = self.__checkAuth(car_ip, car_id, access_token)

                # qui siamo autenticati
                if 'position' in data_decoded:
                    pos = data_decoded['position']
                    speed = data_decoded['speed'] if 'speed' in data_decoded else None

                    # comeBackAction restituisce le azioni da fare, dati in ingresso i dati del client
                    action, position, message = self.__comeBackAction(
                        car_id, car_ip, speed, client_position=pos, route=route)

                    # memorizzo la nuova posizione per il client corrente
                    self.connectedClient[car_id] = position
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
                            "message": "Benvenuto nella strada " + self.name
                        }).encode())

        except socket.error:
            print("Errore: Client disconnesso - forse è morto")
        except Exception as e:
            client.send(json.dumps({
                "status": "error", "message": str(e)
            }).encode())

        # locals() restituisce tutte le variabili locali che sono state istanziate
        if 'car_id' in locals() and car_id in self.connectedClient:
            # con del eliminiamo il car_id che si è disconnesso
            del self.connectedClient[car_id]
            if 'route' in locals():  # aggiorno il db
                self.__lock.acquire()
                self.__db.upsertRoute(
                    car_id, car_ip, connected=False, id=route.id)
                self.__lock.release()

        try:
            client.shutdown(socket.SHUT_RDWR)
            client.close()  # scollego il client
        except socket.error:
            print("Client disconnesso")

    def disable(self):
        self.__db.upsertStreet(
            name=self.name, ip_address=self.ipAddress, length=self.lenght, available=False, id=self.__id)


def arg_tuple_parse(arg_list):
    """
    Funzione per fare il Parse di tuple per argsparse

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
    -st semaphore,2 speed_limit,3    --> lista con nome segnali che devono essere presenti sulla strada e numero.

    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', type=str,
                        default=None, help="Indirizzo ip della strada")
    parser.add_argument('-p', '--port', type=int, default=8000,
                        help="Porta della strada, default 8000")
    parser.add_argument('-l', '--lenght', type=int,
                        default=1000, help="Lunghezza strada, default 1000, minimo 100 [metri]")
    parser.add_argument('-s', '--speed', type=int, default=120,
                        help="Velcità massima percorribile sulla strada, default 120, minimo 50 [km/h]")
    parser.add_argument('-n', '--name', type=str,
                        default="road1", help="Nome della strada")
    parser.add_argument('-st', '--sig-type', nargs='+',
                        type=str, help="Nome segnali e quantità, default 'semaphore,2 speed_limit,3'")
    args = parser.parse_args()

    min_street_lenght = 100
    min_speed = 50

    if((args.lenght <= min_street_lenght) or (args.speed <= min_speed)):
        print("Dati inseriti non sono corretti")
        sys.exit(0)

    print("Inizializzazione della strada...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    ipAddress = args.host
    if ipAddress is None:
        # se l'indirizzo ip è nullo l'indirizzo ip della strada diventa quello del localhost
        hostname = socket.gethostname()
        ipAddress = socket.gethostbyname(hostname)

    s.settimeout(0.2)
    s.bind((ipAddress, args.port))
    s.listen(5)

    ipAddress, port = s.getsockname()
    street = Street(args.name, args.speed, args.lenght,
                    arg_tuple_parse(args.sig_type), ipAddress, port)

    print(f"La strada è in ascolto {ipAddress}:{port}")

    while running:
        try:
            (conn, client_address) = s.accept()
            print(
                f'Connesso con la macchina: {client_address[0]}:{client_address[1]}')
            print(
                f'Macchine attualmente connesse: {len(street.connectedClient) + 1 }')

            t = threading.Thread(target=street.manageCar,
                                 args=(conn, client_address))
            t.daemon = True
            t.start()
        except socket.timeout:
            pass
        except KeyboardInterrupt:
            print("Chiusura della socket")
            running = False  # Kill the threads

    street.disable()
    s.shutdown(socket.SHUT_WR)
    s.close()
