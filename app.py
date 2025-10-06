import os
import sqlite3
import numpy as np
import face_recognition  
import pickle
from flask import Flask, render_template, request, url_for

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

DB_PATH = "faces.db"

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    image_path TEXT,
                    encoding BLOB,
                    category TEXT)''')
    conn.commit()
    conn.close()


init_db()


# Save face data
def save_face(name, image_path, encoding, category):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO faces (name, image_path, encoding, category) VALUES (?, ?, ?, ?)",
              (name, image_path, encoding.dumps(), category))
    conn.commit()
    conn.close()


# Load stored faces
def load_faces(category=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if category:
        c.execute("SELECT name, image_path, encoding FROM faces WHERE category=?", (category,))
    else:
        c.execute("SELECT name, image_path, encoding FROM faces")
    data = c.fetchall()
    conn.close()
    return [(name, path, pickle.loads(enc)) for name, path, enc in data]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload_missing", methods=["POST"])
def upload_missing():
    file = request.files["file"]
    name = request.form.get("name", "Unknown")
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    img = face_recognition.load_image_file(filepath)
    encodings = face_recognition.face_encodings(img)
    if not encodings:
        return "No face detected. Try another image."

    save_face(name, filepath, np.array(encodings[0]), "missing")
    return f"✅ {name} has been added to the missing persons database."


@app.route("/upload_found", methods=["POST"])
def upload_found():
    file = request.files["file"]
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    unknown_img = face_recognition.load_image_file(filepath)
    unknown_encs = face_recognition.face_encodings(unknown_img)
    if not unknown_encs:
        return "No face detected."

    unknown_enc = unknown_encs[0]
    known_faces = load_faces(category="missing")

    matches = []
    for name, path, known_enc in known_faces:
        distance = face_recognition.face_distance([known_enc], unknown_enc)[0]
        if distance < 0.6:  # Lower is stricter
          confidence = round((1 - distance) * 100, 2)
          matches.append((name, path, confidence))

    if matches:
        return render_template("matches.html", matches=matches)
    else:
        return "❌ No matches found."


if __name__ == "__main__":
    app.run(debug=True)