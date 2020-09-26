import segnali
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))) + "/utility")
from DatabaseHelper import Database
from random import randrange
import Auth as auth
from datetime import datetime


class Strada:
    def __init__(self, street_lenght: int, ip_address: str, signal_type: list, name: str, max_speed_road: int):

        self.__lenght_street = street_lenght
        self.__name = name
        self.__max_speed_road = max_speed_road
        self.__ip_address = ip_address
        self.__init_point = 0  # per il sistema di riferimento
        self.__signal_type = signal_type  # tuple (segnale,posizione)
        self.__signal = self.create_signal(5, 5, 10)
        self.__db = Database()
        db_result = self.__db.upsertStreet(
            name=self.__name, ip_address=self.__ip_address, length=self.__lenght_street)

        if db_result is not None:
            self.__id = db_result.id  # strada istanziata nel database e restituzione del database
            self.__available = db_result.available
            for i in self.__signal:
                if i[0].getName() == "semaphore":
                    i[0].run()
        else:
            self.__id = None  # se l'id è none vuol dire che non è stato scritto sul db
            self.__available = False

    # forse è meglio rendere publici questi attributi e non appesantire la classe con i getter? da discutere
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

    def __find_signal(self, client_position: float, client_speed: int):
        for i in self.__signal:
            if ((i[1] - client_position < i[0].delta) and (i[1] - client_position > 0)):
                if(i[0].getName() == "speed_limit"):
                    return i[0].getAction(client_speed), i[0].getName(), i[0].getSpeed()
                return i[0].getAction(), i[0].getName(), None

    def create_signal(self, step: int, stop_dist: int, time_semaphore: int):
        street_signal = list()

        for i in self.__signal_type:
            for count in range(i[1]):
                while True:
                    position = randrange(0, self.__lenght_street, step)
                    if(position not in (j[1] for j in street_signal) and position < (self.__lenght_street - stop_dist)):
                        break

                if (i[0] == "speed_limit"):
                    street_signal.append(
                        (segnali.SpeedLimit(self.__max_speed_road), position))
                if (i[0] == "stop"):
                    street_signal.append((segnali.Stop(), position))
                if (i[0] == "semaphore"):
                    street_signal.append(
                        (segnali.Semaforo(time_semaphore), position))

        # stop fine strada
        street_signal.append((segnali.Stop(), self.__lenght_street))
        return street_signal
    #accetto in input una velocità e un tempo, calcola il tempo passato tra quello originale e il corrente. Mi devo recuperare
    #la vecchia posizione dal db e mi calcolo quella nuova. Nel momento in cui ho la posizone nuova devo andare a salvare sul db 

    def come_back_action(self, speed_client: int, timestamp: datetime,car_id:str,car_ip:str,db_route_result):

        #dobbiamo controllare se è autenticato
        #sto supponendo che la targa sia corretta 

        new_date_time=(datetime.now()-timestamp).seconds
       
        #stiamo considerando che la velocità ci viene passata in km/h mentre la posizione è in m e il tempo è in s
        if(db_route_result is not None):
            old_position=db_route_result.current_street_position
            new_position=((speed_client/3.6)*new_date_time)+old_position
            if(new_position!= old_position):
                self.__db.upsertRoute(car_id=car_id,car_ip=car_ip,route_list=db_route_result.route_list,current_index=db_route_result.current_index,current_street_position=new_position)
        
            return self.__find_signal(new_position,speed_client),new_position
        
        raise Exception("Errore, dati non corretti o vuoti")
    





        


    # supponiamo che qui arriva il token del client decodificato a questo punto lo dobbiamo controllare per vedere se è valido
    # MODIFICHE NINO

    def checkAuth(self, car_id: str, car_ip: str, token_client: str = None):
        if token_client is not None:
            token_client = auth.decode_token(token_client)
            if token_client is None:
                return False  # token scaduto o non valido

            # il token decodificato è un dizionario
            street_id_token = token_client['street_id']
            route_id_token = token_client['route_id']

            if street_id_token != self.__id:
                return False  # throw exception?

            db_route_result = self.__db.getRoutes(route_id_token)
            if (not db_route_result) or (db_route_result[0].car_id != car_id):
                return False  # throw exception?

            current_index = db_route_result[0].current_index
            if(db_route_result[0].route_list[current_index + 1] != self.__id):
                return False  # throw exception? se restituisce false qui significa che la macchina sta accedendo ad una strada che è diversa dalla sequenza

            # ho autenticato l'utente e aggiorno la route indicando
            self.__db.upsertRoute(car_id, car_ip, None,
                                  current_index + 1, 0, route_id_token)
            return True

        db_result_route = self.__db.checkRoute(car_id)
        if db_result_route is None:
            return False

        # non mi convince, forse bisogna inserire un'altro parametro nel db per capire se questa strada è l'indice giusto.... discuterne
        if(db_result_route.route_list[db_result_route.current_index] == self.__id):
            return True  # autenticated in this road
        return False


if __name__ == '__main__':
    # signal_list=[('semaphore',1),('speed_limit',3)]
    # strada1=Strada(100,"10.11.13.41:400",signal_list,"Bronte",100)
    # print(strada1.get_signal())
    signal_list_2 = [('stop', 1), ('speed_limit', 3)]
    strada2 = Strada(150, "10.10.13.41:400", signal_list_2, "Adrano", 80)
    if(strada2.get_status()):
        print(strada2.get_signal())
        print(strada2.find_signal(20, 80))
