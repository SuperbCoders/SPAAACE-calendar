from flask import Flask, render_template, session, request, redirect, jsonify
from datetime import datetime
import calendar
import requests
from db import *

app = Flask(__name__)

app.config['SECRET_KEY']='a08hsd0983hroahid08qwh30iha08hdaws'



# AUTH

@app.route("/login", methods=['POST'])
def loginer():
    if "auth" in session:
        redirect("/")

    code = request.form["code"]

    conn = connect()
    cur = conn.cursor()

    query = 'SELECT count(code) FROM access WHERE code = %s;'
    cur.execute(query, (code,))
    counter = cur.fetchone()[0]

    if counter > 0:
        session["auth"] = True
        return redirect("/")
    else:
        return redirect("/login")

@app.route("/logout")
def logout():
    if "auth" not in session:
        return redirect("/login")

    session.pop("auth")

    return redirect("/login")



# API

@app.route("/api/get", methods=['GET'])
def api_get():
    conn = connect()
    cur = conn.cursor()

    from_date = request.args.get("from")
    if from_date == None or len(from_date) == 0:
        return jsonify({"error":"'from' date not provided!"})

    to_date = request.args.get("to")
    if to_date == None or len(to_date) == 0:
        return jsonify({"error":"'to' date not provided!"})

    from_query = from_date.replace(".", "-")
    to_query = to_date.replace(".", "-")

    query = 'SELECT id, to_char(start, \'HH24:MI\'), to_char(finish, \'HH24:MI\'), to_char(date, \'YYYY.MM.DD\') FROM working WHERE date >= %s AND date <= %s;'
    cur.execute(query, (from_query, to_query))

    days = []

    rows = cur.fetchall()
    for row in rows:
        days.append({"id":row[0], "start":row[1], "finish":row[2], "date":row[3], "booking":[]})

    query = 'SELECT id, to_char(start, \'HH24:MI\'), to_char(finish, \'HH24:MI\'), name, email, note FROM booking WHERE working_id = %s;'
    for day in days:
        cur.execute(query, (day["id"],))
        rows = cur.fetchall()
        for row in rows:
            day["booking"].append({"id":row[0], "start":row[1], "finish":row[2], "name":row[3], "email":row[4], "note":row[5], "products":[]})
            
            query_products = '''SELECT 
            booking_products.product_id,
            products.name FROM booking_products 
            INNER JOIN products ON booking_products.product_id = products.id 
            WHERE booking_products.booking_id = %s;'''
            cur.execute(query_products, (day["booking"][len(day["booking"])-1]["id"],))

            product_rows = cur.fetchall()
            for product_row in product_rows:
                day["booking"][len(day["booking"])-1]["products"].append({"id":product_row[0], "name":product_row[1]})

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(days)

@app.route("/api/products", methods=['GET'])
def api_products():
    conn = connect()
    cur = conn.cursor()

    query = 'SELECT id, name FROM products;'
    cur.execute(query)

    products = []
    rows = cur.fetchall()
    for row in rows:
        products.append({"id":row[0], "name":row[1]})

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(products)

@app.route("/api/book", methods=['POST'])
def api_book():
    conn = connect()
    cur = conn.cursor()

    data = request.get_json()

    date = data["date"]
    if date == None or len(date) == 0:
        return jsonify({"error":"date not provided!"})

    start = data["start"]
    if start == None or len(start) == 0:
        return jsonify({"error":"start not provided!"})

    finish = data["finish"]
    if finish == None or len(finish) == 0:
        return jsonify({"error":"finish not provided!"})

    name = data["name"]
    if name == None or len(name) == 0:
        return jsonify({"error":"name not provided!"})

    email = data["email"]
    if email == None or len(email) == 0:
        return jsonify({"error":"email not provided!"})

    note = data["note"]
    if note == None or len(note) == 0:
        note = ""

    products = []
    if "products" in data:
        products = data["products"]

    query = 'SELECT id FROM working WHERE date = %s AND start <= %s AND finish >= %s;'
    cur.execute(query, (date.replace(".", "-"), start.replace(".", "-"), finish.replace(".", "-")))
    row = cur.fetchone()

    if row == None or len(row) == 0:
        return jsonify({"error":"failed to place a booking record!"})
    
    working_id = row[0]

    query = 'INSERT INTO booking(working_id, start, finish, name, email, note) VALUES(%s, %s, %s, %s, %s, %s) RETURNING id, to_char(start, \'HH24:MI\'), to_char(finish, \'HH24:MI\'), name, email, note;'
    cur.execute(query, (working_id, start.replace(".", "-"), finish.replace(".", "-"), name, email, note))
    row = cur.fetchone()
    response = {"id":row[0], "start":row[1], "finish":row[2], "name":row[3], "email":row[4], "note":row[5], "products":products}
    booking_id = row[0]

    for product in products:
        query = 'INSERT INTO booking_products(booking_id, product_id) VALUES(%s, %s);'
        cur.execute(query, (booking_id, product))
        conn.commit()

    conn.commit()
    cur.close()
    conn.close()

    api_token = os.getenv("UNISENDER_TOKEN")
    receiver = os.getenv("RECEIVER_EMAIL")
    message = "<b>Поступила новая заявка!</b>Имя: %s<br>Email: %s<br>День: %s<br>Время: %s - %s" % (name, email, date, start, finish)
    r = requests.get("https://api.unisender.com/ru/api/sendEmail?format=json&api_key=%s&email=Автоматическое сообщение <%s>&sender_name=NoReply&sender_email=no-reply@spaaace.io&subject=Уведомление о заявке&body=%s&lang=ru&error_checking=1&list_id=1" % (api_token, receiver, message))

    if r.status_code == 200:
        return jsonify(response)
    else:
        return jsonify({"error":"failed to send email notification!"})


# VIEWS

# Just a login page view
@app.route("/login")
def login():
    if "auth" in session:
        redirect("/")

    return render_template("login.html")

# Index page view
@app.route("/")
def index():
    if "auth" not in session:
        return redirect("/login")

    # Try to get year and month arguments,
    # set to current if none were provided
    year = request.args.get("year")
    if year == None or len(year) == 0:
        year = datetime.now().year

    month = request.args.get("month")
    if month == None or len(month) == 0:
        month = datetime.now().month

    date_filter = "%s-%s-01" % (year, month)

    # Get week data of the current month,
    # prepare the data for further details
    weeks_num = len(calendar.monthcalendar(int(year), int(month)))
    weeks_days = calendar.monthcalendar(int(year), int(month))

    weeks = []
    counter = 0
    for week in weeks_days:
        weeks.append([])
        for day in week:
            if day != 0:
                weeks[counter].append({"num":day})
            else:
                weeks[counter].append({})
        counter = counter + 1

    conn = connect()
    cur = conn.cursor()

    # Select working days data
    query = 'SELECT id, date, start, finish FROM working WHERE date >= %s AND date < (date %s + interval \'1 month\') ORDER BY date ASC;'
    cur.execute(query, (date_filter,date_filter))

    rows = cur.fetchall()

    working = []
    for row in rows:
        working.append({"id":row[0], "date":row[1], "start":row[2], "finish":row[3], "booking":[]})

    # Select booking data of the working days,
    # set booking data to the correct working days
    query = 'SELECT id, working_id, start, finish, note FROM booking ORDER BY start ASC, finish ASC;'
    cur.execute(query)

    rows = cur.fetchall()

    for row in rows:
        for i in range(0, len(working)):
            if working[i]["id"] == row[1]:
                working[i]["booking"].append({"id":row[0], "start":row[2], "finish":row[3], "note":row[4], "products":[]})
                break

    # Select booking products and set that data
    query = 'SELECT product_id, booking_id FROM booking_products;'
    cur.execute(query)

    rows = cur.fetchall()

    for row in rows:
        for i in range(0, len(working)):
            for k in range(0, len(working[i]["booking"])):
                if working[i]["booking"][k]["id"] == row[1]:
                    working[i]["booking"][k]["products"].append(row[0])

    # Go through the weeks data,
    # set working and booking data for the correct days
    for week in weeks:
        for day in week:
            for work in working:
                if "num" in day and work["date"].day == day["num"]:
                    day.update(work)

    # Just select products data
    query = 'SELECT id, name FROM products;'
    cur.execute(query)

    rows = cur.fetchall()

    products = []
    for row in rows:
        products.append({"id":row[0], "name":row[1]})

    # Select access codes
    query = 'SELECT code FROM access;'
    cur.execute(query)

    rows = cur.fetchall()

    access = []
    for row in rows:
        access.append(row[0])

    return render_template("index_new.html", weeks=weeks, products=products, products1=products, access=access, year=year, month=month)



# INTERNAL

# Internal method for setting the working schedule
@app.route("/internal/schedule", methods=["POST"])
def schedule():
    if "auth" not in session:
        return redirect("/login")

    conn = connect()
    cur = conn.cursor()

    data = request.get_json()

    year = data["year"]
    month = data["month"]
    start = data["start"]
    finish = data["finish"]
    days = data["days"]
    old = data["old"]

    # Delete existing working records, to replace afterwards
    query = 'DELETE FROM working WHERE id = %s;'
    for day in old:
        cur.execute(query, (day,))
        conn.commit()

    # Insert new working records
    query = 'INSERT INTO working(start, finish, date) VALUES(%s, %s, %s);'
    for day in days:
        cur.execute(query, (start, finish, day))
        conn.commit()

    cur.close()
    conn.close()

    return "true"

# Internal method for getting info of a single day
@app.route("/internal/day/get", methods=["POST"])
def get_day():
    if "auth" not in session:
        return redirect("/login")

    conn = connect()
    cur = conn.cursor()

    data = request.get_json()

    id = data["id"]

    # Select working data
    query = 'SELECT id, to_char(date, \'YYYY.MM.DD\'), to_char(start, \'HH24:MI\'), to_char(finish, \'HH24:MI\') FROM working WHERE id = %s;'
    cur.execute(query, (id,))

    row = cur.fetchone()

    day = {"id":row[0], "date":row[1], "start":row[2], "finish":row[3], "booking":[]}

    # Select booking data of the working day
    query = 'SELECT id, working_id, to_char(start, \'HH24:MI\'), to_char(finish, \'HH24:MI\'), name, email, note FROM booking WHERE working_id = %s;'
    cur.execute(query, (id,))

    rows = cur.fetchall()

    for row in rows:
        day["booking"].append({"id":row[0], "start":row[2], "finish":row[3], "name": row[4], "email": row[5], "note":row[6], "products":[]})

    # Select booking products and set that data
    for booking in day["booking"]:
        query = '''SELECT 
        booking_products.product_id,
        products.name FROM booking_products INNER JOIN products ON 
        booking_products.product_id = products.id WHERE booking_products.booking_id = %s;'''
        cur.execute(query, (booking["id"],))

        rows = cur.fetchall()

        for row in rows:
            booking["products"].append({"id":row[0], "name":row[1]})

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(day)

# Internal method for deleting day working records
@app.route("/internal/day/disable", methods=["POST"])
def disable_day():
    if "auth" not in session:
        return redirect("/login")

    conn = connect()
    cur = conn.cursor()

    id = request.form["id"]
    month= request.form["month"]
    year = request.form["year"]

    # Select working data
    query = 'DELETE FROM working WHERE id = %s;'
    cur.execute(query, (id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/?year=%s&month=%s" % (year, month))

# Internal method deleting a booking record
@app.route("/internal/booking/delete", methods=["POST"])
def delete_booking():
    if "auth" not in session:
        return redirect("/login")

    conn = connect()
    cur = conn.cursor()

    booking_id = request.form["id"]
    year = request.form["year"]
    month = request.form["month"]

    query = 'DELETE FROM booking WHERE id = %s;'
    cur.execute(query, (booking_id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/?year=%s&month=%s" % (year, month))

# Internal method for creating a new booking record
@app.route("/internal/booking/new", methods=["POST"])
def new_booking():
    if "auth" not in session:
        return redirect("/login")

    conn = connect()
    cur = conn.cursor()

    data = request.get_json()

    working_id = data["working_id"]
    year = data["year"]
    month = data["month"]
    oldStartStr = data["oldStart"]
    oldFinishStr = data["oldFinish"]
    startStr = data["start"]
    finishStr = data["finish"]
    name = data["name"]
    email = data["email"]
    note = data["note"]
    products = data["products"]

    oldStart = datetime.strptime(oldStartStr, "%H:%M")
    oldFinish = datetime.strptime(oldFinishStr, "%H:%M")
    start = datetime.strptime(startStr, "%H:%M")
    finish = datetime.strptime(finishStr, "%H:%M")

    if start < oldStart or finish > oldFinish:
        return redirect("/?year=%s&month=%s" % (year, month))

    # Insert new data
    query = 'INSERT INTO booking(working_id, start, finish, name, email, note) VALUES(%s, %s, %s, %s, %s, %s) RETURNING id;'
    cur.execute(query, (working_id, start, finish, name, email, note))
    booking_id = cur.fetchone()[0]
    conn.commit()

    query = 'INSERT INTO booking_products(booking_id, product_id) VALUES(%s, %s);'
    for product in products:
        cur.execute(query, (booking_id, product))
        conn.commit()

    cur.close()
    conn.close()

    return "true"

# Internal method for creating a new booking record from list
@app.route("/internal/booking/new2", methods=["POST"])
def new_booking2():
    if "auth" not in session:
        return redirect("/login")

    conn = connect()
    cur = conn.cursor()

    data = request.get_json()

    year = data["year"]
    month = data["month"]
    start = data["start"]
    finish = data["finish"]
    date = data["date"]
    name = data["name"]
    email = data["email"]
    note = data["note"]
    products = data["products"]

    # Get or create a new working record
    query = 'SELECT id FROM working WHERE date = %s;'
    cur.execute(query, (date,))
    working_id = ""
    row = cur.fetchone()

    if row == None:
        query = 'INSERT INTO working(start, finish, date) VALUES(%s, %s, %s) RETURNING id;'
        cur.execute(query, (start, finish, date))
        working_id = cur.fetchone()[0]
        conn.commit()
    else:
        working_id = row[0]

    # Insert new data
    query = 'INSERT INTO booking(working_id, start, finish, name, email, note) VALUES(%s, %s, %s, %s, %s, %s) RETURNING id;'
    cur.execute(query, (working_id, start, finish, name, email, note))
    booking_id = cur.fetchone()[0]
    conn.commit()

    query = 'INSERT INTO booking_products(booking_id, product_id) VALUES(%s, %s);'
    for product in products:
        cur.execute(query, (booking_id, product))
        conn.commit()

    cur.close()
    conn.close()

    return "true"

# Internal method for editing an existing booking record
@app.route("/internal/booking/edit", methods=["POST"])
def edit_booking():
    if "auth" not in session:
        return redirect("/login")

    conn = connect()
    cur = conn.cursor()

    data = request.get_json()

    booking_id = data["booking_id"]
    start = data["start"]
    finish = data["finish"]
    name = data["name"]
    email = data["email"]
    note = data["note"]
    products = data["products"]

    query = 'UPDATE booking SET start = %s, finish = %s, name = %s, email = %s, note = %s WHERE id = %s;'
    cur.execute(query, (start, finish, name, email, note, booking_id))
    conn.commit()

    query = 'DELETE FROM booking_products WHERE booking_id = %s;'
    cur.execute(query, (booking_id,))
    conn.commit()
    
    query = 'INSERT INTO booking_products(booking_id, product_id) VALUES(%s, %s);'
    for product in products:
        cur.execute(query, (booking_id, product))
        conn.commit()

    cur.close()
    conn.close()

    return "true"

# Internal method for getting a list of booking records
@app.route("/internal/booking/list", methods=["POST"])
def list_booking():
    if "auth" not in session:
        return redirect("/login")

    conn = connect()
    cur = conn.cursor()

    query = '''SELECT 
    booking.id, 
    booking.working_id, 
    to_char(working.date, \'YYYY.MM.DD\'), 
    to_char(booking.start, \'HH24:MI\'), 
    to_char(booking.finish, \'HH24:MI\'), 
    booking.name, 
    booking.email, 
    booking.note FROM booking INNER JOIN working ON 
    booking.working_id = working.id;'''
    cur.execute(query)

    booking = []
    rows = cur.fetchall()
    for row in rows:
        booking.append({"id":row[0], "working_id":row[1], "date":row[2], "start":row[3], "finish":row[4], "name":row[5], "email":row[6], "note":row[7], "products":[]})

    for book in booking:
        query = '''SELECT 
        booking_products.product_id,
        products.name FROM booking_products INNER JOIN products ON 
        booking_products.product_id = products.id WHERE booking_products.booking_id = %s;'''
        cur.execute(query, (book["id"],))

        rows = cur.fetchall()

        for row in rows:
            book["products"].append({"id":row[0], "name":row[1]})

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(booking)

# Internal method for getting a list of booking records
@app.route("/internal/booking/get", methods=["POST"])
def get_booking():
    if "auth" not in session:
        return redirect("/login")

    conn = connect()
    cur = conn.cursor()

    data = request.get_json()
    booking_id = data["booking_id"]

    query = '''SELECT 
    booking.id, 
    booking.working_id, 
    to_char(booking.start, \'HH24:MI\'), 
    to_char(booking.finish, \'HH24:MI\'), 
    booking.name, 
    booking.email, 
    booking.note FROM booking WHERE booking.id = %s;'''
    cur.execute(query, (booking_id,))

    row = cur.fetchone()
    booking = {"id":row[0], "working_id":row[1], "start":row[2], "finish":row[3], "name":row[4], "email":row[5], "note":row[6], "products":[]}

    query = '''SELECT 
    booking_products.product_id,
    products.name FROM booking_products INNER JOIN products ON 
    booking_products.product_id = products.id WHERE booking_products.booking_id = %s;'''
    cur.execute(query, (booking_id,))

    rows = cur.fetchall()

    for row in rows:
        booking["products"].append({"id":row[0], "name":row[1]})

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(booking)

# New product creation method
@app.route("/internal/products/new", methods=["POST"])
def new_product():
    if "auth" not in session:
        return redirect("/login")

    name = request.form["name"]
    year = request.form["year"]
    month = request.form["month"]
    
    conn = connect()
    cur = conn.cursor()

    query = 'INSERT INTO products(name) VALUES(%s);'
    cur.execute(query, (name,))
    
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/?year=%s&month=%s" % (year, month))

# Product deletion method
@app.route("/internal/products/delete", methods=["POST"])
def delete_product():
    if "auth" not in session:
        return redirect("/login")

    id = request.form["id"]
    year = request.form["year"]
    month = request.form["month"]

    conn = connect()
    cur = conn.cursor()

    query = 'DELETE FROM products WHERE id = %s;'
    cur.execute(query, (id,))
    
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/?year=%s&month=%s" % (year, month))

# New access code creation method
@app.route("/internal/access/new", methods=["POST"])
def new_access():
    if "auth" not in session:
        return redirect("/login")

    year = request.form["year"]
    month = request.form["month"]

    conn = connect()
    cur = conn.cursor()

    query = 'INSERT INTO access DEFAULT VALUES;'
    cur.execute(query)
    
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/?year=%s&month=%s" % (year, month))

# Access code deletion method
@app.route("/internal/access/delete", methods=["POST"])
def delete_access():
    if "auth" not in session:
        return redirect("/login")

    code = request.form["code"]
    year = request.form["year"]
    month = request.form["month"]

    conn = connect()
    cur = conn.cursor()

    query = 'DELETE FROM access WHERE code = %s;'
    cur.execute(query, (code,))
    
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/?year=%s&month=%s" % (year, month))





# RUN
if __name__ == "__main__":
    app.run(port=5000)