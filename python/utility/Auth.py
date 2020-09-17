import jwt
import json
import datetime


def create_token(route_id: int, street_id: str) -> str:
    json_data_file = open("config.json")
    config = json.load(json_data_file)

    auth_token = jwt.encode({
        'payload': {
            'street_id': street_id,
            'route_id': route_id,
        },
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        'iat': datetime.datetime.utcnow(),
    }, config["secret_key"], algorithm='HS256')

    return auth_token


def decode_token(auth_token: str) -> dict:
    json_data_file = open("config.json")
    config = json.load(json_data_file)
    try:
        token_decode = jwt.decode(auth_token, config["secret_key"])
        return token_decode["payload"]
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        return False
