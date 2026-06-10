from flask import Flask, render_template, request, redirect, session
import math

app = Flask(__name__)
app.secret_key = "secret123"

locations = {
    "gachibowli": (17.4401, 78.3489),
    "airport": (17.2403, 78.4294),
    "hitech city": (17.4435, 78.3772),
    "kukatpally": (17.4948, 78.3996),
    "secunderabad": (17.4399, 78.4983),
    "manikonda": (17.4062, 78.3586)
}

def distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R*c,2)

@app.route('/')
def login():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def handle_login():
    if request.form['username']=="admin" and request.form['password']=="1234":
        return redirect('/home')
    return "<h2>Invalid Login</h2>"

@app.route('/home')
def home():
    return render_template("index.html")

@app.route('/compare', methods=['POST'])
def compare():
    pickup = request.form['pickup'].lower().strip()
    drop = request.form['drop'].lower().strip()

    if pickup not in locations or drop not in locations:
        return "<h2>❌ Select location from dropdown</h2>"

    lat1, lon1 = locations[pickup]
    lat2, lon2 = locations[drop]

    dist = distance(lat1, lon1, lat2, lon2)
    time = int(dist * 3)

    def price(base, km):
        return int(base + dist * km)

    cabs = [
        {"name":"Uber Go","price":price(50,12),"wait":4},
        {"name":"Uber Non-AC","price":price(60,13),"wait":5},
        {"name":"Uber Premium","price":price(120,20),"wait":7},

        {"name":"Ola Mini","price":price(45,11),"wait":4},
        {"name":"Ola Auto","price":price(30,9),"wait":3},
        {"name":"Ola Sedan","price":price(70,14),"wait":7},

        {"name":"Rapido Bike","price":price(20,7),"wait":3},
        {"name":"Rapido Auto","price":price(40,10),"wait":5},
        {"name":"Rapido Cab","price":price(60,12),"wait":6},
    ]

    cheapest = min(cabs, key=lambda x: x['price'])

    return render_template("result.html",
        pickup=pickup, drop=drop,
        distance=dist, time=time,
        lat1=lat1, lon1=lon1,
        lat2=lat2, lon2=lon2,
        cabs=cabs, cheapest=cheapest
    )

if __name__ == "__main__":
    app.run(debug=True)