import segnali 
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))) + "/utility")
from DatabaseHelper import Database
from random import randrange


class Strada:
    def __init__(self, street_lenght:float, ip_address: str, signal_type:list,name:str,max_speed_road:int):

        self.__lenght_street = street_lenght
        self.__name=name
        self.__max_speed_road=max_speed_road
        self.__ip_address = ip_address
        self.__init_point = 0  # per il sistema di riferimento
        self.__signal_type = signal_type  # tuple (segnale,posizione)
        self.__signal=self.create_signal(5,5,10)
        db=Database()
        db_result=db.upsertStreet(name=self.__name,ip_address= self.__ip_address,length=self.__lenght_street)

        if db_result is not None:
            self.__id=db_result.id #strada istanziata nel database
            self.__available=True
            for i in self.__signal:
                if i[0].getName() == "semaphore":
                    i[0].run()
        else:
            self.__available=False #mi dice se la strada è disponibile o no 
    
        
    def get_lenght(self):
        return self.__lenght_street
    def get_status(self):
        return self.__available

    def get_id(self):
        return self.__id

    def get_name(self):
        return self.__name

    def get_ip(self):
        return self.__ip_address

    def get_signal(self):
        signal_street = list()
        street_dict = dict()
        for i in self.__signal:
            street_dict.clear()
            street_dict['name'] = i[0].getName()
            street_dict['position'] = i[1]
            signal_street.append(street_dict.copy())

        return signal_street

    def find_signal(self, client_position: float, client_speed: int):
        for i in self.__signal:
            if ((i[1] - client_position < i[0].delta) and (i[1] - client_position > 0)):
                if(i[0].getName() == "speed_limit"):
                    return i[0].getAction(client_speed), i[0].getName(), i[0].getSpeed()
                return i[0].getAction(client_speed), i[0].getName()
    
    def create_signal(self,step,stop_dist,time_semaphore):
        street_signal=list()

        for i in self.__signal_type:
                for count in range(i[1]):
                    while True:
                        position=randrange(0,self.__lenght_street,step)
                        if(position not in (j[1] for  j in street_signal) and position<(self.__lenght_street-stop_dist) ):
                            break
                        
                    if (i[0]=="speed_limit"):
                        street_signal.append((segnali.SpeedLimit(self.__max_speed_road),position))
                    if (i[0]=="stop"):
                        street_signal.append((segnali.Stop(),position))
                    if (i[0]=="semaphore"):
                        street_signal.append((segnali.Semaforo(time_semaphore),position))

        street_signal.append((segnali.Stop(),self.__lenght_street)) #stop fine strada
        return street_signal
        
            
                




    '''
    funzione che riceve il token dal client, riceve il token e l'id del client. Dentro la funzione mi devo fare il decode del token,se non restituisce false
    posso andare a recuperare la street id e devo verificare che è la stessa mia. Con la route id mi faccio la get della route id e mi controllo car_id e car_ip

    '''
if __name__ == '__main__':
    signal_list=[('semaphore',1),('speed_limit',3)]
    strada1=Strada(100,"10.11.13.41:400",signal_list,"Bronte",100)
    print(strada1.get_signal())
    signal_list_2=[('stop',1),('speed_limit',3)]
    strada2=Strada(150,"10.10.13.41:400",signal_list,"Adrano",80)
    print(strada2.get_signal())

