import sqlite3

def connect_db():
    conn = sqlite3.connect('football.db')
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=()):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid

def fetch_query(query, params=()):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def fetch_one_query(query, params=()):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None