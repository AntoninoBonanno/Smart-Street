import json
from flask import Flask
from DatabaseHelper import Database

app = Flask(__name__)
db = Database()


@app.route('/', methods=['GET'])
def street_list():
    streets = db.getStreets()
    streets = [street.to_dict() for street in streets]
    streets.sort(key=lambda obj: obj["id"])

    return json.dumps({"streets": streets})


if __name__ == '__main__':
    app.run()
