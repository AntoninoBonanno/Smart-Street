import segnali.segnale


class Strada:
    def __init__(self, street_lenght, ip_address, signal):
        self.lenght_street = street_lenght
        self.ip_address = ip_address
        self.init_point = 0  # per il sistema di riferimento
        self.signal = signal  # tuple (segnale,posizione)
        for i in self.signal:
            print(i[0].getName())

            if i[0].getName() == "semaphore":
                i[0].run()

    def get_lenght(self):
        return self.lenght_street

    def get_ip(self):
        return self.ip_address

    def get_signal(self):
        signal_street = list()
        street_dict = dict()
        for i in self.signal:
            street_dict.clear()
            street_dict['name'] = i[0].getName()
            street_dict['position'] = i[1]
            signal_street.append(street_dict.copy())

        return signal_street

    def find_signal(self, position, client_position, client_speed):
        for i in self.signal:
            if ((i[1] - client_position < i[0].delta) and (i[1] - client_position > 0)):
                if(i[0].getName() == "Speed Limit"):
                    return i[0].getAction(client_speed), i[0].getName(), i[0].getSpeed()
                return i[0].getAction(client_speed), i[0].getName()
