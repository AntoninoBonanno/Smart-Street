import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))) + "/utility")

import atexit
from random import randint
from flask import Flask, jsonify, request, abort, make_response

import Auth
from DatabaseHelper import Database

app = Flask(__name__)
db = Database()


@app.route('/', methods=['GET'])
def street_list():
    streets = db.getStreets()
    streets = [street.to_dict() for street in streets]
    streets.sort(key=lambda obj: obj["id"])

    res = jsonify(streets=streets)
    res.status_code = 200
    return res


@app.route('/', methods=['POST'])
def create_route():
    post_data = request.get_json(force=True)

    car_id = post_data.get('targa', None)
    street_id = post_data.get('destinazione', None)
    if (car_id is None or street_id is None or isinstance(street_id, str) or street_id < 1):
        abort(make_response(jsonify(message="Formato dei parametri non corretti"), 400))

    route = db.checkRoute(car_id)

    if route is None:

        current_street = db.getStreets(street_id)
        if (not current_street):
            abort(make_response(jsonify(message="Destinazione non trovata"), 400))
        current_street = current_street[0]

        streets = db.getStreets()
        # recupero la lista di tutte le strade escludendo quella passata nella funzione, perchè è la strada da raggiungere
        street_ids = [
            street.id for street in streets if street.id != street_id]
        streets_len = len(street_ids) - 1

        route_list = []
        if streets_len > 0:
            last_id = -1
            # creo un percorso random con almeno 5 strade e un max di 15
            for i in range(randint(5, 15)):
                idx = randint(0, streets_len)  # recupero un id
                while idx == last_id:  # l'id non deve essere lo stesso del precedente, altrimenti resto nella stessa strada
                    idx = randint(0, streets_len)

                last_id = idx
                route_list.append(street_ids[idx])

        # aggiungo la strada da raggiungere alla fine
        route_list.append(street_id)
        route = db.upsertRoute(car_id, request.remote_addr, route_list)
        if(route is None):
            abort(make_response(jsonify(message="Errore creazione percorso"), 500))

        message = f"Procedi con l'indirizzo indicato per poter raggiungere {current_street.name}"
    else:
        current_street = db.getStreets(route.destination)[0]
        message = f"Hai già richiesto l'accesso per la destinazione {current_street.name}. Raggiungi la destinazione prima di richiederne una nuova."

    token = Auth.create_token(route.id, route.route_list[route.current_index])

    return jsonify(address=current_street.getIpAddress(), access_token=token.decode('UTF-8'), message=message), 200


def onExit():
    db.close()


atexit.register(onExit)

if __name__ == '__main__':
    app.run()
