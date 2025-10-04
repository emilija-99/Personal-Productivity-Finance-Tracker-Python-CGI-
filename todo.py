#!C:/Users/Emilija/AppData/Local/Programs/Python/Python311/python.exe
import os, sys, cgi, cgitb, sqlite3, html, datetime
from db import getConnection, closeConnection

cgitb.enable()
print("Content-Type: text/html\n")

VALID_STATUS = ['todo','in-progress','done'];

conn = getConnection()
def sanitize(s):
    return html.escape(s or "")

def fetchTodos():
    conn = getConnection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM todos ORDER BY created_at DESC, id DESC")
    rows = cur.fetchall()
    conn.close()
    board = {s: [] for s in VALID_STATUS}
    for r in rows:
        board[r["status"]].append(r)
    return board

def render_todo_list(todos):
    rows = []
    for todo in todos:
        rows.append(f"""
        <tr>
            <td>{html.escape(todo['title'])}</td>
            <td>{html.escape(todo['description'] or '')}</td>
            <td>{html.escape(todo['status'])}</td>
            <td>{html.escape(todo['created_at'])}</td>
            <td>{html.escape(todo['due_date'] or '')}</td>
            <td>
                <a href="/cgi-bin/edit_todo.py?id={todo['id']}">Edit</a> |
                <a href="/cgi-bin/delete_todo.py?id={todo['id']}" onclick="return confirm('Are you sure?')">Delete</a>
            </td>
        </tr>
        """)
    return f"""
    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>Title</th>
            <th>Description</th>
            <th>Status</th>
            <th>Created At</th>
            <th>Due Date</th>
            <th>Actions</th>
        </tr>
        {''.join(rows)}
    </table>
    """

def render_form(errors=None):
    error_html = ''
    if errors:
        error_html = '<ul style="color:red;">' + ''.join(f'<li>{html.escape(e)}</li>' for e in errors) + '</ul>'
    return f"""
    <h4>Create new task</h4>
    {error_html}
    <form method="post" action="todo.py">
        <label>Title: <input type="text" name="title" required></label><br>
        <label>Description: <textarea name="description"></textarea></label><br>
        <label>Status:
            <select name="status">
                <option value="todo">To Do</option>
                <option value="in-progress">In Progress</option>
                <option value="done">Done</option>
            </select>
        </label><br>
        <label>Due Date: <input type="date" name="due_date"></label><br>
        <button type="submit">Add</button>
    </form>
    """


def init_db():
    conn = getConnection()
    cur = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL CHECK(status IN ('todo','in-progress','done')),
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        due_date TEXT
      )
    """)
    conn.commit()
    conn.close()

def main():
    form = cgi.FieldStorage()
    errors = []

    if os.environ['REQUEST_METHOD'] == 'POST':
        title = (form.getvalue('title') or '').strip()
        description = (form.getvalue('description') or '').strip()
        status = (form.getvalue('status') or 'todo').strip()
        due_date = (form.getvalue('due_date') or '').strip()

        if not title:
            errors.append("Title is required.")
        if status not in VALID_STATUS:
            errors.append("Invalid status.")
        if due_date:
            try:
                datetime.datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                errors.append("Due date must be in YYYY-MM-DD format.")

        if not errors:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO todos (title, description, status, created_at, due_date)
                VALUES (?, ?, ?, ?, ?)
            """, (title, description, status, datetime.datetime.now().isoformat(), due_date or None))
            conn.commit()
            print("<p style='color:green;'>To-Do item added successfully!</p>")

    cur = conn.cursor()
    cur.execute("SELECT * FROM todos ORDER BY created_at DESC")
    todos = cur.fetchall()

    print(f"""
    <html>
    <body>
        <div class="div-centered">
          <div class="container-todos">
            {render_todo_list(todos)}
        </div>
        <hr>
        <div class="container-add-todo">
            {render_form(errors)}
        </div>
        </div>
        
    </body>
    </html>
    <style>
    .div-centered{{
        display: flex;
        flex-direction: column;
        align-items: left;
        gap: 20px;        
    }}
    .container-todos {{
        float: left;
        width: 50%;
        margin-bottom: 20px;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        border: 1px solid #ccc;
    }}
    .container-add-todo {{
        border: 1px solid #ccc;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        float: center;
        padding: 10px;
        box-sizing: border-box;
        width: 30%;
    }}
    </style>
    """)
def render_card(row):
    tid = row["id"]
    title = sanitize(row["title"])
    desc = sanitize(row["description"])
    created = sanitize(row["created_at"])
    due = sanitize(row["due_date"]) if row["due_date"] else ""
    status = row["status"]

    order = list(VALID_STATUS)
    idx = order.index(status)
    prev_status = order[idx - 1] if idx > 0 else None
    next_status = order[idx + 1] if idx < len(order) - 1 else None

    buttons = []
    if prev_status:
        buttons.append(f"""
        <form method="post" style="display:inline;">
          <input type="hidden" name="action" value="move">
          <input type="hidden" name="id" value="{tid}">
          <input type="hidden" name="status" value="{prev_status}">
          <button type="submit" title="Move to {prev_status}">←</button>
        </form>
        """)
    if next_status:
        buttons.append(f"""
        <form method="post" style="display:inline;">
          <input type="hidden" name="action" value="move">
          <input type="hidden" name="id" value="{tid}">
          <input type="hidden" name="status" value="{next_status}">
          <button type="submit" title="Move to {next_status}">→</button>
        </form>
        """)

    delete_btn = f"""
    <form method="post" style="display:inline;margin-left:6px;">
      <input type="hidden" name="action" value="delete">
      <input type="hidden" name="id" value="{tid}">
      <button type="submit" title="Delete" onclick="return confirm('Delete this task?')">✖</button>
    </form>
    """

    return f"""
    <div class="card">
      <div class="card-title">{title}</div>
      <div class="card-desc">{desc}</div>
      <div class="card-meta">
        <span>Created: {created}</span>
        {f'<span>Due: {due}</span>' if due else ''}
      </div>
      <div class="card-actions">{''.join(buttons)}{delete_btn}</div>
    </div>
    """

def render_column(title, status, rows):
    cards = "".join(render_card(r) for r in rows) or "<div class='empty'>No tasks</div>"
    return f"""
    <section class="col">
      <header>{title}</header>
      {cards}
      <button class="add" onclick="document.getElementById('dlg').showModal(); document.getElementById('status').value='{status}';">
        + Add here
      </button>
    </section>
    """

    closeConnection(conn)
if __name__ == "__main__":
    init_db()
    board = fetchTodos()
    print(board)
    # render_todo_list(board)

    main()