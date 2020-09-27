from threading import Thread
import time
from random import randint
import base64
import os

'''
Segnale è la classe "padre" da cui derivano tutti i segnali ( stop, speed limit ecc. sono specializzazioni di Segnale)
Ogni segnale ha:
 - nome
 - id
 - azione (che deve effettuare il client in prossimità del segnale)
 - delta (ci indica quanti metri prima avvisare il client della presenza del segnale)

Per ogni tipologia di segnale viene definita l'opportuna azione, il nome ecc.
'''


class Segnale:
    def __init__(self):
        self.id_signal = base64.b64encode(os.urandom(6)).decode('ascii')
        self.delta = 2
        self.name = "Generic"
        self.action = ["accelera", "fermati", "rallenta"]

    def getAction(self):
        return self.action[0]

    def getDelta(self):
        return self.delta

    def getId(self):
        return self.id_signal

    def getName(self):
        return self.name


class Stop(Segnale):

    def __init__(self):
        super().__init__()
        self.delta = 50  # metri
        self.name = "stop"

    def getAction(self):
        return self.action[1]


class SpeedLimit(Segnale):

    def __init__(self, max_speed_road, force=False):
        super().__init__()

        self.delta = 20  # metri
        self.name = "speed_limit"
        self.new_speed = randint(
            30, (max_speed_road)) if force == False else max_speed_road

    def getSpeed(self):
        return self.new_speed

    def getAction(self, client_speed):
        if (client_speed <= self.new_speed):
            return self.action[0]
        return self.action[2]


'''
Il semaforo è gestito con un thread
'''


class Semaforo(Thread, Segnale):

    def __init__(self, durata):
        Thread.__init__(self)
        Segnale.__init__(self)
        '''
        con multi-ereditarità super non funziona, quindi bisogna utilizzare il riferimento diretto al costruttore delle classi padre
        '''
        self.delta = 30  # metri
        self.status = "red"
        self.durata = durata
        self.name = "semaphore"

    def getAction(self):
        if self.status == "green":
            return self.action[0]
        if self.status == "red":
            return self.action[1]
        if self.status == "yellow":
            return self.action[2]

    def run(self):
        while True:
            self.status = "red"
            time.sleep(self.durata)
            self.status = "green"
            time.sleep(self.durata)
            self.status = "yellow"
            time.sleep(self.durata)

    # per avviare il thread dal main usare nomethread.start()
