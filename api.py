from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

# 🟢 REGISTER API
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = generate_password_hash(data.get('password'))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
    except:
        conn.close()
        return jsonify({"error": "User already exists"}), 400

    conn.close()
    return jsonify({"message": "User registered"})


# 🟢 LOGIN API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cur.fetchone()

    conn.close()

    if user and check_password_hash(user[2], password):
        return jsonify({"message": "Login successful", "user_id": user[0]})
    else:
        return jsonify({"error": "Invalid credentials"}), 401


# 🟢 GET NOTES
@app.route('/api/notes', methods=['GET'])
def get_notes():
    user_id = request.args.get('user_id')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM notes WHERE user_id=%s", (user_id,))
    notes = cur.fetchall()

    conn.close()

    result = []
    for note in notes:
        result.append({
            "id": note[0],
            "text": note[2],
            "created_at": str(note[3])
        })

    return jsonify(result)


# 🟢 ADD NOTE
@app.route('/api/notes', methods=['POST'])
def add_note():
    data = request.json
    user_id = data.get('user_id')
    text = data.get('text')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO notes (user_id, text) VALUES (%s, %s)", (user_id, text))
    conn.commit()

    conn.close()

    return jsonify({"message": "Note added"})


# 🟢 UPDATE NOTE
@app.route('/api/notes/<int:id>', methods=['PUT'])
def update_note(id):
    data = request.json
    text = data.get('text')
    user_id = data.get('user_id')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE notes SET text=%s WHERE id=%s AND user_id=%s",
        (text, id, user_id)
    )
    conn.commit()

    conn.close()

    return jsonify({"message": "Note updated"})


# 🟢 DELETE NOTE
@app.route('/api/notes/<int:id>', methods=['DELETE'])
def delete_note(id):
    user_id = request.args.get('user_id')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM notes WHERE id=%s AND user_id=%s",
        (id, user_id)
    )
    conn.commit()

    conn.close()

    return jsonify({"message": "Note deleted"})


if __name__ == "__main__":
    app.run(debug=True)
