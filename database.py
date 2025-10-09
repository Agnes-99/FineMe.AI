import sqlite3
import pickle

def init_db():
    conn = sqlite3.connect("faces.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS missing_people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        encoding BLOB NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def add_missing_person(name, file_path, encoding):
    conn = sqlite3.connect("faces.db")
    cursor = conn.cursor()
    # Store encoding as pickled blob
    encoding_blob = pickle.dumps(encoding)
    cursor.execute(
        "INSERT INTO missing_people (name, file_path, encoding) VALUES (?, ?, ?)",
        (name, file_path, encoding_blob)
    )
    conn.commit()
    conn.close()

def load_missing_people():
    conn = sqlite3.connect("faces.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, file_path, encoding FROM missing_people")
    results = []
    for name, file_path, enc_blob in cursor.fetchall():
        try:
            encoding = pickle.loads(enc_blob)  # ✅ Unpickle encoding
            results.append((name, file_path, encoding))
        except Exception as e:
            print(f"[ERROR] Failed to unpickle encoding for {name}: {e}")
    conn.close()
    return results