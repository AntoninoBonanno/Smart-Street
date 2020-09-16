from threading import Thread
import time
from random import randint 
import base64
import os

class Segnale:
    def __init__(self):
        self.id_signal= base64.b64encode(os.urandom(6)).decode('ascii')
        self.delta=2
        self.action=["accelera","fermati","rallenta"]

    def getAction(self):
        return self.action[0]
    def getDelta(self):
        return self.delta
    def getId(self):
        return self.id_signal


class Stop(Segnale):
    
    def __init__(self):
        super().__init__()
        self.delta=10
    def getAction(self):
        return self.action[1]

class SpeedLimit(Segnale):
    
    def __init__(self,client_speed,max_speed_road):
        super().__init__()
     
        self.delta=10
        
        self.max_speed_road=max_speed_road
        self.new_speed=randint(30,(self.max_speed_road))
        self.client_speed=client_speed
    def getSpeed(self):
        return self.new_speed
    def getAction(self):
        if (self.client_speed<self.new_speed):
            return self.action[0]
        
        return self.action[2]
        

class Semaforo(Segnale,Thread):
    
    def __init__(self,durata):
        super().__init__()
        Thread.__init__(self)
        self.delta=8
        self.status="red"
        self.durata=durata
        
    def getAction(self):
        if self.status=="green":
            return self.action[0]
        if self.status=="red":
            return self.action[1]
        if self.status=="yellow":
            return self.action[2]

    def run(self):
        while True:
            self.status="red"
            time.sleep(self.durata)
            self.status="green"
            time.sleep(self.durata)
            self.status="yellow"
            time.sleep(self.durata)