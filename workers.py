#!C:/Users/Emilija/AppData/Local/Programs/Python/Python311/python.exe
import os, sys, cgi, cgitb, sqlite3, html, bcrypt
from db import getConnection

cgitb.enable()

conn = getConnection()
conn.row_factory = sqlite3.Row

# --- helpers -------------------------------------------------

def redirect(url, set_cookies=None):
    # IMPORTANT: call this BEFORE sending any Content-Type/blank line
    sys.stdout.write("Status: 303 See Other\r\n")
    sys.stdout.write(f"Location: {url}\r\n")
    sys.stdout.write("Cache-Control: no-store\r\n")
    if set_cookies:
        for h in set_cookies:
            sys.stdout.write(f"Set-Cookie: {h}\r\n")
    sys.stdout.write("\r\n")
    raise SystemExit

def script_self():
    # Use the real mount path as fallback to avoid /Zabac mismatch
    return os.environ.get("SCRIPT_NAME", "/Web-programiranje-1/Zabac/workers.py")

def get_cookie(name: str):
    raw = os.environ.get("HTTP_COOKIE", "")
    for part in raw.split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            if k == name:
                return v
    return None

# --- data ops ------------------------------------------------

def get_all_workers():
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, role FROM users WHERE role = 'worker'")
    return cur.fetchall()

def delete_worker(worker_id: str):
    if not worker_id:
        return "Missing worker ID."
    _conn = getConnection()
    try:
        with _conn:
            _conn.execute("DELETE FROM users WHERE id = ?", (worker_id,))
    finally:
        try: _conn.close()
        except: pass
    redirect(script_self())  # no output happened yet -> safe

def add_worker(username: str, email: str, role_val: str, password: str):
    if not (username and email and role_val and password):
        return "Missing required fields."
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    _conn = getConnection()
    try:
        with _conn:
            _conn.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (username, email, pw_hash, role_val),
            )
    finally:
        try: _conn.close()
        except: pass
    redirect(script_self())  # no output happened yet -> safe

# --- UI ------------------------------------------------------

def admin_add_form():
    print(
        """<div style="margin-left:20px">
            <h2>Add Worker</h2>
            <form method="POST" action="" style="margin-left:10px">
                <input type="hidden" name="action" value="add_worker">
                <label>Username:</label><br>
                <input type="text" name="username" required><br>

                <label>Role:</label><br>
                <select name="role_val" required>
                    <option value="worker">Worker</option>
                    <option value="admin">Admin</option>
                </select><br>

                <label>Email:</label><br>
                <input type="email" name="email" required><br>

                <label>Password:</label><br>
                <input type="password" name="password" required><br><br>

                <button type="submit">Add Worker</button>
            </form>
        </div><br>"""
    )

def render_page(user_role: str | None):
    # NOW we send headers, because we know we’re rendering HTML
    print("Content-Type: text/html")
    print()

    if user_role != 'user':
        workers = get_all_workers()
        diff_style = "<style>.user_info { height:900px; }</style>"
        if user_role == "admin":
            diff_style = "<style>.user_info { height:800px; }</style>"

        print(f"""<html>
<head>
  <title>Workers Info</title>
  <link rel="stylesheet" href="./templates/global.css">
  {diff_style}
  <meta charset="utf-8">
</head>
<body>
  <h1 style="margin-left:20px">Workers in ZABAC</h1>""")

        if user_role == "admin":
            admin_add_form()

        print("""<div style="margin-left:20px">
<table class="styled-table">
  <tr>
    <th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Actions</th>
  </tr>""")

        if not workers:
            print("""<tr><td colspan="5" style="text-align:center;color:#666;">No workers found.</td></tr>""")
        else:
            for w in workers:
                wid   = html.escape(str(w["id"]))
                uname = html.escape(w["username"] or "")
                email = html.escape(w["email"] or "")
                wrole = html.escape(w["role"] or "")
                if(user_role == 'admin'):
                    print(f"""<tr>
  <td>{wid}</td><td>{uname}</td><td>{email}</td><td>{wrole}</td>
  <td>
    <form method="POST" action="" style="margin:0">
      <input type="hidden" name="action" value="delete_worker">
      <input type="hidden" name="id" value="{wid}">
      <input type="submit" value="Cancellation"
             onclick="return confirm('Are you sure you want to cancellation this worker?');">
    </form>
  </td>
</tr>""")
                else:
                    print(f"""<tr>
  <td>{wid}</td><td>{uname}</td><td>{email}</td><td>{wrole}</td>
  </tr>""")

        print("""</table></div></body></html>""")

# --- main ----------------------------------------------------

def __main__():
    # DO NOT print Content-Type here. We might redirect.
    sid = get_cookie("session_id")
    if not sid:
        redirect("/Web-programiranje-1/Zabac/templates/login.html")

    row = conn.execute("SELECT * FROM session WHERE sid = ?", (sid,)).fetchone()
    if not row:
        redirect("/Web-programiranje-1/Zabac/templates/login.html")

    user_id = row["user_id"]
    urow = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    user_role = urow["role"] if urow else None

    form = cgi.FieldStorage()
    method = os.environ.get("REQUEST_METHOD", "GET").upper()

    # Handle POST first, before sending any output
    if method == "POST" and user_role == "admin":
        action = (form.getfirst("action") or "").strip()
        if action == "add_worker":
            username = (form.getfirst("username") or "").strip()
            email    = (form.getfirst("email") or "").strip()
            role_val = (form.getfirst("role_val") or "").strip()
            password = form.getfirst("password") or ""
            add_worker(username, email, role_val, password)  # redirects
            return
        elif action == "delete_worker":
            worker_id = (form.getfirst("id") or "").strip()
            delete_worker(worker_id)  # redirects
            return
        else:
            # Unknown POST -> hard refresh to GET
            redirect(script_self())

    # GET (or non-admin): render UI
    render_page(user_role)

__main__()
try:
    conn.close()
except:
    pass
