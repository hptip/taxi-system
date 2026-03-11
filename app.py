from flask import Flask, render_template, request, redirect, flash
import pyodbc

from datetime import datetime
app = Flask(__name__)
app.secret_key = "taxi_secret"


conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=LAPTOP-3GT9SESD\\SQLEXPRESS;"
    "DATABASE=TaxiManagement;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()


# Trang chủ - hiển thị danh sách lái xe
from flask import render_template

@app.route("/")
def home():

    cursor.execute("SELECT COUNT(*) FROM Drivers")
    driver_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Cars")
    car_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Trips")
    trip_count = cursor.fetchone()[0]

    return render_template(
        "home.html",
        driver_count=driver_count,
        car_count=car_count,
        trip_count=trip_count
    )

@app.route("/drivers")
def index():
    cursor.execute("SELECT * FROM Drivers")
    drivers = cursor.fetchall()
    return render_template("index.html", drivers=drivers)




# Thêm lái xe
@app.route("/add", methods=["GET","POST"])
def add_driver():

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]
        license = request.form["license"]
        status = request.form["status"]

        cursor.execute(
        "INSERT INTO Drivers (name,phone,license_number,status) VALUES (?,?,?,?)",
        (name,phone,license,status)
        )

        conn.commit()

        return redirect("/")

    return render_template("add_driver.html")


# Xóa lái xe
@app.route("/delete/<id>")
def delete_driver(id):

    cursor.execute("DELETE FROM Drivers WHERE driver_id=?", (id,))
    conn.commit()

    return redirect("/")


# Sửa lái xe
@app.route("/edit/<id>",methods=["GET","POST"])
def edit_driver(id):

    if request.method=="POST":

        name=request.form["name"]
        phone=request.form["phone"]
        license=request.form["license"]
        status=request.form["status"]

        cursor.execute(
        "UPDATE Drivers SET name=?,phone=?,license_number=?,status=? WHERE driver_id=?",
        (name,phone,license,status,id)
        )

        conn.commit()

        return redirect("/")

    cursor.execute("SELECT * FROM Drivers WHERE driver_id=?", (id,))
    driver=cursor.fetchone()

    return render_template("edit_driver.html",driver=driver)
#Hien thi danh sach xe
@app.route("/cars")
def cars():

    cursor.execute("SELECT * FROM Cars")
    cars = cursor.fetchall()

    return render_template("cars.html", cars=cars)

#Them xe
@app.route("/add_car", methods=["GET","POST"])
def add_car():

    if request.method == "POST":

        plate = request.form["plate"]
        model = request.form["model"]
        status = request.form["status"]

        cursor.execute(
        "INSERT INTO Cars (plate_number,car_model,status) VALUES (?,?,?)",
        (plate,model,status)
        )

        conn.commit()

        return redirect("/cars")

    return render_template("add_car.html")
#Sua xe
@app.route("/edit_car/<id>", methods=["GET","POST"])
def edit_car(id):

    if request.method == "POST":

        plate = request.form["plate"]
        model = request.form["model"]
        status = request.form["status"]

        cursor.execute(
        "UPDATE Cars SET plate_number=?, car_model=?, status=? WHERE car_id=?",
        (plate,model,status,id)
        )

        conn.commit()

        return redirect("/cars")

    cursor.execute("SELECT * FROM Cars WHERE car_id=?",id)
    car = cursor.fetchone()

    return render_template("edit_car.html", car=car)


#Xoa xe
@app.route("/delete_car/<id>")
def delete_car(id):

    cursor.execute("DELETE FROM Cars WHERE car_id=?", (id,))
    conn.commit()

    return redirect("/cars")
#Danh sach chuyen di
@app.route("/trips")
def trips():

    cursor.execute("""
    SELECT t.trip_id,
           d.name as driver_name,
           t.pickup_location,
           t.dropoff_location,
           t.start_time,
           t.end_time
    FROM Trips t
    JOIN Drivers d ON t.driver_id = d.driver_id
    JOIN Cars c ON t.car_id = c.car_id
    """)

    trips = cursor.fetchall()

    return render_template("trips.html", trips=trips, now=datetime.now())

#Them chuyen di
@app.route("/add_trip", methods=["GET","POST"])
def add_trip():

    if request.method == "POST":

        driver_id = request.form["driver_id"]
        car_id = request.form["car_id"]
        pickup = request.form["pickup"]
        dropoff = request.form["dropoff"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        start_time = datetime.fromisoformat(start_time)
        end_time = datetime.fromisoformat(end_time)

        #Tai xe om hoac nghi
        cursor.execute("SELECT status FROM Drivers WHERE driver_id=?", (driver_id,))
        driver_status = cursor.fetchone()[0]

        if driver_status != "Khỏe":
            flash("Tài xế đang ốm hoặc nghỉ, không thể tạo chuyến!", "danger")
            return redirect("/add_trip")
        #Xe hong hoac bao duong
        cursor.execute("SELECT status FROM Cars WHERE car_id=?", (car_id,))
        car_status = cursor.fetchone()[0]

        if car_status != "Hoạt động":
            flash("Xe đang hỏng hoặc bảo dưỡng!", "danger")
            return redirect("/add_trip")
        #Tai xe da co chuyen
        cursor.execute("""
        SELECT * FROM Trips
        WHERE driver_id=?
        AND (
            (? < end_time) AND (? > start_time)
        )
        """, (driver_id, start_time, end_time))

        exist = cursor.fetchone()

        if exist:
            flash("Tài xế đã có chuyến trong khoảng thời gian này.","danger")
            return redirect("/add_trip")
        #Xe da co chuyen
        cursor.execute("""
        SELECT * FROM Trips
        WHERE driver_id=?
        AND (
            (? < end_time) AND (? > start_time)
        )
        """, (driver_id, start_time, end_time))

        exist = cursor.fetchone()

        if exist:
            flash("Tài xế đã có chuyến trong khoảng thời gian này.","danger")
            return redirect("/add_trip")
        
        #Check trung chuyen
        cursor.execute("""
        SELECT start_time,end_time
        FROM Trips
        WHERE driver_id=?
        """,(driver_id,))

        trips = cursor.fetchall()

        for trip in trips:

            old_start = trip[0]
            old_end = trip[1]

            if start_time < old_end and end_time > old_start:

                flash("Tài xế đã có chuyến trong khoảng thời gian này!", "danger")
                return redirect("/add_trip")

        cursor.execute(
        """INSERT INTO Trips(driver_id,car_id,pickup_location,dropoff_location,start_time,end_time)
        VALUES(?,?,?,?,?,?)""",
        (driver_id,car_id,pickup,dropoff,start_time,end_time)
        )

        conn.commit()

        flash("Tạo chuyến đi thành công!", "success")
        return redirect("/trips")

    cursor.execute("SELECT * FROM Drivers")
    drivers = cursor.fetchall()

    cursor.execute("SELECT * FROM Cars")
    cars = cursor.fetchall()

    return render_template("add_trip.html", drivers=drivers, cars=cars)

#Xoa chuyen di
@app.route("/delete_trip/<id>")
def delete_trip(id):

    cursor.execute("DELETE FROM Trips WHERE trip_id=?", (id,))
    conn.commit()

    return redirect("/trips")
#Sua chuyen di
@app.route("/edit_trip/<id>", methods=["GET","POST"])
def edit_trip(id):

    if request.method == "POST":

        driver_id = request.form["driver_id"]
        car_id = request.form["car_id"]
        pickup = request.form["pickup"]
        dropoff = request.form["dropoff"]
        date = request.form["date"]

        cursor.execute("""
        UPDATE Trips
        SET driver_id=?, car_id=?, pickup_location=?, dropoff_location=?, trip_date=?
        WHERE trip_id=?
        """, (driver_id,car_id,pickup,dropoff,date,id))

        conn.commit()

        return redirect("/trips")

    cursor.execute("SELECT * FROM Drivers")
    drivers = cursor.fetchall()

    cursor.execute("SELECT * FROM Cars")
    cars = cursor.fetchall()

    cursor.execute("SELECT * FROM Trips WHERE trip_id=?", id)
    trip = cursor.fetchone()

    return render_template("edit_trip.html", trip=trip, drivers=drivers, cars=cars)




if __name__=="__main__":
    app.run(debug=True)

