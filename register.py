#!C:/Users/Emilija/AppData/Local/Programs/Python/Python311/python.exe
import sys, cgi, cgitb, bcrypt, sqlite3, datetime
from db import getConnection
import re

cgitb.enable()

ERROR_URL   = "http://localhost/Web-programiranje-1/Zabac/templates/register.html"
SUCCESS_URL = "http://localhost/Web-programiranje-1/Zabac/templates/login.html"

def out_header():
    print("ERROR:")

def html_header(status=None):
    if status:
        print(f"Status: {status}")
    print("Content-Type: text/html; charset=utf-8")
    print()

def redirect(url):
    sys.stdout.write(f"Location: {url}\r\n\r\n")

def validate_inputs(username, email, password, confirm):
    errors = []

    if not (username and email and password and confirm):
        errors.append("All fields are required.")

    if password != confirm:
        errors.append("Passwords do not match.")

    # At least 8, at most 20, at least one digit, at least one special char
    special_rx = re.compile(r'[@_!#$%^&*()<>?/\|}{~:\-\+=\[\];.,]')
    if not (8 <= len(password) <= 20):
        errors.append("Password length must be between 8 and 20 characters.")
    if not re.search(r'\d', password or ""):
        errors.append("Password must contain at least one digit.")
    if not special_rx.search(password or ""):
        errors.append("Password must contain at least one special character.")

    return errors
def __main__():
    form = cgi.FieldStorage()

    username = (form.getvalue('username') or '').strip()
    email    = (form.getvalue('email') or '').strip()
    password = form.getvalue('password') or ''
    confirm  = form.getvalue('password_confirm') or ''
    
    errors = validate_inputs(username, email, password, confirm)
    if errors:
        html_header("400 Bad Request")
        print("<h3 style='color:#b00'>Registration error</h3>")
        print("<ul>")
        for e in errors:
            print(f"<li>{e}</li>")
        print("</ul>")
        print(f"<p><a href='{ERROR_URL}'>Back to register</a></p>")
        return 

    conn = getConnection()
    cur = conn.cursor()

    # Check if this username and email exipist in DB already
    cur.execute("SELECT 1 FROM users WHERE username = ? OR email = ? LIMIT 1", (username, email))
    if cur.fetchone() is not None:
        html_header("409 Conflict")
        print("<p style='color:#b00'>Username or email already exists.</p>")
        print(f"<p><a href='{ERROR_URL}'>Back</a></p>")
        return

    # encript password using bcrypt
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    created_at = datetime.datetime.now().isoformat(timespec='seconds')

    try:
        cur.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?,?,?,?)",
            (username, email, pw_hash, created_at)
        )
        conn.commit()
        redirect(SUCCESS_URL)
    except sqlite3.IntegrityError:
        # Backup guard in case UNIQUE constraints exist at DB level
        sys.exit(0)
    finally:
        conn.close()
        

__main__()