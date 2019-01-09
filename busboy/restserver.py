from flask import Flask
app = Flask(__name__)

import busboy.constants as c

@app.route("/")
def hello():
   return f"<h1>Hello Down There!</h1><p>Church cross east’s id: {c.church_cross_east}</p>"

@app.route("/trip/<trip_id>/")
def trip_points(trip_id):
    return f"<h1>You asked for {trip_id}!</h1>"

if __name__ == "__main__":
    app.run(host="0.0.0.0")
