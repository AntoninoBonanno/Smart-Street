# Street

The Street object is a Server that abstracts the road and contains all the useful functions to manage the behavior of clients along its path

Specifications:
- Accept a connection from the client, verifying the authentication from the DB
- Establishes a connection with the client, Stores the new position of the car on the DB (current road)
- Periodically stores the relative position (within the street) of the client
- It warns the car of the signals or the cars near it and therefore the action it must perform
- At the end of the road, it checks the DB to verify the path of the car and then provides the information to access the next road. If there are no subsequent roads, it indicates to the machine that it has arrived at its destination and confirms the arrival of the machine on the DB.


The Signale class is the "parent" class, from which all signals (stop, speed limit, semaphores) derive.

- *Stop*: marks the end of a road, related action: stop
- *SpeedLimit*: defines a new maximum allowed speed
- *Semaforo*: according to the red / yellow / green status the related actions are stop / slow down / speed up


## Execution

Run this command:

`> python python\Street\Street.py`

or you can specify:

`> python python\Street\Street.py -...`


## Authors

[Castagnolo Giulia](https://github.com/yuko95), [Bonanno Antonino](https://github.com/AntoninoBonanno)


