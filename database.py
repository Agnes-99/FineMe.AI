import sqlite3
import os

DB_PATH = "static/database/missing_people.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS missing_people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            filename TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def add_missing_person(name, filename):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO missing_people (name, filename) VALUES (?, ?)', (name, filename))
        conn.commit()
    except sqlite3.IntegrityError:
        # If the person already exists, update the filename
        c.execute('UPDATE missing_people SET filename = ? WHERE name = ?', (filename, name))
        conn.commit()
    finally:
        conn.close()


def load_missing_people():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name, filename FROM missing_people')
    results = c.fetchall()
    conn.close()
    return [{"name": name, "filename": filename} for name, filename in results]


def get_missing_person_by_name(name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name, filename FROM missing_people WHERE name = ?', (name,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"name": row[0], "filename": row[1]}
    return None