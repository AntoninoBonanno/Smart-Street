import os
import sys
import json
import socket
import argparse
import threading
from _thread import *
from strada import Strada


def threaded(c, street):
    c.send(json.dumps({
        "status": "success",
        "message": "Welcome to the Server"
    }))

    while True:
        # data received from client
        data = c.recv(2048).decode()
        car_ip, port = c.getpeername()

        try:
            if data:  # se non invia niente il client significa che sta elaborando... se non invia dopo un tot di tempo chiudere la connessione
                data_decoded = json.loads(data)  # data è json

                access_token = data_decoded['access_token']
                car_id = data_decoded['targa']

                if not car_id:
                    c.send(json.dumps(
                        {"status": "error", "message": "Devi inviare la targa"}))
                    break  # chiudo il thread

                if(street.checkAuth(car_id, car_ip, access_token) == False):
                    c.send(json.dumps(
                        {"status": "error", "message": "Autenticazione fallita"}))
                    break  # chiudo il thread

                # qui siamo autenticati
                if data_decoded['speed']:
                    pos = data_decoded['posizione']
                    speed = data_decoded['speed']
                    # eh qui è da vedere
                    c.send(json.dumps({
                        "status": "success",
                        "message": "messaggio",
                        "actions": [{
                            "speed": "azione dello speed",
                            "position": 0
                        }]
                    }))
            else:
                timer = 1
        except Exception as e:
            print("ERROR")
            c.send(json.dumps({"status": "error", "message": str(e)}))
            break

    # connection closed
    c.close()


def ServerStreet(ip_address, port, st_lenght, speed, name, sig_type):

    sig_type = [('stop', 1), ('speed_limit', 2)]

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if(ip_address is None):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

    s.bind((ip_address, port))

    ip_address, port = s.getsockname()
    host_strada = ip_address + ':' + str(port)
    street = Strada(street_lenght=st_lenght, ip_address=host_strada,
                    signal_type=sig_type, name=name, max_speed_road=speed)
    print("socket binded to port", port)

    '''
    listen

    Abilita il socket a ricevere connessioni. backlog
    specifica quanti tentativi di connessione falliti
    tollerare prima di rifiutare nuove connessioni da uno
    specifico client. Se assente, viene scelto un valore
    automaticamente.
    '''
    s.listen(5)

    print("socket is listening")
    # a forever loop until client wants to exit
    ThreadCount = 0
    while True:
        # establish connection with client
        c, addr = s.accept()
        print('Connected to :', addr[0], ':', addr[1])
        # Start a new thread and return its identifier
        start_new_thread(threaded, (c, street))
        ThreadCount += 1
        print('Thread Number: ' + str(ThreadCount))

    s.close()


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

    ServerStreet(args.ip_address, args.port, args.st_lenght,
                 args.speed, args.name, args.sig_type)
