import sqlite3

conn = sqlite3.connect("taxi.db")
cursor = conn.cursor()

cursor.executescript("""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Drivers (
    driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    license_number TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Cars (
    car_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT NOT NULL UNIQUE,
    car_model TEXT,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Trips (
    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id INTEGER NOT NULL,
    car_id INTEGER NOT NULL,
    pickup_location TEXT NOT NULL,
    dropoff_location TEXT NOT NULL,
    start_time DATETIME,
    end_time DATETIME,
    FOREIGN KEY(driver_id) REFERENCES Drivers(driver_id),
    FOREIGN KEY(car_id) REFERENCES Cars(car_id)
);

CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL
);

INSERT INTO Users(username,password,role)
VALUES
('admin','123','admin'),
('staff1','123','staff');
""")

cursor.execute("ALTER TABLE Trips ADD COLUMN distance REAL")
cursor.execute("ALTER TABLE Trips ADD COLUMN price INTEGER")




conn.commit()
conn.close()

print("Database created successfully!")