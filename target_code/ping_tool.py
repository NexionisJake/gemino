import os

def ping_host(hostname):
    print(f"Pinging {hostname}")
    # Vulnerable to command injection
    os.system(f"ping -c 1 {hostname}")
