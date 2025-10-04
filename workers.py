#!C:/Users/Emilija/AppData/Local/Programs/Python/Python311/python.exe
import os, sys, cgi, cgitb, sqlite3, html
import bcrypt
from db import getConnection

cgitb.enable()

print("Content-Type: text/html")
print()  

conn = getConnection()

def admin_add():
    print(
        """<div style="margin-left:20px">
            <h2>Add Worker</h2>
            <form method="POST" action="" style="margin-left:10px">
                <input type="hidden" name="action" value="add_worker">
                <label>Username:</label><br>
                <input type="text" name="username" required><br>

                <label>Role:</label><br>
                <select name="role" required>
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

# ---- Data: list workers (KEEP CONNECTION OPEN; DO NOT CLOSE HERE) ----
def get_all_workers():
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, role FROM users WHERE role = 'worker'")
    rows = cur.fetchall()
    return rows

def delete_worker(worker_id: str) -> str:
    if not worker_id:
        return "Missing worker ID."
    _conn = getConnection()
    try:
        cur = _conn.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (worker_id,))
        _conn.commit()
        return f"Worker with ID {html.escape(worker_id)} deleted successfully."
    finally:
        try:
            _conn.close()
        except Exception:
            pass

def add_worker(username: str, email: str, role: str, password: str) -> str:
    if not (username and email and role and password):
        return "Missing required fields."

    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    _conn = getConnection()
    cur = _conn.cursor()
    cur.execute("INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, email, pw_hash, role),)
    _conn.commit()
    _conn.close()
    return f"Worker {html.escape(username)} added successfully."
      
def render_page(role: str | None = None):
    workers = get_all_workers()

    style = """
    .user-information {
        display: none;
    }
    """ if role == "admin" else """
    .user-information {
        display: block;
    }
    """
    if role == "admin":
        admin_add()
        print(
            """<html>
                <head>
                    <title>Workers Info</title>
                    <link rel="stylesheet" href="./templates/global.css">
                    <meta charset="utf-8">
                     <style>
                    {style}
                    </style>
                </head>
                <body>
                    <h1 style="margin-left:20px">Workers in ZABAC</h1>
            <div style="margin-left:20px">
                <table class="styled-table">
                <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Actions</th>
                </tr>
            """)

        if not workers:
            print("""<tr>
                    <td colspan="5" style="text-align:center;color:#666;">No workers found.</td>
                    </tr>""")
        else:
            for w in workers:
                wid = html.escape(str(w["id"]))
                uname = html.escape(w["username"] or "")
                email = html.escape(w["email"] or "")
                role = html.escape(w["role"] or "")
                print(f"""<tr>
                <td>{wid}</td>
                <td>{uname}</td>
                <td>{email}</td>
                <td>{role}</td>
                <td>
                <form method="POST" action="" style="margin:0">
                        <input type="hidden" name="action" value="delete_worker">
                        <input type="hidden" name="id" value="{wid}">
                        <input type="submit" value="Cancellation" onclick="return confirm('Are you sure you want to cancellation this worker?');">
                </form>
                </td>
            </tr>""")
        print("""</table></div></body></html>""")

def __main__():
    form = cgi.FieldStorage()
    session_id = os.environ.get("HTTP_COOKIE", "").split("session_id=")[-1].split(";")[0].strip()

    sql = "SELECT role FROM users WHERE id = ?"
    cur = conn.cursor()
    cur.execute(sql, (session_id,))

    row = cur.fetchone()
    role = row['role'] if row else None

    render_page(role)

    if role != "admin":
        print()
    else:
        action = (form.getfirst("action") or "").strip()
        if action == "add_worker":
            username = (form.getfirst("username") or "").strip()
            email    = (form.getfirst("email") or "").strip()
            role     = (form.getfirst("role") or "").strip()
            password = form.getfirst("password") or ""
            message = add_worker(username, email, role, password)

        elif action == "delete_worker":
            worker_id = (form.getfirst("id") or "").strip()
            message = delete_worker(worker_id)
__main__()
conn.close()
