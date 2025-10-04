#!C:/Users/Emilija/AppData/Local/Programs/Python/Python311/python.exe
import sys, cgi, cgitb, bcrypt, sqlite3, datetime
from db import getConnection
 

cgitb.enable()

ERROR_URL   = "http://localhost/Web-programiranje-1/Zabac/templates/register.html"
SUCCESS_URL = "http://localhost/Web-programiranje-1/Zabac/templates/login.html"

def out_header():
    print("ERROR.")
def redirect(url):
    sys.stdout.write(f"Location: {url}\r\n\r\n")
def __main__():
    form = cgi.FieldStorage()

    username = (form.getvalue('username') or '').strip()
    email    = (form.getvalue('email') or '').strip()
    password = form.getvalue('password') or ''
    confirm  = form.getvalue('password_confirm') or ''

    # Validate and exit early on failure
    if not (username and email and password and confirm):
        out_header()
        print("<p style='color:red'>Error: All fields are required</p>")
        sys.exit(0)

    if password != confirm:
        out_header()
        print("<p style='color:red'>Error: Passwords do not match</p>")
        sys.exit(0)

    conn = getConnection()
    cur = conn.cursor()

    # Uniqueness check
    cur.execute("SELECT 1 FROM users WHERE username = ? OR email = ? LIMIT 1", (username, email))
    if cur.fetchone() is not None:
        # Use your existing helper to send a 303 redirect
        sys.exit(0)

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