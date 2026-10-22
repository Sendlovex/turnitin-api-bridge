import argparse
import json
import os
import re
import sys
from bs4 import BeautifulSoup
import requests

BASE_URL = "https://edu-turnitin.com"
SIGNIN_URL = f"{BASE_URL}/home/signin"

def inspect_portal(username, password):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": f"{BASE_URL}/home"
    })

    print(f"[*] Navigating to {BASE_URL}/home...")
    init_res = session.get(f"{BASE_URL}/home")
    print(f"[*] Initial Session Cookies: {session.cookies.get_dict()}")

    print(f"[*] Attempting login with username: {username}...")
    payload = {
        "form_type": "login",
        "username": username,
        "password": password
    }

    login_res = session.post(SIGNIN_URL, data=payload, allow_redirects=True)
    print(f"[*] Post-login Status: {login_res.status_code}")
    print(f"[*] Post-login URL: {login_res.url}")

    if "Invalid username or password" in login_res.text:
        print("[-] Login failed: Invalid username or password.")
        sys.exit(1)

    soup = BeautifulSoup(login_res.text, "html.parser")
    title = soup.title.string if soup.title else "No Title"
    print(f"[+] Login successful! Page title: '{title}'")
    print(f"[+] Authenticated Cookies: {session.cookies.get_dict()}")

    # Save dashboard HTML for offline inspection
    output_html = "dashboard_dump.html"
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(login_res.text)
    print(f"[+] Saved dashboard HTML to {output_html}")

    # Inspect forms
    forms = soup.find_all("form")
    print(f"\n[+] Found {len(forms)} form(s) on dashboard:")
    for idx, f in enumerate(forms, start=1):
        action = f.get("action", "")
        method = f.get("method", "GET").upper()
        enctype = f.get("enctype", "application/x-www-form-urlencoded")
        inputs = [{"name": inp.get("name"), "type": inp.get("type"), "id": inp.get("id")} for inp in f.find_all(["input", "select", "textarea"])]
        print(f"    Form #{idx}: method={method}, action={action}, enctype={enctype}")
        print(f"    Inputs: {json.dumps(inputs, indent=6)}")

    # Inspect tables / lists for submission rows
    tables = soup.find_all("table")
    print(f"\n[+] Found {len(tables)} table(s) on dashboard.")
    for idx, t in enumerate(tables, start=1):
        headers = [th.get_text(strip=True) for th in t.find_all(["th"])]
        rows = t.find_all("tr")
        print(f"    Table #{idx}: Headers={headers}, Rows={len(rows)}")

    # Inspect links for potential upload / assignments / reports
    nav_links = [{"text": a.get_text(strip=True), "href": a.get("href")} for a in soup.find_all("a", href=True) if any(k in a.get("href", "").lower() or k in a.get_text(strip=True).lower() for k in ["upload", "submit", "assignment", "report", "ai", "similarity", "dashboard", "file"])]
    print(f"\n[+] Relevant navigation links found: {len(nav_links)}")
    for l in nav_links[:10]:
        print(f"    - {l['text']} -> {l['href']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect edu-turnitin.com account portal structure")
    parser.add_argument("--username", "-u", default=os.getenv("EDU_TURNITIN_USER"), help="Instructor username")
    parser.add_argument("--password", "-p", default=os.getenv("EDU_TURNITIN_PASS"), help="Instructor password")
    args = parser.parse_args()

    if not args.username or not args.password:
        print("Usage: python inspect_portal.py --username <USER> --password <PASS>")
        sys.exit(1)

    inspect_portal(args.username, args.password)
