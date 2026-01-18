import os

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
