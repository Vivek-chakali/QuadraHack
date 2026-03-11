from flask import Flask, render_template, request, redirect, session
import sqlite3
import datetime
import smtplib
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "supersecretkey"

# ---------------------------
# EMAIL CONFIG (EDIT THIS)
# ---------------------------
SENDER_EMAIL = "vivekchakali16@gmail.com"
APP_PASSWORD = "ojqekdzkjyndfzkz"
RECEIVER_EMAIL = "shravyachakali4@gmail.com"

# ---------------------------
# DATABASE INITIALIZATION
# ---------------------------
def init_db():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
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
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        ("admin", "admin123", "admin")
    )

    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        ("staff", "staff123", "staff")
    )

    conn.commit()
    conn.close()

init_db()

# ---------------------------
# EMAIL FUNCTION
# ---------------------------
def send_email_alert(item_name, quantity):
    subject = f"Restock Alert: {item_name}"
    body = f"Stock for {item_name} is low.\nCurrent quantity: {quantity}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("EMAIL SENT SUCCESSFULLY")

    except Exception as e:
        print("Email failed:", e)

# ---------------------------
# BACKGROUND INVENTORY CHECK
# ---------------------------
def check_inventory_levels():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, item_name, quantity, threshold FROM inventory")
    items = cursor.fetchall()

    for item in items:
        item_id, name, qty, threshold = item

        if qty <= threshold:

            cursor.execute("""
                SELECT * FROM restock_logs
                WHERE item_id=?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (item_id,))
            last_log = cursor.fetchone()

            if not last_log:
                restock_qty = threshold * 2

                cursor.execute("""
                    INSERT INTO restock_logs
                    (item_id, restock_quantity, timestamp)
                    VALUES (?, ?, ?)
                """, (item_id, restock_qty, datetime.datetime.now()))

                send_email_alert(name, qty)
                print("Background restock triggered for", name)

    conn.commit()
    conn.close()

# ---------------------------
# LOGIN ROUTE
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username=? AND password=?",
                       (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["role"] = user[0]
            return redirect("/admin" if user[0] == "admin" else "/staff")

        return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html")

# ---------------------------
# ADMIN DASHBOARD
# ---------------------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()
    conn.close()

    processed_items = []
    for item in items:
        status = "Normal"
        if item[2] <= item[3]:
            status = "Low"
        if item[2] <= item[3] // 2:
            status = "Critical"

        processed_items.append((*item, status))

    return render_template("admin.html", items=processed_items)

# ---------------------------
# ADD INVENTORY
# ---------------------------
@app.route("/add_item", methods=["POST"])
def add_item():
    if session.get("role") != "admin":
        return redirect("/")

    item_name = request.form["item_name"]
    quantity = int(request.form["quantity"])
    threshold = int(request.form["threshold"])

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO inventory (item_name, quantity, threshold, last_updated)
        VALUES (?, ?, ?, ?)
    """, (item_name, quantity, threshold, datetime.datetime.now()))

    conn.commit()
    conn.close()

    return redirect("/admin")

# ---------------------------
# SELL ITEM
# ---------------------------
@app.route("/sell_item/<int:item_id>", methods=["POST"])
def sell_item(item_id):
    if session.get("role") != "admin":
        return redirect("/")

    sold_qty = int(request.form["sold_qty"])

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("SELECT quantity, threshold FROM inventory WHERE id=?",
                   (item_id,))
    item = cursor.fetchone()

    if item:
        current_qty, threshold = item
        new_qty = max(current_qty - sold_qty, 0)

        cursor.execute("""
            UPDATE inventory
            SET quantity=?, last_updated=?
            WHERE id=?
        """, (new_qty, datetime.datetime.now(), item_id))

        conn.commit()

    conn.close()
    return redirect("/admin")

# ---------------------------
# STAFF DASHBOARD
# ---------------------------
@app.route("/staff")
def staff():
    if session.get("role") != "staff":
        return redirect("/")

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()

    cursor.execute("SELECT * FROM restock_logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()

    conn.close()

    processed_items = []
    normal = low = critical = 0

    for item in items:
        status = "Normal"
        if item[2] <= item[3]:
            status = "Low"
        if item[2] <= item[3] // 2:
            status = "Critical"

        if status == "Normal":
            normal += 1
        elif status == "Low":
            low += 1
        else:
            critical += 1

        processed_items.append((*item, status))

    return render_template("staff.html",
                           items=processed_items,
                           logs=logs,
                           total_items=len(processed_items),
                           normal=normal,
                           low=low,
                           critical=critical)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------------------
# START SCHEDULER
# ---------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(check_inventory_levels, "interval", seconds=10)
scheduler.start()
print("Scheduler started — checking every 10 seconds")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
