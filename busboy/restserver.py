import json
import datetime as dt
from flask import Flask, send_file, abort
app = Flask(__name__)

import busboy.constants as c
import busboy.database as db
from busboy.model import TripId

@app.route("/")
def hello():
   return f"<h1>Hello Down There!</h1><p>Church cross east’s id: {c.church_cross_east}</p>"

@app.route("/points/<trip_id>/")
def trip_points(trip_id: str):
    tps = db.trip_points(db.default_connection(), TripId(trip_id))
    response = json.dumps(tps.to_json())
    return (response, {"Content-Type": "text/json", "Access-Control-Allow-Origin": "*"})

@app.route("/trips/<date>/")
def trips_on_day(date: str):
    try:
        d = dt.date.fromisoformat(date)
    except ValueError:
        abort(400)
    else:
        trips = db.trips_on_day(
            db.default_connection(),
            d
        )
        body = [t.value for t in trips]
        return (json.dumps(body), {"Content-Type": "text/json", "Access-Control-Allow-Origin": "*"})


@app.route("/map.html")
def map():
    return send_file("map/map.html")

@app.route("/map.js")
def map_js():
    return send_file("map/map.js")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
