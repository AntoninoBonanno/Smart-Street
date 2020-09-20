import socket
import thread
import signal
import sys


def on_new_client(clientsocket, addr):
    while True:
        msg = clientsocket.recv(1024)
        # do some checks and if msg == someWeirdSignal: break:
        print(addr, ' >> ', msg)
        msg = 'SERVER >> prova'
        # Maybe some code to compute the last digit of PI, play game or anything else can go here and when you are done.
        clientsocket.send(msg)
    clientsocket.close()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = socket.gethostname()  # Get local machine name
port = 50000                # Reserve a port for your service.

print('Server started!')
print('Waiting for clients...')

s.bind((host, port))        # Bind to the port
s.listen(5)                 # Now wait for client connection.

while True:
    c, addr = s.accept()
    thread.start_new_thread(on_new_client, (c, addr))
s.close()


def signal_handler(signal, frame):
    s.close()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
