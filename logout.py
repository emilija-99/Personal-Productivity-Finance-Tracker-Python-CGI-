#!C:/Users/Emilija/AppData/Local/Programs/Python/Python311/python.exe
import os, sys, cgitb, sqlite3
from db import getConnection

cgitb.enable()

LOGIN_URL = "http://localhost/Web-programiranje-1/Zabac/templates/login.html"

def get_cookie(name: str):
    raw = os.environ.get("HTTP_COOKIE", "")
    for part in raw.split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            if k == name:
                return v
    return None

def cookie_header(name, value="", max_age=0, path="/", http_only=True, same_site="Lax"):
    # Max-Age=0 tells the browser to delete the cookie
    parts = [f"{name}={value}", f"Path={path}", f"Max-Age={int(max_age)}"]
    if http_only:
        parts.append("HttpOnly")
    if same_site:
        parts.append(f"SameSite={same_site}")
    return "; ".join(parts)

# Optional: remove server-side session if you store sessions in DB
sid = get_cookie("session_id")
try:
    if sid:
        conn = getConnection()
        cur = conn.cursor()
        cur.execute("DELETE FROM session WHERE sid = ?", (sid,))
        conn.commit()
except Exception:
    # Don’t block logout on DB issues; cookies will still be cleared
    pass

# Write HEADERS (no Content-Type; we’re redirecting)
sys.stdout.write("Status: 303 See Other\r\n")
sys.stdout.write(f"Location: {LOGIN_URL}\r\n")

# Clear cookies (session_id is HttpOnly; username often isn’t)
sys.stdout.write("Set-Cookie: " + cookie_header("session_id", "", 0, "/", True, "Lax") + "\r\n")
sys.stdout.write("Set-Cookie: " + cookie_header("username", "", 0, "/", False, "Lax") + "\r\n")

# End headers
sys.stdout.write("\r\n")
