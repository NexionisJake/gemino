import os

# NOTE: Assuming a database driver object 'db' which supports parameterized queries (e.g., using '?' placeholders).

# Mock setup for runnable context (In a real application, this class is external)
class MockDB:
    def execute(self, query, params=None):
        # Simulate successful retrieval if parameters match
        if params == ('admin', 'securepass'):
            return [{"id": 1, "username": "admin"}]
        return []

db = MockDB()

def login(username, password):
    # Using parameterized queries to ensure user input is treated as data, not executable SQL.
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    params = (username, password)
    return db.execute(query, params)