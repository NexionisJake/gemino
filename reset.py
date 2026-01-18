import os
import shutil

# Template files content
LOGIN_VULNERABLE = '''import sqlite3

def login(username, password):
    # VULNERABILITY: SQL Injection
    query = f"SELECT * FROM users WHERE user = '{username}' AND pass = '{password}'"
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()
'''

PING_VULNERABLE = '''import os

def ping_host(hostname):
    """
    Pings a hostname to check if it's alive.
    """
    # VULNERABILITY: Command Injection
    # The 'hostname' input is directly concatenated into the shell command string.
    command = f"ping -c 1 {hostname}"
    
    # Using os.system is often dangerous with untrusted input
    exit_code = os.system(command)
    return exit_code == 0
'''

def reset_login():
    path = os.path.join("target_code", "login.py")
    with open(path, "w") as f:
        f.write(LOGIN_VULNERABLE)
    print(f"✓ Reset {path} to vulnerable state.")

def reset_ping():
    path = os.path.join("target_code", "ping_tool.py")
    with open(path, "w") as f:
        f.write(PING_VULNERABLE)
    print(f"✓ Reset {path} to vulnerable state.")

def clean_tests():
    folder = "target_code"
    removed = 0
    for f in os.listdir(folder):
        if f.startswith("test_") and f.endswith(".py"):
            os.remove(os.path.join(folder, f))
            removed += 1
    if removed:
        print(f"✓ Removed {removed} test file(s).")

def clean_backups():
    folder = "target_code"
    removed = 0
    for f in os.listdir(folder):
        if f.endswith(".bak"):
            os.remove(os.path.join(folder, f))
            removed += 1
    if removed:
        print(f"✓ Removed {removed} backup file(s).")

def clean_reports():
    folder = "reports"
    if os.path.exists(folder):
        for f in os.listdir(folder):
            os.remove(os.path.join(folder, f))
        print(f"✓ Cleared reports folder.")

if __name__ == "__main__":
    print("🟣 PurpleVibe Demo Reset")
    print("-" * 30)
    reset_login()
    reset_ping()
    clean_tests()
    clean_backups()
    clean_reports()
    print("-" * 30)
    print("✓ Environment ready for demo!")
