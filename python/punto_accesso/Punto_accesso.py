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
    route = db.checkRoute(car_id)

    if route is None:

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

        message = f"Procedi con l'indirizzo indicato per poter raggiungere {destination_street.name}"
    else:
        destination_street = db.getStreets(route.destination)[0]
        message = f"Hai già richiesto l'accesso per la destinazione {destination_street.name}. Raggiungi la destinazione prima di richiederne una nuova."

    token = Auth.create_token(
        route.id, route.route_list[route.current_index])  # creo il token

    firstStreet = db.getStreets(route.route_list[route.current_index])[0]
    return jsonify(address=firstStreet.getIpAddress(), access_token=token.decode('UTF-8'), message=message), 200


def onExit():
    db.close()


# quando si chiude il processo, chiudo anche la connessione con il db
atexit.register(onExit)

if __name__ == '__main__':
    app.run()  # avvio il server
