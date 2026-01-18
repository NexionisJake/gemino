import sqlite3

def login(username, password):
    # VULNERABILITY: SQL Injection
    query = f"SELECT * FROM users WHERE user = '{username}' AND pass = '{password}'"
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()
