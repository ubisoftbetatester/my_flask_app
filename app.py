import difflib
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE,
                    role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS missing_material (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    quantity INTEGER,
                    description TEXT,
                    delivery_time TEXT,
                    notes TEXT,
                    resolved BOOLEAN)''')
    c.execute('''CREATE TABLE IF NOT EXISTS preparations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    description TEXT,
                    notes TEXT,
                    resolved BOOLEAN)''')
    c.execute('''CREATE TABLE IF NOT EXISTS others (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    resolved BOOLEAN)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT,
                    record_id INTEGER,
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_code TEXT)''')
    conn.commit()
    conn.close()

def make_diff(old_text, new_text):
    return "\n".join(difflib.ndiff(old_text.splitlines(), new_text.splitlines()))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    code = request.form["code"]
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE code = ?", (code,))
    user = c.fetchone()
    conn.close()
    if user:
        session["code"] = code
        session["role"] = user[0]
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if "code" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html")

@app.route("/missing_material")
def missing_material():
    if "code" not in session:
        return redirect(url_for("index"))
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM missing_material")
    materials = c.fetchall()
    conn.close()
    return render_template("missing_material.html", materials=materials)

@app.route("/preparations")
def preparations():
    if "code" not in session:
        return redirect(url_for("index"))
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM preparations")
    preparations = c.fetchall()
    conn.close()
    return render_template("preparations.html", preparations=preparations)

@app.route("/others")
def others():
    if "code" not in session:
        return redirect(url_for("index"))
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM others")
    others = c.fetchall()
    conn.close()
    return render_template("others.html", others=others)

@app.route("/edit_record/<section>/<int:id>", methods=["GET", "POST"])
def edit_record(section, id):
    if "code" not in session:
        return redirect(url_for("index"))
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    if request.method == "POST":
        if section == "missing_material":
            c.execute("SELECT * FROM missing_material WHERE id = ?", (id,))
            old = c.fetchone()
            new = (
                request.form["code"],
                request.form["quantity"],
                request.form["description"],
                request.form["delivery_time"],
                request.form["notes"],
                request.form["resolved"] == "yes"
            )
            c.execute('''UPDATE missing_material SET
                            code = ?, quantity = ?, description = ?, delivery_time = ?, notes = ?, resolved = ?
                            WHERE id = ?''', (*new, id))
            c.execute('''INSERT INTO history (table_name, record_id, field_name, old_value, new_value, user_code)
                        VALUES (?, ?, ?, ?, ?, ?)''', ('missing_material', id, 'all_fields', str(old), str(new), session["code"]))
        elif section == "preparations":
            c.execute("SELECT * FROM preparations WHERE id = ?", (id,))
            old = c.fetchone()
            new = (
                request.form["code"],
                request.form["description"],
                request.form["notes"],
                request.form["resolved"] == "yes"
            )
            c.execute('''UPDATE preparations SET
                            code = ?, description = ?, notes = ?, resolved = ?
                            WHERE id = ?''', (*new, id))
            c.execute('''INSERT INTO history (table_name, record_id, field_name, old_value, new_value, user_code)
                        VALUES (?, ?, ?, ?, ?, ?)''', ('preparations', id, 'all_fields', str(old), str(new), session["code"]))
        elif section == "others":
            c.execute("SELECT * FROM others WHERE id = ?", (id,))
            old = c.fetchone()
            new = (
                request.form["content"],
                request.form["resolved"] == "yes"
            )
            c.execute('''UPDATE others SET
                            content = ?, resolved = ?
                            WHERE id = ?''', (*new, id))
            c.execute('''INSERT INTO history (table_name, record_id, field_name, old_value, new_value, user_code)
                        VALUES (?, ?, ?, ?, ?, ?)''', ('others', id, 'all_fields', str(old), str(new), session["code"]))
        conn.commit()
        conn.close()
        return redirect(url_for(f"{section}s"))
    else:
        if section == "missing_material":
            c.execute("SELECT * FROM missing_material WHERE id = ?", (id,))
            record = c.fetchone()
            conn.close()
            return render_template("edit_record.html", section=section, record=record)
        elif section == "preparations":
            c.execute("SELECT * FROM preparations WHERE id = ?", (id,))
            record = c.fetchone()
            conn.close()
            return render_template("edit_record.html", section=section, record=record)
        elif section == "others":
            c.execute("SELECT * FROM others WHERE id = ?", (id,))
            record = c.fetchone()
            conn.close()
            return render_template("edit_record.html", section=section, record=record)

@app.route("/history/<section>")
def view_history(section):
    if "code" not in session:
        return redirect(url_for("index"))
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE table_name = ? ORDER BY timestamp DESC", (section,))
    changes = c.fetchall()
    conn.close()
    return render_template("history.html", changes=changes)

if __name__ == "__main__":
    init_db()
