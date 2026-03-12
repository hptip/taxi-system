import sqlite3

conn = sqlite3.connect("taxi.db")
cursor = conn.cursor()

cursor.executescript("""

CREATE TABLE IF NOT EXISTS Drivers (
    driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    license_number TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS Cars (
    car_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT NOT NULL,
    car_model TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS Trips (
    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id INTEGER,
    car_id INTEGER,
    pickup_location TEXT,
    dropoff_location TEXT,
    start_time DATETIME,
    end_time DATETIME,
    FOREIGN KEY(driver_id) REFERENCES Drivers(driver_id),
    FOREIGN KEY(car_id) REFERENCES Cars(car_id)
);
ALTER TABLE Trips ADD COLUMN distance REAL;
ALTER TABLE Trips ADD COLUMN price REAL;

""")


conn.commit()
conn.close()

print("Database created successfully!")