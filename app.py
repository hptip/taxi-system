from flask import Flask, render_template, request, redirect, flash
import sqlite3
from geopy.geocoders import Nominatim   
from datetime import datetime,timedelta
import requests


app = Flask(__name__)
app.secret_key = "taxi_secret"


def get_db():
    conn = sqlite3.connect("taxi.db")
    conn.row_factory = sqlite3.Row
    return conn
#Tinh duong di
geolocator = Nominatim(user_agent="taxi_app")
def calculate_route(pickup, dropoff):

    try:

        # tìm tọa độ
        location1 = geolocator.geocode(pickup + ", Vietnam")
        location2 = geolocator.geocode(dropoff + ", Vietnam")

        if not location1 or not location2:
            return None, None

        coord1 = f"{location1.longitude},{location1.latitude}"
        coord2 = f"{location2.longitude},{location2.latitude}"

        url = f"https://router.project-osrm.org/route/v1/driving/{coord1};{coord2}?overview=false"

        response = requests.get(
            url,
            headers={"User-Agent": "taxi-app"},
            timeout=5
        )
        data = response.json()

        if "routes" not in data or len(data["routes"]) == 0:
            return None, None

        distance = data["routes"][0]["distance"] / 1000
        duration = data["routes"][0]["duration"] / 60
        duration *=1.4

        return round(distance,2), round(duration,1)

    except Exception as e:
        print("Route error:", e)
        return None, None





# Trang chủ - hiển thị danh sách lái xe

@app.route("/")
def home():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Drivers")
    driver_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Cars")
    car_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Trips")
    trip_count = cursor.fetchone()[0]
    conn.close()

    return render_template(
        "home.html",
        driver_count=driver_count,
        car_count=car_count,
        trip_count=trip_count
    )

@app.route("/drivers")
def index():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Drivers")
    drivers = cursor.fetchall()
    conn.close()
    return render_template("index.html", drivers=drivers)




# Thêm lái xe
@app.route("/add", methods=["GET","POST"])
def add_driver():
    conn = get_db()
    cursor = conn.cursor()


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
        conn.close()

        return redirect("/drivers")
    conn.close()
    return render_template("add_driver.html")


# Xóa lái xe
@app.route("/delete_driver/<int:id>")
def delete_driver(id):

    conn = get_db()
    cursor = conn.cursor()

    # kiểm tra driver có trip không
    cursor.execute("SELECT * FROM Trips WHERE driver_id=?", (id,))
    trip = cursor.fetchone()

    if trip:
        flash("Không thể xóa tài xế vì đang có chuyến đi!", "danger")
        conn.close()
        return redirect("/drivers")

    cursor.execute("DELETE FROM Drivers WHERE driver_id=?", (id,))
    conn.commit()
    conn.close()

    flash("Xóa tài xế thành công!", "success")
    return redirect("/drivers")


# Sửa lái xe
@app.route("/edit/<id>",methods=["GET","POST"])
def edit_driver(id):
    conn = get_db()
    cursor = conn.cursor()


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
        conn.close()

        return redirect("/drivers")

    cursor.execute("SELECT * FROM Drivers WHERE driver_id=?", (id,))
    driver=cursor.fetchone()
    conn.close()

    return render_template("edit_driver.html",driver=driver)
#Hien thi danh sach xe
@app.route("/cars")
def cars():
    conn = get_db()
    cursor = conn.cursor()


    cursor.execute("SELECT * FROM Cars")
    cars = cursor.fetchall()
    conn.close()

    return render_template("cars.html", cars=cars)

#Them xe
@app.route("/add_car", methods=["GET","POST"])
def add_car():
    conn = get_db()
    cursor = conn.cursor()


    if request.method == "POST":

        plate = request.form["plate"]
        model = request.form["model"]
        status = request.form["status"]

        cursor.execute(
        "INSERT INTO Cars (plate_number,car_model,status) VALUES (?,?,?)",
        (plate,model,status)
        )

        conn.commit()
        conn.close()
        return redirect("/cars")
    conn.close()
    return render_template("add_car.html")
#Sua xe
@app.route("/edit_car/<id>", methods=["GET","POST"])
def edit_car(id):
    conn = get_db()
    cursor = conn.cursor()


    if request.method == "POST":

        plate = request.form["plate"]
        model = request.form["model"]
        status = request.form["status"]

        cursor.execute(
        "UPDATE Cars SET plate_number=?, car_model=?, status=? WHERE car_id=?",
        (plate,model,status,id)
        )

        conn.commit()
        conn.close()

        return redirect("/cars")

    cursor.execute("SELECT * FROM Cars WHERE car_id=?", (id,))
    car = cursor.fetchone()
    conn.close()
    return render_template("edit_car.html", car=car)


#Xoa xe
@app.route("/delete_car/<id>")
def delete_car(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Trips WHERE car_id=?", (id,))
    trip = cursor.fetchone()

    if trip:
        flash("Không thể xóa xe vì đang có chuyến!", "danger")
        conn.close()
        return redirect("/cars")


    cursor.execute("DELETE FROM Cars WHERE car_id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/cars")
#Danh sach chuyen di
@app.route("/trips")
def trips():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT t.trip_id,
                    d.name as driver_name,
                    c.plate_number as license_plate,
                    t.pickup_location,
                    t.dropoff_location,
                    t.start_time,
                    t.end_time,
                    t.distance,
                    t.price
    FROM Trips t
    JOIN Drivers d ON t.driver_id = d.driver_id
    JOIN Cars c ON t.car_id = c.car_id
    ORDER BY t.start_time DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    trips = []
    now = datetime.now()

    for r in rows:

        start = datetime.fromisoformat(r["start_time"]) if r["start_time"] else None
        end = datetime.fromisoformat(r["end_time"]) if r["end_time"] else None

        if not start or not end:
            status = "Không xác định"
        elif now < start:
            status = "Chưa bắt đầu"
        elif start <= now <= end:
            status = "Đang chạy"
        else:
            status = "Hoàn thành"

        trip = dict(r)
        trip["status"] = status

        trips.append(trip)

    return render_template("trips.html", trips=trips)

#Ham check trip conflict
def check_trip_conflict(cursor, driver_id, car_id, start_time, end_time, exclude_trip=None):

    buffer_minutes = 15

    # kiểm tra tài xế
    if exclude_trip:
        cursor.execute("""
        SELECT start_time,end_time
        FROM Trips
        WHERE driver_id=? AND trip_id != ?
        """,(driver_id,exclude_trip))
    else:
        cursor.execute("""
        SELECT start_time,end_time
        FROM Trips
        WHERE driver_id=?
        """,(driver_id,))

    trips = cursor.fetchall()

    for trip in trips:

        old_start = datetime.fromisoformat(trip["start_time"])
        old_end = datetime.fromisoformat(trip["end_time"])

        safe_end = old_end + timedelta(minutes=buffer_minutes)

        if start_time < safe_end and end_time > old_start:
            return "Tài xế đã có chuyến trong khoảng thời gian này!"

    # kiểm tra xe
    if exclude_trip:
        cursor.execute("""
        SELECT start_time,end_time
        FROM Trips
        WHERE car_id=? AND trip_id != ?
        """,(car_id,exclude_trip))
    else:
        cursor.execute("""
        SELECT start_time,end_time
        FROM Trips
        WHERE car_id=?
        """,(car_id,))

    trips = cursor.fetchall()

    for trip in trips:

        old_start = datetime.fromisoformat(trip["start_time"])
        old_end = datetime.fromisoformat(trip["end_time"])

        safe_end = old_end + timedelta(minutes=buffer_minutes)

        if start_time < safe_end and end_time > old_start:
            return "Xe đã có chuyến trong khoảng thời gian này!"

    return None
#Them chuyen di
@app.route("/add_trip", methods=["GET","POST"])
def add_trip():
    conn = get_db()
    cursor = conn.cursor()
    # kiểm tra tài xế và xe
    cursor.execute("SELECT COUNT(*) FROM Drivers WHERE status='Khỏe'")
    available_drivers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Cars WHERE status='Hoạt động'")
    available_cars = cursor.fetchone()[0]

    if available_drivers == 0 or available_cars == 0:
        flash("Không thể tạo chuyến: không có tài xế sẵn sàng hoặc không có xe hoạt động!", "danger")
        conn.close()
        return redirect("/trips")


    if request.method == "POST":

        driver_id = request.form["driver_id"]
        car_id = request.form["car_id"]
        pickup = request.form["pickup"]
        dropoff = request.form["dropoff"]
        start_time = request.form["start_time"]

        start_time = datetime.strptime(start_time,"%Y-%m-%dT%H:%M")
        #check trung dia diem
        if pickup.strip() == dropoff.strip():
            flash("Điểm đón và điểm trả không được giống nhau!", "danger")
            conn.close()
            return redirect("/add_trip")
        #check thoi gian
        now = datetime.now()

        if start_time < now:
            flash("Thời gian bắt đầu không được trước hiện tại!", "danger")
            conn.close()
            return redirect("/add_trip")
        #tinh duong di
        distance, estimated_time = calculate_route(pickup, dropoff)
        #truong hop OSRM lỗi
        if distance is None or estimated_time is None:
            flash("Không tính được tuyến đường!", "danger")
            conn.close()
            return redirect("/add_trip")

        price_per_km = 12000

        price = round(distance * price_per_km)

        end_time = start_time + timedelta(minutes=estimated_time)
        buffer_minutes = 15
        #check time hop le
        if end_time <= start_time:
            flash("Thời gian kết thúc phải sau thời gian bắt đầu!", "danger")
            conn.close()
            return redirect("/add_trip")

        #Tai xe om hoac nghi
        cursor.execute("SELECT status FROM Drivers WHERE driver_id=?", (driver_id,))
        driver_status = cursor.fetchone()[0]

        if driver_status != "Khỏe":
            flash("Tài xế đang ốm hoặc nghỉ, không thể tạo chuyến!", "danger")
            conn.close()
            return redirect("/add_trip")
        #Xe hong hoac bao duong
        cursor.execute("SELECT status FROM Cars WHERE car_id=?", (car_id,))
        car_status = cursor.fetchone()[0]

        if car_status != "Hoạt động":
            flash("Xe đang hỏng hoặc bảo dưỡng!", "danger")
            conn.close()
            return redirect("/add_trip")
        
        
        #Check trung chuyen
        error = check_trip_conflict(cursor, driver_id, car_id, start_time, end_time)

        if error:
            flash(error, "danger")
            conn.close()
            return redirect("/add_trip")
        

        cursor.execute(
        """INSERT INTO Trips(driver_id,car_id,pickup_location,dropoff_location,start_time,end_time,distance,price)
            VALUES(?,?,?,?,?,?,?,?)""",
        (driver_id,car_id,pickup,dropoff,start_time,end_time,distance,price)
        )

        conn.commit()

        flash("Tạo chuyến đi thành công!", "success")
        conn.close()
        return redirect("/trips")

    cursor.execute("SELECT * FROM Drivers WHERE status='Khỏe'")
    drivers = cursor.fetchall()

    cursor.execute("SELECT * FROM Cars WHERE status='Hoạt động'")
    cars = cursor.fetchall()
    conn.close()

    return render_template("add_trip.html", drivers=drivers, cars=cars)

#Xoa chuyen di
@app.route("/delete_trip/<int:id>")
def delete_trip(id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT start_time, end_time FROM Trips WHERE trip_id=?",
        (id,)
    )

    trip = cursor.fetchone()

    if trip:

        start = datetime.fromisoformat(trip["start_time"])
        end = datetime.fromisoformat(trip["end_time"])
        now = datetime.now()

        if start <= now <= end:
            flash("Không thể xóa chuyến đang chạy!", "danger")
            conn.close()
            return redirect("/trips")

        cursor.execute("DELETE FROM Trips WHERE trip_id=?", (id,))
        conn.commit()

        flash("Xóa chuyến thành công!", "success")

    conn.close()

    return redirect("/trips")
#Sua chuyen di
@app.route("/edit_trip/<id>", methods=["GET","POST"])
def edit_trip(id):

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":

        driver_id = request.form["driver_id"]
        car_id = request.form["car_id"]
        pickup = request.form["pickup"]
        dropoff = request.form["dropoff"]
        start_time = request.form["start_time"]

        start_time = datetime.strptime(start_time,"%Y-%m-%dT%H:%M")
        #check trung dia diem
        if pickup.strip() == dropoff.strip():
            flash("Điểm đón và điểm trả không được giống nhau!", "danger")
            conn.close()
            return redirect("/edit_trip")
        #check thoi gian
        now = datetime.now()

        if start_time < now:
            flash("Thời gian bắt đầu không được trước hiện tại!", "danger")
            conn.close()
            return redirect(f"/edit_trip/{id}")
        #Dia diem khong ton tai
        distance, estimated_time = calculate_route(pickup, dropoff)
        #OSRM lỗi
        if distance is None or estimated_time is None:
            flash("Không tính được tuyến đường!", "danger")
            conn.close()
            return redirect(f"/edit_trip/{id}")
    


        end_time = start_time + timedelta(minutes=estimated_time)

        price_per_km = 12000
        price = round(distance * price_per_km)
        # kiểm tra tài xế
        cursor.execute("SELECT status FROM Drivers WHERE driver_id=?", (driver_id,))
        driver_status = cursor.fetchone()[0]

        if driver_status != "Khỏe":
            flash("Tài xế đang nghỉ hoặc ốm!", "danger")
            conn.close()
            return redirect(f"/edit_trip/{id}")

        # kiểm tra xe
        cursor.execute("SELECT status FROM Cars WHERE car_id=?", (car_id,))
        car_status = cursor.fetchone()[0]

        if car_status != "Hoạt động":
            flash("Xe đang bảo dưỡng hoặc hỏng!", "danger")
            conn.close()
            return redirect(f"/edit_trip/{id}")

        error = check_trip_conflict(cursor, driver_id, car_id, start_time, end_time, id)

        if error:
            flash(error, "danger")
            conn.close()
            return redirect(f"/edit_trip/{id}")

        # cập nhật
        cursor.execute("""
        UPDATE Trips
        SET driver_id=?,
            car_id=?,
            pickup_location=?,
            dropoff_location=?,
            start_time=?,
            end_time=?,
            distance=?,
            price=?
        WHERE trip_id=?
        """,
        (driver_id,car_id,pickup,dropoff,start_time,end_time,distance,price,id)
        )

        conn.commit()
        conn.close()

        flash("Cập nhật chuyến đi thành công!", "success")
        return redirect("/trips")

    cursor.execute("SELECT * FROM Drivers")
    drivers = cursor.fetchall()

    cursor.execute("SELECT * FROM Cars")
    cars = cursor.fetchall()

    cursor.execute("SELECT * FROM Trips WHERE trip_id=?", (id,))
    trip = cursor.fetchone()

    conn.close()

    return render_template("edit_trip.html",trip=trip,drivers=drivers,cars=cars)




if __name__ == "__main__":
    app.run(debug=True)
