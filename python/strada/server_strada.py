import socket
import argparse
import json 
from _thread import *
import threading 
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))) + "/utility")
import Auth as auth
from strada import Strada as st

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip','--ip-address', type=str,default='127.0.0.1')
    parser.add_argument('-p','--port', type=int,default=8888)
    parser.add_argument('-l','--st-lenght', type=int,default=50)
    parser.add_argument('-s','--speed', type=int,default=50)
    parser.add_argument('-n','--name', type=str,default="road1")
    parser.add_argument('--st','--sig-type', nargs='+', type=tuple)
    args = parser.parse_args()
    return args


print_lock = threading.Lock() 
  
# thread function 
def threaded(c,street):

    while True: 
        # data received from client 
        data = c.recv(1024).decode()
        #data è json
        
        try:
            if(data is None ):
                raise Exception("Error connection not valid")
            data_decoded = json.loads(data)
            access_token=data_decoded['access_token']
            car_id=data_decoded['targa']
            
            if(access_token is not None):
                #come prelevo car ip?
                if(street.validate_token(access_token,car_id,car_ip)):
                    msg="AUTHENTICATED--->Please send me your information about position and speed"
                    c.send(msg.encode())
                else:
                    raise Exception("I can't accept the connection, please check your token. Bye")
                
            elif not car_id:
            
                if(street.check_auth(car_id)):
                    #qui siamo autenticati 
                    pos=data_decoded['posizione']
                    speed=data_decoded['speed']

                    if(not pos and not speed):
                        #diamo i comandi 
                        print("faccio qualcosa")
                    else:
                        msg="Please send me your information"
                        c.send(msg.encode())
                else:
                    raise Exception("Error connection not valid")

                    
        except:
            print("ERROR")
            print_lock.release() 
            break
        

    # connection closed 
    c.close() 
  
  
def ServerStreet(ip_address,port,st_lenght,speed,name,sig_type): 
    sig_type=[('stop',1),('speed_limit',2)]
    street=st(street_lenght=st_lenght,ip_address=ip_address+':'+port,signal_type=sig_type,name=name,max_speed_road=speed)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.bind((ip_address, port)) 
    print("socket binded to port", port) 
    # put the socket into listening mode 
    s.listen(5) 
    print("socket is listening") 
    # a forever loop until client wants to exit 
    while True: 
        # establish connection with client 
        c, addr = s.accept() 
        # lock acquired by client 
        print_lock.acquire() 
        print('Connected to :', addr[0], ':', addr[1]) 
        # Start a new thread and return its identifier 
        start_new_thread(threaded, (c,),street) 
    s.close() 
  
  
if __name__ == '__main__': 
    args=parse()
    ServerStreet(args.ip_address,args.port,args.st_lenght,args.speed,args.name,args.sig_type) 