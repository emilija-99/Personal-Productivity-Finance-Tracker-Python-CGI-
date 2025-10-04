#!C:/Users/Emilija/AppData/Local/Programs/Python/Python311/python.exe
import os, sys, cgi, cgitb, sqlite3, html, datetime
from db import getConnection

cgitb.enable()
print("Content-Type: text/html\n")

conn = getConnection()
session_id = (os.environ.get('HTTP_COOKIE') or '').split('session_id=')[-1].split(';')[0].strip()
# print("session id: ", session_id);
def getUserInfo(id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (id,))
    row = cur.fetchone()
    return row

def __main__():
    user = getUserInfo(session_id)
    if not user:
        print("<h1>User not found</h1>")
        return
    print(f"""
    <html>
        <head>
            <title>User Info</title>
            <link rel="stylesheet" href="./templates/global.css">
        </head>
        <body>
            <div class="div-user-info">
                <p><strong>Username:</strong> {html.escape(user['username'])}</p>
                <p><strong>Email:</strong> {html.escape(user['email'])}</p>
                <p><strong>Role:</strong> {html.escape(user['role'])}</p>
            </div>
        </body>
    </html>
    """)

__main__()