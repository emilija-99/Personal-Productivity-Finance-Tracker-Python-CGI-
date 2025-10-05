#!C:/Users/Emilija/AppData/Local/Programs/Python/Python311/python.exe
import sys, cgi, cgitb, bcrypt, sqlite3, secrets
from db import getConnection
import urllib.parse
cgitb.enable()

LOGIN_URL = "http://localhost/Web-programiranje-1/Zabac/templates/login.html"
HOME_URL  = "http://localhost/Web-programiranje-1/Zabac/templates/index.html"

def make_cookie(name, value, path='/', max_age=None, http_only=True, same_site="Lax"):
    parts = [f"{name}={value}", f"Path={path}"]
    if max_age is not None: parts.append(f"Max-Age={max_age}")
    if http_only: parts.append("HttpOnly")
    if same_site: parts.append(f"SameSite={same_site}")
    return "; ".join(parts)

def redirect(url, set_cookies=None, status="303 See Other"):
    sys.stdout.write(f"Status: {status}\r\n")
    if set_cookies:
        for c in set_cookies:
            sys.stdout.write(f"Set-Cookie: {c}\r\n")
    sys.stdout.write(f"Location: {url}\r\n\r\n")
    sys.stdout.flush()
    raise SystemExit


form = cgi.FieldStorage()
username = (form.getvalue('username') or '').strip()
password = (form.getvalue('password') or '')
remember = (form.getvalue('remember') or 'off').strip()  

if not username or not password:
    redirect(f"{LOGIN_URL}?error=missing")

conn = getConnection()
cur = conn.cursor()

# FETCH USER
cur.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
row = cur.fetchone()

if not row or not bcrypt.checkpw(password.encode('utf-8'), row['password_hash'].encode('utf-8')):
    print("Content-Type: text/html; charset=utf-8")
    print()
    print(f"""
    <html>
    <head><title>Login Failed</title></head>
    <body>
      <p style="color:red">Invalid username or password!</p>
      <a href="{LOGIN_URL}">Try again</a>
    </body>
    </html>
    """)
    conn.close()
    raise SystemExit
    
user_id = row['id']

# create data for inserting session into db
now = sqlite3.datetime.datetime.now().isoformat()
expire = sqlite3.datetime.datetime.now() + sqlite3.datetime.timedelta(days=30)
sid = secrets.token_urlsafe(32)

cur.execute("INSERT INTO session (sid, user_id, expires_at, created_at, remember) VALUES (?, ?, ?, ?, ?)", (sid, user_id, expire, now,  1 if remember else 0))
conn.commit()

# set username and session_id into cookies
cookies = [make_cookie("username", username, max_age=30*24*3600) if remember == 'on' else make_cookie("username", username)]
cookies.append(make_cookie("session_id", str(sid), max_age=30*24*3600 if remember == 'on' else None))

redirect(HOME_URL, set_cookies=cookies)
conn.close()