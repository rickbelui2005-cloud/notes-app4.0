from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ✅ PostgreSQL connection
def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

# ✅ Create tables
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# 🟢 REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
        except:
            conn.close()
            return "Username already exists"

        conn.close()
        return redirect('/login')

    return render_template('register.html')


# 🟢 LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect('/')
        else:
            return "Invalid username or password"

    return render_template('login.html')


# 🟢 HOME (Add + Show Notes)
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        note = request.form['note']
        cur.execute(
            "INSERT INTO notes (user_id, text) VALUES (%s, %s)",
            (session['user_id'], note)
        )
        conn.commit()

    cur.execute(
        "SELECT * FROM notes WHERE user_id=%s ORDER BY id DESC",
        (session['user_id'],)
    )
    notes = cur.fetchall()

    conn.close()

    return render_template('index.html', notes=notes)


# 🟢 DELETE
@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM notes WHERE id=%s AND user_id=%s",
        (id, session['user_id'])
    )

    conn.commit()
    conn.close()

    return redirect('/')


# 🟢 EDIT
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        new_text = request.form['note']
        cur.execute(
            "UPDATE notes SET text=%s WHERE id=%s AND user_id=%s",
            (new_text, id, session['user_id'])
        )
        conn.commit()
        conn.close()
        return redirect('/')

    cur.execute(
        "SELECT * FROM notes WHERE id=%s AND user_id=%s",
        (id, session['user_id'])
    )
    note = cur.fetchone()

    conn.close()

    return render_template('edit.html', note=note)


# 🟢 LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == "__main__":
    app.run(debug=True)