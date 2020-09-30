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
        """
        - name: nome del segnale
        - id_signal: id univoco 
        - action: azione associata al segnale 
        - delta: quanti metri prima avvisare il client della presenza del segnale)
        """
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
        """
        Stop eredita attributi e metodi da Segnale
        """
        super().__init__()
        self.delta = 100  # metri
        self.name = "stop"

    def getAction(self):
        return self.action[1]


class SpeedLimit(Segnale):

    def __init__(self, max_speed_road, force=False):
        """SpeedLimit eredita attributi e metodi da Segnale

        Args:
            max_speed_road ([type]): massima velocità raggiungibile
            force (bool, optional): forziamo il segnale ad assumere la massima velocità raggiungibile nella strada
        """        """
        
        """
        super().__init__()

        self.delta = 50  # metri
        self.name = "speed_limit"
        self.new_speed = randint(
            30, (max_speed_road)) if force == False else max_speed_road

    def getSpeed(self):
        return self.new_speed

    def getAction(self, client_speed):
        # override di getAction per definire le azioni di speed_limit
        if (client_speed <= self.new_speed):
            return self.action[0]
        return self.action[2]


class Semaforo(Thread, Segnale):

    def __init__(self, durata):
        """Semaforo eredita attributi e metodi dalla classe Segnale, ma è anche figlia di Thread. Gestiamo il semaforo come un thread

        Args:
            durata ([type]): durata in secondi del semaforo
        """
        Thread.__init__(self)
        Segnale.__init__(self)
        '''
        con multi-ereditarità super non funziona, quindi bisogna utilizzare il riferimento diretto al costruttore delle classi padre
        '''
        self.delta = 80  # metri
        self.status = "red"
        self.durata = durata  # in secondi
        self.name = "semaphore"

    def getAction(self):
        # override di getAction per definire le azioni associate al semaforo
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
