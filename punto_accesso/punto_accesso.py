from flask import Flask
import mysql.connector as mysql

app = Flask(__name__)
db = mysql.connect(
    host="localhost",
    user="root",
    password="",
    database="street_smart"
)


@app.route('/', methods=['GET'])
def street_list():
    return '{"name":"Bob"}'


if __name__ == '__main__':

    cursor = db.cursor()
    query = "SELECT * FROM streets"
    cursor.execute(query)
    streets = cursor.fetchall()

    print(streets)

    app.run()
