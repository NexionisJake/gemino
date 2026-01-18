import sqlite3
import os

# Ensure target directory exists
if not os.path.exists('target_code'):
    os.makedirs('target_code')

db_path = 'target_code/db.sqlite'
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('''CREATE TABLE users (user text, pass text)''')
c.execute("INSERT INTO users VALUES ('admin', 'supersecret')")
conn.commit()
conn.close()
print("DB Seeded.")
