import segnali.segnale
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))) + "/utility")
from DatabaseHelper import Database


class Strada:
    def __init__(self, street_lenght:float, ip_address: str, signal:list,name:str):
        self.__lenght_street = street_lenght
        self.__name=name
        self.__ip_address = ip_address
        self.__init_point = 0  # per il sistema di riferimento
        self.__signal = signal  # tuple (segnale,posizione)
        db_result=Database.upsertStreet(self.__name, self.__ip_address,self.__lenght_street)

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

    def find_signal(self, client_position: float, client_speed: float):
        for i in self.__signal:
            if ((i[1] - client_position < i[0].delta) and (i[1] - client_position > 0)):
                if(i[0].getName() == "Speed Limit"):
                    return i[0].getAction(client_speed), i[0].getName(), i[0].getSpeed()
                return i[0].getAction(client_speed), i[0].getName()



    '''
    funzione che riceve il token dal client, riceve il token e l'id del client. Dentro la funzione mi devo fare il decode del token,se non restituisce false
    posso andare a recuperare la street id e devo verificare che è la stessa mia. Con la route id mi faccio la get della route id e mi controllo car_id e car_ip

    '''
