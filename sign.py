from flask import Flask,render_template, request, redirect, url_for 
import sqlite3
import random
import time

app= Flask(__name__)



@app.route("/")
def Home():
    return render_template("home.html")

@app.route("/Services")
def services():
    return render_template("services.html")

@app.route("/About")
def About():
    return render_template("about.html")

@app.route("/sign", methods=['POST', 'GET'])
def sign():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        username = request.form['username']
        password = request.form['password']
        Date = request.form['Dob']
        email = request.form['email']
        Address = request.form['Address']
        region_count = int(request.form['region_count'])
        
        conn = sqlite3.connect('Sensors.db')
        c = conn.cursor()

        c.execute('SELECT * FROM Sign WHERE username = ?', (username,))
        user = c.fetchone()

        if user is None:
            c.execute("INSERT INTO Sign(name, surname, username, password, Dob, email, Address, region_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(name, surname, username, password, Date, email, Address, region_count))
            conn.commit()

           # Insert user regions into user_regions table
            for region_id in range(1, region_count + 1):
                c.execute("INSERT INTO user_regions(username, region_id) VALUES (?, ?)", (username, region_id))
                conn.commit()

            return redirect(url_for('login2'))
        else:
            return render_template("sign.html")
    else:
        return render_template("sign.html")


@app.route("/login2", methods = ['POST', 'GET'])
def login2():
    if request.method== 'POST':
        username = request.form['username']  #request input from the html page
        password = request.form['password']
        conn = sqlite3.connect('Sensors.db')
        c = conn.cursor()
        c.execute("SELECT * FROM  Sign  WHERE username = ? AND password = ?", (username,password)) #check if a row exists where the username and password match the provided values
        user = c.fetchone()

        if user is not None:
            return redirect(url_for('index3', username=username))
        else:
            error = "Username or Password is incorrect!!, TRY Again or SIGN UP."
            return render_template("login2.html",error = error)
    else:
        return render_template("login2.html")

@app.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        
        conn = sqlite3.connect('Sensors.db')
        c = conn.cursor()
        c.execute("SELECT password FROM Sign WHERE username = ?", (username,))
        password = c.fetchone()

        if password is not None:
            return render_template("forgot_password.html", password=password[0])
        else:
            return redirect(url_for('sign'))
    else:
        return render_template("forgot_password.html")


# Connect to the SQLite database
conn = sqlite3.connect('Sensors.db')


 # Create the Time table
conn = sqlite3.connect('Sensors.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS Time(
              Zone TEXT,
              timeframe TEXT,
              DateT REAL,
              liters INTEGER,
              duration INTEGER,
              valid INTEGER,
              FOREIGN KEY(Zone) REFERENCES regions(id),
              PRIMARY KEY (Zone, timeframe, DateT, region)
            )''')
conn.commit()

conn = sqlite3.connect('Sensors.db')
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS user_regions (username TEXT, region_id INTEGER, FOREIGN KEY(username) REFERENCES Sign(username), FOREIGN KEY(region_id) REFERENCES regions(region_id), PRIMARY KEY (username, region_id))")
conn.commit()

c.close()
# Connect to the SQLite database
conn = sqlite3.connect('Sensors.db')
c = conn.cursor()

# Create the regions table if it doesn't exist
c.execute("CREATE TABLE IF NOT EXISTS regions (region_id INTEGER PRIMARY KEY, region_name TEXT)")

# Close the cursor and connection
c.close()
conn.close()
# Generate random sensor data and insert it into the database

def generate_sensors_data(region_count):
    timestamp = "%.1f" % int(time.time())
    soil_moisture = "%.1f" % random.uniform(0.0, 1.0)
    temperature = "%.1f" % random.uniform(20.0, 30.0)
    humidity = "%.1f" % random.uniform(40.0, 60.0)
    water = "%.1f" % random.uniform(0.0, 1000.0)
    c = conn.cursor()

    for region_id in range(1, region_count + 1):
        c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "soil_moisture", soil_moisture, region_id))
        c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "temperature", temperature, region_id))
        c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "humidity", humidity, region_id))
        c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "water_levels", water, region_id))
    
    conn.commit()




# Start a separate thread to generate and insert the sensor data every minute
def background_thread(region_count):
    while True:
        generate_sensors_data(region_count)
        time.sleep(60)

# Start the background thread on app startup
from threading import Thread
bg_thread = Thread(target=background_thread)  #It assigns the background_thread function as the target for the thread and then starts the thread by calling its start() method.
bg_thread.start()


@app.route('/index3/<username>', methods=['POST', 'GET'])
def index3(username):
    conn = sqlite3.connect('Sensors.db')
    c = conn.cursor()

    # Retrieve the user's region count from the user_regions table
    c.execute("SELECT region_count FROM Sign WHERE username = ?", (username,))
    region_count = c.fetchone()[0]

    # Query the sensor data from the database, filtered by region if specified
    region = request.args.get('region', default=None, type=int)

    # If a region count is specified, generate new sensor data and update the database
    if region_count is not None:
        timestamp = str(int(time.time()))
        for region_id in range(1, region_count + 1):
            soil_moisture = "%.1f" % random.uniform(0.0, 100)
            temperature = "%.1f" % random.uniform(20.0, 30.0)
            humidity = "%.1f" % random.uniform(40.0, 60.0)
            water = "%.1f" % random.uniform(0.0, 1000.0)
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "soil_moisture", soil_moisture, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "temperature", temperature, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "humidity", humidity, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "water_levels", water, region_id))
        conn.commit()

    # Query the sensor data from the database, filtered by region if specified
    if region is not None:
        c.execute("SELECT * FROM sensors_data WHERE region = ? ORDER BY timestamp DESC LIMIT 4", (region,))
    else:
        c.execute("SELECT * FROM sensors_data ORDER BY timestamp DESC LIMIT 4")
    sensor_data = c.fetchall()

    # Query the regions from the database
    c.execute("SELECT * FROM regions")
    regions = c.fetchall()

    # Close the cursor and connection
    c.close()
    conn.close()

    # Render the HTML template with the sensor data, regions, and region param
    return render_template('index3.html', username=username, sensor_data=sensor_data, regions=regions, region=region, region_count=region_count)

@app.route("/monitor/<username>", methods=['POST', 'GET'])
def monitor(username):
    conn = sqlite3.connect('Sensors.db')
    c = conn.cursor()

    # Retrieve the user's region count from the user_regions table
    c.execute("SELECT region_count FROM Sign WHERE username = ?", (username,))
    region_count = c.fetchone()[0]

    # Query the sensor data from the database, filtered by region if specified
    region = request.args.get('region', default=None, type=int)

    # If a region count is specified, generate new sensor data and update the database
    if region_count is not None:
        timestamp = str(int(time.time()))
        for region_id in range(1, region_count + 1):
            soil_moisture = "%.1f" % random.uniform(0.0, 100)
            temperature = "%.1f" % random.uniform(20.0, 30.0)
            humidity = "%.1f" % random.uniform(40.0, 60.0)
            water = "%.1f" % random.uniform(0.0, 1000.0)
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "soil_moisture", soil_moisture, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "temperature", temperature, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "humidity", humidity, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "water_levels", water, region_id))
        conn.commit()

    # Query the sensor data from the database, filtered by region if specified
    if region is not None:
        c.execute("SELECT * FROM sensors_data WHERE region = ? ORDER BY timestamp DESC LIMIT 4", (region,))
    else:
        c.execute("SELECT * FROM sensors_data ORDER BY timestamp DESC LIMIT 4")
    sensor_data = c.fetchall()

    # Query the regions from the database
    c.execute("SELECT * FROM regions")
    regions = c.fetchall()

    # Close the cursor and connection
    c.close()
    conn.close()

    # Render the HTML template with the sensor data, regions, and region param
    return render_template('monitor.html', username=username, sensor_data=sensor_data, regions=regions, region=region, region_count=region_count)


@app.route("/Time/<username>", methods=['POST', 'GET'])
def Time(username):
    if request.method == 'POST':
        Zone = request.form['region_id']
        Time = request.form['timeframe']
        date = request.form['DateT']
        level = request.form['liters']
        Duration = request.form['duration']
        Days = request.form['valid']

        conn = sqlite3.connect('Sensors.db')
        c = conn.cursor()
        c.execute('SELECT * FROM Time WHERE Zone = ? AND timeframe = ? AND DateT = ?', (Zone, Time, date))
        user = c.fetchone()

        if user is None:
            c.execute("INSERT INTO Time(Zone, timeframe, DateT, liters, duration, valid) VALUES (?, ?, ?, ?, ?, ?)",
                      (Zone, Time, date, level, Duration, Days))
            conn.commit()

            # Retrieve the inserted row for display
            c.execute("SELECT * FROM Time WHERE Zone = ? AND timeframe = ? AND DateT = ?", (Zone, Time, date))
            row = c.fetchone()

            # Close the cursor and connection
            c.close()
            conn.close()

            return redirect(url_for('TimeData', username=username, row=row))

    return render_template("Time.html", username=username)


@app.route('/TimeData/<username>')
def TimeData(username):
    Zone = request.args.get('Zone')
    Time = request.args.get('Time')
    date = request.args.get('date')
    level = request.args.get('level')
    Duration = request.args.get('Duration')
    Days = request.args.get('Days')
    row = (Zone, Time, date, level, Duration, Days)

    return render_template('TimeData.html', username=username, row=row)


if __name__ == "__main__":
    app.run(debug=True)