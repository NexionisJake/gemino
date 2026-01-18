import sqlite3

def login(username, password):
    # SECURE FIX: Use parameterized query (? placeholders) to prevent SQL Injection.
    # The database driver handles safe escaping of the inputs.
    query = "SELECT * FROM users WHERE user = ? AND pass = ?"
    
    # It is a best practice to use context managers for database connections
    with sqlite3.connect('db.sqlite') as conn:
        cursor = conn.cursor()
        # Pass parameters as a tuple separate from the query string
        cursor.execute(query, (username, password))
        return cursor.fetchone()