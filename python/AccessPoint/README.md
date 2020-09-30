# AccessPoint

The access point is a REST Server written entirely in Python language, created through the Flask library.

Specifications:

- Can provide possible destinations
- It can create paths for a client by providing an authentication token. The route is a sequence of roads expressed with their id, which the client must follow to arrive at the chosen destination.
- Provides the ip address of the first street of the route

## Dependencies

* [Flask](https://flask.palletsprojects.com/en/1.1.x/)


## Installation

1) Install Flask

    `> pip install Flask`

    or if you use Anaconda

    `> conda install -c anaconda flask`

## Execution

Run this command:

`> python python\AccessPoint\AccessPoint.py`

or you can specify:

`> python python\AccessPoint\AccessPoint.py --host [ip_host] --port [port_host]`


## Authors

[Bonanno Antonino](https://github.com/AntoninoBonanno), [Biuso Mario](https://github.com/Mariobiuso)


