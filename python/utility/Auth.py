import os
import jwt
import json
import datetime


def create_token(route_id: int, street_id: str) -> str:
    """
    Funzione che crea un token jwt da consegnare alla macchina per poter accedere alle strade

    Args:
        route_id (int): id del percorso
        street_id (str): id della strada a cui chiedere accesso

    Returns:
        str: token jwt
    """

    config_path = os.path.join(
        os.path.dirname(__file__), "../../config.json")

    json_data_file = open(config_path, 'r')
    config = json.load(json_data_file)  # carico il file di configurazione

    auth_token = jwt.encode({
        'payload': {  # nel token memorizzo le informazioni per effetuare dei controlli lato strada
            'street_id': street_id,
            'route_id': route_id,
        },
        # scadenza del token 5 minuti
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        'iat': datetime.datetime.utcnow(),
    }, config["secret_key"], algorithm='HS256')

    return auth_token


def decode_token(auth_token: str) -> dict:
    """
    Funzione che decodifica il token

    Args:
        auth_token (str): token jwt

    Returns:
        dict: None se il token non è stato decodificato correttamente o è scaduto (teken non valido),
              altrimenti il payload del token -> 'street_id', 'route_id'
    """

    config_path = os.path.join(
        os.path.dirname(__file__), "../../config.json")

    json_data_file = open(config_path, 'r')
    config = json.load(json_data_file)
    try:
        token_decode = jwt.decode(
            auth_token, config["secret_key"])  # decodifico il token
        return token_decode["payload"]  # restituisco il payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        return None
