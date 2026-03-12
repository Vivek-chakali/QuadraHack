from flask import Flask, render_template, request, redirect, session
import sqlite3
import datetime
import smtplib
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -----------------------
# EMAIL CONFIG
# -----------------------
SENDER_EMAIL = "vivekchakali16@gmail.com"
APP_PASSWORD = "your_app_password"

# -----------------------
# DATABASE INIT
# -----------------------
def init_db():

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        email TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT,
        quantity INTEGER,
        threshold INTEGER,
        last_updated TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restock_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        restock_quantity INTEGER,
        timestamp TEXT
    )
    """)

    cursor.execute(
        "INSERT OR IGNORE INTO users (username,password,role) VALUES (?,?,?)",
        ("admin","admin123","admin")
    )

    cursor.execute(
        "INSERT OR IGNORE INTO users (username,password,role) VALUES (?,?,?)",
        ("staff","staff123","staff")
    )

    conn.commit()
    conn.close()

init_db()

# -----------------------
# SEND EMAIL
# -----------------------
def send_email_alert(item_name, quantity):

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE email IS NOT NULL AND alerts=1")
    emails = cursor.fetchall()

    conn.close()

    for email in emails:

        subject = f"Restock Alert: {item_name}"
        body = f"Stock for {item_name} is LOW.\nCurrent quantity: {quantity}"

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = email[0]

        try:

            server = smtplib.SMTP("smtp.gmail.com",587)
            server.starttls()
            server.login(SENDER_EMAIL,APP_PASSWORD)

            server.sendmail(SENDER_EMAIL,email[0],msg.as_string())

            server.quit()

            print("Email sent to",email[0])

        except Exception as e:

            print("Email error:",e)

# -----------------------
# INVENTORY CHECK
# -----------------------
def check_inventory_levels():

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id,item_name,quantity,threshold FROM inventory")

    items = cursor.fetchall()

    for item in items:

        item_id,name,qty,threshold = item

        if qty <= threshold:

            send_email_alert(name,qty)

    conn.close()

# -----------------------
# HOME PAGE
# -----------------------
@app.route("/")
def home():

    return render_template("home.html")

# -----------------------
# LOGIN
# -----------------------
@app.route("/login", methods=["GET", "POST"])
def login():


    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        email = request.form.get("email")
        alerts = 1 if request.form.get("alerts") else 0

        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()

        if user:

            # SAVE EMAIL + ALERT PREFERENCE
            if email:
                cursor.execute(
                    "UPDATE users SET email=?, alerts=? WHERE username=?",
                    (email, alerts, username)
                )
                conn.commit()

            session["role"] = user[0]

            if user[0] == "admin":
                return redirect("/admin")
            else:
                return redirect("/staff")

        conn.close()

        return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html")
# -----------------------
# ADMIN DASHBOARD
# -----------------------
@app.route("/admin")
def admin():

    if session.get("role") != "admin":
        return redirect("/login")

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inventory")

    items = cursor.fetchall()

    conn.close()

    return render_template("admin.html",items=items)

# -----------------------
# ADD ITEM
# -----------------------
@app.route("/add_item",methods=["POST"])
def add_item():

    item_name = request.form["item_name"]
    quantity = request.form["quantity"]
    threshold = request.form["threshold"]

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO inventory (item_name,quantity,threshold,last_updated)
    VALUES (?,?,?,?)
    """,(item_name,quantity,threshold,datetime.datetime.now()))

    conn.commit()
    conn.close()

    return redirect("/admin")

# -----------------------
# STAFF PAGE
# -----------------------
@app.route("/staff")
def staff():

    if session.get("role") != "staff":
        return redirect("/login")

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inventory")

    items = cursor.fetchall()

    conn.close()

    return render_template("staff.html",items=items)

# -----------------------
# LOGOUT
# -----------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# -----------------------
# SCHEDULER
# -----------------------
scheduler = BackgroundScheduler()

scheduler.add_job(check_inventory_levels,"interval",seconds=20)

scheduler.start()

print("Inventory monitor running...")

# -----------------------
# RUN APP
# -----------------------
if __name__ == "__main__":

    app.run(host="0.0.0.0",port=10000)