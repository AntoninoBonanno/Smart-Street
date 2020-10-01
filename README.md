# Smart-Street

The goal of the project is to create an application that simulates the behavior of an intelligent road. The basic idea is to have roads traveled by cars, the cars communicate and interact with the road, the latter gives the cars the actions to be carried out.

For the development of the project the following languages were used:
- [Street server](https://github.com/AntoninoBonanno/Smart-Street/tree/master/python/Street): python
- [Client](https://github.com/AntoninoBonanno/Smart-Street/tree/master/c%2B%2B) (auto): C ++
- [Access point](https://github.com/AntoninoBonanno/Smart-Street/tree/master/python/AccessPoint): python
- [Graphic user interface](https://github.com/AntoninoBonanno/Smart-Street/tree/master/Go): GoLang, Qml and JavaScript

The application stores data relating to clients, routes, ip etc. in a MySQL database.



## Installation

1) Run the **database.sql** script, for initialize the database on MariaDB (MySQL)

2) Install the [utility dependencies](https://github.com/AntoninoBonanno/Smart-Street/tree/master/python/utility#installation)

3) Install the [Access point](https://github.com/AntoninoBonanno/Smart-Street/tree/master/python/AccessPoint#installation)

4) Build or make sure execution of [Client](https://github.com/AntoninoBonanno/Smart-Street/tree/master/python/utility#installation)  (auto)

5) Build or make sure execution of [Graphic user interface](https://github.com/AntoninoBonanno/Smart-Street/tree/master/Go#installation)



## Run project

1) Run the database

2) Run the [Access point](https://github.com/AntoninoBonanno/Smart-Street/tree/master/python/AccessPoint#execution) 

3) Run one or more [Street](https://github.com/AntoninoBonanno/Smart-Street/tree/master/python/Street#execution), make sure change the port at each street

4) Run the [Graphic user interface](https://github.com/AntoninoBonanno/Smart-Street/tree/master/Go#execution)

5) Run one or more [Client](https://github.com/AntoninoBonanno/Smart-Street/tree/master/python/utility#execution) (auto), make sure change the license plate at each car

6) Check the progress of the machines in the graphics


## Operation scenario


![alt text](https://github.com/AntoninoBonanno/Smart-Street/scenario.png?raw=true)


- The client, or the car, contacts the Access Point (PA), which responds with a list of possible destinations
- The client chooses the destination.
- At this point, the access point sends the information to the car for start route
- The client, knowing the IP address of the street, contacts the street, authenticates itself and starts the journey on it.
- During the journey the client and the server (road) exchange various information to change the behavior of the client.
- When a car arrives at the end of the road it is traveling on, the road communicates the IP address and the authentication token of the next road. If there are no other paths to take, she will have reached the goal.


## Authors

[Bonanno Antonino](https://github.com/AntoninoBonanno), [Biuso Mario](https://github.com/Mariobiuso), [Castagnolo Giulia](https://github.com/yuko95)