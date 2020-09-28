import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))) + "/utility")

import atexit
import argparse
from random import randint
from flask import Flask, jsonify, request, abort, make_response

import Auth
from DatabaseHelper import Database

app = Flask(__name__)
db = Database()


@app.route('/', methods=['GET'])
def street_list():
    """
    Funzione che restituisce la lista delle strade e le loro informazioni

    Returns:
        Json: {streets: lista delle strade, message: messaggio generico}
    """

    streets = db.getStreets()  # recupero le strade dal DB
    # Converto l'oggetto in dizionario
    streets = [street.to_dict() for street in streets]
    streets.sort(key=lambda obj: obj["id"])  # ordino per id

    return jsonify(streets=streets, message="Lista delle destinazioni possibili"), 200


@app.route('/', methods=['POST'])
def create_route():
    """
    Funzione che crea un percorso per la destinazione selezionata, creando un token di autenticazione per poter accedere alla prima strada del percorso.
    Se esiste già un percorso, viene restituito il token per la strada dove era attualmente la macchina. Una macchina deve completare il percorso prima di richiederne uno nuovo.

    Returns:
        Json: {address: indirizzo della strada a cui bisogna chiedere l'accesso, access_token: token per accedere nella strada, message: messaggio generico}
    """

    post_data = request.get_json(force=True)

    car_id = post_data.get('targa', None)
    street_id = post_data.get('destinazione', None)
    if (car_id is None or street_id is None or isinstance(street_id, str) or street_id < 1):
        abort(make_response(jsonify(message="Formato dei parametri non corretti"), 400))

    # Verifico se esiste già un percorso per quella macchina
    route = db.getRoutes(car_id=car_id, finished=False)

    if not route:

        destination_street = db.getStreets(street_id)
        if (not destination_street):  # verifico se esiste la destinazione selezionata
            abort(make_response(jsonify(message="Destinazione non trovata"), 400))
        destination_street = destination_street[0]

        if (destination_street.available == False):  # verifico se la destinazione è available
            abort(make_response(
                jsonify(message="Destinazione attualmente non disponibile"), 400))

        streets = db.getStreets()
        # recupero la lista di tutte le strade escludendo quella passata nella funzione, perchè è la strada da raggiungere
        street_ids = [
            street.id for street in streets if (street.id != street_id and street.available == True)]
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
        # salvo il nuovo percorso sul DB
        route = db.upsertRoute(car_id, request.remote_addr, route_list)
        if(route is None):
            abort(make_response(jsonify(message="Errore creazione percorso"), 500))

        message = f"Procedi con l'host e port indicato per poter raggiungere {destination_street.name}"
    else:
        route = route[0]
        destination_street = db.getStreets(route.destination)[0]
        message = f"Hai gia' richiesto l'accesso per la destinazione {destination_street.name}. Raggiungi la destinazione prima di richiederne una nuova."

    current_index = route.current_index if route.current_index > -1 else 0
    firstStreet = db.getStreets(route.route_list[current_index])[0]

    if (route.current_street_position is not None) and (route.current_street_position> firstStreet.length):
        # se la macchina ha già completato la strada e per qualche motivo la strada non è riuscita ad aggiornare la route, lo faccio da qui
        current_index += 1
        firstStreet = db.getStreets(route.route_list[current_index])[0]
        db.upsertRoute(car_id, request.remote_addr, current_index=current_index,
                       current_street_position=0, id=route.id)

    token = Auth.create_token(route.id, firstStreet.id)  # creo il token

    host, port = firstStreet.getIpAddress()
    if not host:
        abort(make_response(jsonify(message="Errore indirizzo strada"), 500))

    return jsonify(host=host, port=port, access_token=token.decode('UTF-8'), message=message), 200


def onExit():
    db.close()


# quando si chiude il processo, chiudo anche la connessione con il db
atexit.register(onExit)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default=None)
    parser.add_argument('--port', type=int, default=None)
    args = parser.parse_args()

    app.run(host=args.host, port=args.port)  # avvio il server
