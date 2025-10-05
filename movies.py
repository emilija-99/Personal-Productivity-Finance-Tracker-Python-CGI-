#!C:/Users/Emilija/AppData/Local/Programs/Python/Python311/python.exe
import os, cgitb, sqlite3, html, sys
from urllib.parse import quote
from http import cookies
from db import getConnection
from datetime import datetime

cgitb.enable()
ALLOWED_GENRES = {"Sci-Fi", "Crime", "Drama", "Action"}
NOW_YEAR = datetime.now().year



conn = getConnection()
conn.row_factory = sqlite3.Row
LOGIN_URL = "http://localhost/Web-programiranje-1/Zabac/templates/login.html"

session_id = None  
role = None     
def get_cookie(name: str):
    raw = os.environ.get("HTTP_COOKIE", "")
    for part in raw.split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            if k == name:
                return v
    return None

def clear_cookie_headers(name="session_id"):
    if names is None:
        names = ["session_id"]
    headers = []
    for n in names:
        if n == "session_id":
            headers.append(f"{n}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
        else:
            headers.append(f"{n}=; Path=/; Max-Age=0; SameSite=Lax")
    return headers

def redirect(url, set_cookies=None):
    sys.stdout.write("Status: 303 See Other\r\n")
    sys.stdout.write(f"Location: {url}\r\n")
    sys.stdout.write("Cache-Control: no-store\r\n")
    if set_cookies:
        for h in set_cookies:
            # each h should be like "name=value; Path=/; ..."
            sys.stdout.write(f"Set-Cookie: {h}\r\n")
    sys.stdout.write("\r\n")
    raise SystemExit       # stop now; prevents duplicate output

def create_logout_button():
    # Simple POST form
    print("""
    <form method="post" action="" style="display:inline;">
      <input type="hidden" name="action" value="logout">
      <button type="submit" class="btn btn-logout">Logout</button>
    </form>
    """)
def redirect_logout(url, set_cookies=None, status="303 See Other"):
    # IMPORTANT: do NOT print Content-Type here.
    sys.stdout.write(f"Status: {status}\r\n")
    sys.stdout.write("Cache-Control: no-store\r\n")
    if set_cookies:
        for h in set_cookies:
            sys.stdout.write(f"Set-Cookie: {h}\r\n")
    sys.stdout.write(f"Location: {url}\r\n\r\n")
    raise SystemExit
def handle_logout():
    sid = get_cookie("session_id")
    cur = conn.cursor()
    # Resolve user_id from current session id
    cur.execute("SELECT user_id FROM session WHERE sid = ?", (sid,))
    row = cur.fetchone()
    if row:
        user_id = row["user_id"]
        # delete all sessions for this user
        cur.execute("DELETE FROM session WHERE user_id = ?", (user_id,))
        conn.commit()

    redirect(
            LOGIN_URL + "?logged_out=1",
            set_cookies=clear_cookie_headers(names=["session_id", "username"])
        )

def get_session():
    global session_id
    
    raw_cookie = os.environ.get('HTTP_COOKIE', '')
    c = cookies.SimpleCookie()
    c.load(raw_cookie)
    
    sid = c.get('session_id')
    
    if sid:
        val = sid.value.strip().strip('"').strip("'")
        if val.isdigit():
            session_id = int(val)
        else:
            session_id = None

    sql = "SELECT * from session where sid = ?"
    cur = conn.cursor()
    sid_value = sid.value 
    cur.execute(sql, (sid_value,))
    row = cur.fetchone()

    return row['user_id']
    
def esc(x):
    return html.escape("" if x is None else str(x))

def get_user(user_id: int):
    sql = "SELECT * FROM users WHERE id = ?"
    cur = conn.cursor()
    cur.execute(sql, (user_id,))
    return cur.fetchone()

def show_admin_content():
    sql = "SELECT * FROM movies JOIN movies_details ON movies.id == movies_details.movie_id"
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()

    print("<h1>All Movies</h1>")
    print(f"""<table class='styled-table'><thead><tr><th>Title</th><th>Year</th><th>Genre</th><th>Description</th><th>Available</th></tr></thead><tbody>""")

    for row in rows:
        available = int(row['available'])
        print(f"""
        <tr>
        <td>{html.escape(row['title'])}</td>
        <td>{html.escape(str(row['year']))}</td>
        <td>{html.escape(row['genre'])}</td>
        <td>{html.escape(row['description'])}</td>
        <td>{'Yes' if available > 1 else 'No'}</td>
        <td>
           <form method="POST" action="">
              <input type="hidden" name="action" value="inc_available">
              <input type="hidden" name="movie_id" value="{row['movie_id']}">
              <button type="submit">+1 Available</button>
            </form>
        </td>
        </tr>""")

    print("</tbody></table>")

def user_options(selected_id=None):
    sql_list_of_users = """SELECT u.*
FROM users u
LEFT JOIN movies_booking mb
  ON mb.customer_id = u.id
 AND mb.status = 'booked'
WHERE u.role = 'user'
GROUP BY u.id
HAVING COUNT(mb.id) < 2;"""
    cursor = conn.cursor()
    cursor.execute(sql_list_of_users)
    list_of_users = cursor.fetchall()

    return "".join(
        f'<option value="{u["id"]}"{" selected" if selected_id and u["id"]==selected_id else ""}>{esc(u["username"])}</option>'
        for u in list_of_users
    )

def user_field_for(current_role, current_user_id):
    if current_role in ("admin", "worker"):
        # assumes you have user_options(list_of_users) elsewhere
        return f'<label>User:</label> <select name="user_id">{user_options(current_user_id)}</select>'
    return f'<input type="hidden" name="user_id" value="{current_user_id}"/>'

def show_all_users_and_their_movies():
    rows = conn.execute("""
        SELECT
            u.id            AS user_id,
            u.username      AS username,
            mb.customer_id  AS customer_id,  
            mb.status       AS booking_status,
            mb.movie_id     AS movie_id,
            m.name          AS movie_title,
            m.available     AS available
        FROM users u
        LEFT JOIN movies_booking mb ON u.id = mb.customer_id
        LEFT JOIN movies m          ON mb.movie_id = m.id
        ORDER BY u.id;
    """).fetchall()

    available_movies = conn.execute("""
        SELECT id, name
        FROM movies
        WHERE available >= 1
        ORDER BY name;
        """).fetchall()

    def esc(x):  # small helper
        return html.escape("" if x is None else str(x))

    print("""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8"/>

        <link rel="stylesheet" href="./templates/global.css">
        <title>Users & Movie Bookings</title>
        </head>
        <body>
        <h2>Users & Movie Bookings</h2>

        <table class="styled-table">
        <thead>
            <tr>
            <th>Username</th>
            <th>Movie Title</th>
            <th>Booking Status</th>
            <th>Book Movies</th>
            <th>Unbook Movies</th>
            </tr>
        </thead>
        <tbody>
        """)
    script_url = os.environ.get("SCRIPT_NAME", "../movies.py")

    

    for r in rows:
        username = esc(r["username"])
        movie_title = esc(r["movie_title"]) if r["movie_title"] else '<span class="muted">—</span>'
        status = r["booking_status"] or ""
        booking_status_cell = (
            f'<span class="ok">{esc(status)}</span>' if status == "booked"
            else ('<span class="muted">—</span>' if status == "" else esc(status))
        )

        can_book = (status != "booked") and len(available_movies) > 0
        action_name = "book" if role in ("admin", "member", "worker") else "book_movie_for_user"
        print(f"<!-- Can book? {can_book}, status: {esc(status)}, available_movies: {len(available_movies)} -->")
        print(f"<!-- Action name: {action_name}, role: {role} -->")
        current_row_user_id = r["user_id"]
        action_name = "book_movie_for_user" if role in ("admin", "worker") else "book"

        # Book cell
        if can_book:
            movie_opts = "".join(
                f'<option value="{m["id"]}">{esc(m["name"])}</option>'
                for m in available_movies
            )
            user_selector = user_field_for(role, current_row_user_id)
            book_cell = f"""
            <form method="POST" action="{esc(script_url)}" class="actions">
            <input type="hidden" name="action" value="{esc(action_name)}"/>
            {user_selector}
            <label>Movie:</label>
            <select name="movie_id">{movie_opts}</select>
            <button type="submit">Book</button>
            </form>
            """
        else:
            reason = "already booked" if status == "booked" else "no movies available"
            book_cell = f'<span class="muted">Cannot book ({esc(reason)})</span>'

        # Unbook cell
        if status == "booked" and (r["movie_id"] is not None) and (r["customer_id"] is not None):
            unbook_cell = f"""
            <form method="POST" action="{esc(script_url)}" class="actions">
                <input type="hidden" name="action" value="unbook"/>
                <input type="hidden" name="movie_id" value="{r['movie_id']}"/>
                <input type="hidden" name="user_id"  value="{r['customer_id']}"/>
                <button type="submit">Unbook</button>
            </form>
            """
        else:
            unbook_cell = '<span class="muted">—</span>'




        print(f"""
        <tr>
        <td>{username}</td>
        <td>{movie_title}</td>
        <td>{booking_status_cell}</td>
        <td>{book_cell}</td>
        <td>{unbook_cell}</td>
        </tr>
        """)

    print("""
    </tbody>
    </table>

    </body>
    </html>
    """)

def show_user_content(user_id):
    print("<h1>User Content</h1>")
    user_id = user_id
    if user_id is None:
        print("<p>Please log in.</p>")
        return

    row_cnt = conn.execute(
        "SELECT COUNT(*) AS c FROM movies_booking WHERE customer_id = ? AND status = 'booked'",
        (user_id,)
    ).fetchone()
    active_count = int(row_cnt["c"] or 0)
    can_book_more = active_count < 2

    available_movies = conn.execute(
        "SELECT id, name, available FROM movies WHERE available >= 1 ORDER BY name"
    ).fetchall()

    current = conn.execute("""
        SELECT mb.movie_id, m.name AS title, mb.status
        FROM movies_booking mb
        JOIN movies m ON m.id = mb.movie_id
        WHERE mb.customer_id = ? AND mb.status = 'booked'
        ORDER BY m.name
    """, (user_id,)).fetchall()

    script_url = os.environ.get("SCRIPT_NAME", "/cgi-bin/movies.py")

    print("<h2>Your Dashboard</h2>")

    if not can_book_more:
        print("<p class='warn'>You have 2 active bookings. Movie cannot be booked.</p>")
    else:
        print(f"<p class='muted'>Active bookings: {active_count}/2</p>")


    print("<h3>Available Movies</h3>")
    if available_movies:
        print("<table class='styled-table'><thead><tr><th>Title</th><th>Available</th><th>Action</th></tr></thead><tbody>")
        for m in available_movies:
            title = esc(m["name"])
            avail = int(m["available"])
            if can_book_more:
                action_cell = f"""
                  <form method="POST" action="{esc(script_url)}">
                    <input type="hidden" name="action" value="book"/>
                    <input type="hidden" name="user_id" value="{user_id}"/>
                    <input type="hidden" name="movie_id" value="{m['id']}"/>
                    <button type="submit">Book</button>
                  </form>
                """
            else:
                action_cell = "<span class='warn'>Cannot book (limit reached)</span>"

            print(f"<tr><td>{title}</td><td>{avail}</td><td>{action_cell}</td></tr>")
        print("</tbody></table>")
    else:
        print("<p class='muted'>No movies currently available.</p>")

    # list bookings for user
    print("<h3>Your Bookings</h3>")
    if current:
        print("<table style='styled-table'><thead><tr><th>Title</th><th>Status</th><th>Action</th></tr></thead><tbody>")
        for r in current:
            title = esc(r["title"])
            status = esc(r["status"])
            action_cell = f"""
              <form method="POST" action="{esc(script_url)}">
                <input type="hidden" name="action" value="unbook"/>
                <input type="hidden" name="user_id" value="{user_id}"/>
                <input type="hidden" name="movie_id" value="{r['movie_id']}"/>
                <button type="submit">Unbook</button>
              </form>
            """
            print(f"<tr><td>{title}</td><td class='ok'>{status}</td><td>{action_cell}</td></tr>")
        print("</tbody></table>")
    else:
        print("<p class='muted'>No active bookings.</p>")

# helper
def bad_request(msg, code="400 Bad Request"):
    sys.stdout.write(f"<div style='border:1px solid #c00;padding:10px;color:#a00'><strong>Error:</strong> {esc(msg)}</div>")

def book_movie(user_id: int, movie_id: int):
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("BEGIN IMMEDIATE")
    # check if movie exists in movies and available is!
    movie = conn.execute(
        "SELECT id, available FROM movies WHERE id = ?",
        (movie_id,)
    ).fetchone()

    if not movie:
        conn.execute("ROLLBACK")
        raise Exception("Movie not found")

    if int(movie["available"]) <= 0:
        conn.execute("ROLLBACK")
        raise Exception("Movie is not available")

    # prevent for same user 2 same movies
    existing = conn.execute(
        "SELECT id FROM movies_booking "
        "WHERE customer_id = ? AND movie_id = ? AND status = 'booked' "
        "LIMIT 1",
        (user_id, movie_id)
    ).fetchone()

    if existing:
        conn.execute("ROLLBACK")
        raise Exception("User already booked this movie")

    # update available -1
    upd = conn.execute(
        "UPDATE movies SET available = available - 1 "
        "WHERE id = ? AND available > 0",
        (movie_id,)
    )

    if upd.rowcount != 1:
        conn.execute("ROLLBACK")
        raise Exception("Concurrent booking conflict")

    # insert booked movie into movies_booking
    conn.execute(
        "INSERT INTO movies_booking (customer_id, movie_id, status) "
        "VALUES (?, ?, 'booked')",
        (user_id, movie_id)
    )

    conn.commit()

def unbook_movie(user_id: int, movie_id: int):
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("BEGIN IMMEDIATE")

    booking = conn.execute(
        "SELECT id FROM movies_booking "
        "WHERE customer_id = ? AND movie_id = ? AND status = 'booked' "
        "LIMIT 1",
        (user_id, movie_id)
    ).fetchone()

    if not booking:
        conn.execute("ROLLBACK")
        raise Exception("Active booking not found")

    # if booked movie exist and unbook action, then delete movie from movie_booking and set available + 1 in movies
    conn.execute("DELETE FROM movies_booking WHERE id = ?", (booking["id"],))
    conn.execute("UPDATE movies SET available = available + 1 WHERE id = ?", (movie_id,))

    conn.commit()

def book_movie_for_user(user_id: int, movie_id: int):
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE")

        user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        # edge case - user not found
        if not user:
            conn.execute("ROLLBACK")
            return (False, "User not found")

        # user can have max 2 booked movies
        active_cnt = conn.execute(
            "SELECT COUNT(*) AS c "
            "FROM movies_booking "
            "WHERE customer_id = ? AND status = 'booked'",
            (user_id,)
        ).fetchone()["c"]

        if int(active_cnt or 0) >= 2:
            conn.execute("ROLLBACK")
            return (False, "Booking limit reached (2 active bookings)")

        movie = conn.execute(
            "SELECT id, available FROM movies WHERE id = ?",
            (movie_id,)
        ).fetchone()

        # movie do not exists - edge case
        if not movie:
            conn.execute("ROLLBACK")
            return (False, "Movie not found")

        if int(movie["available"] or 0) <= 0:
            conn.execute("ROLLBACK")
            return (False, "Movie is not available")

        # check if user already booked this movie
        existing = conn.execute(
            "SELECT id FROM movies_booking "
            "WHERE customer_id = ? AND movie_id = ? AND status = 'booked' "
            "LIMIT 1",
            (user_id, movie_id)
        ).fetchone()
        if existing:
            conn.execute("ROLLBACK")
            return (False, "Already booked this movie")

        # check and exec
        upd = conn.execute(
            "UPDATE movies "
            "SET available = available - 1 "
            "WHERE id = ? AND available > 0",
            (movie_id,)
        )
        
        if upd.rowcount != 1:
            conn.execute("ROLLBACK")
            return (False, "Concurrent booking conflict")
        
        # insert into movies_booking -> set movie to user_id
        conn.execute(
            "INSERT INTO movies_booking (customer_id, movie_id, status) "
            "VALUES (?, ?, 'booked')",
            (user_id, movie_id)
        )

        conn.commit()
        return (True, "Booked")

    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        return (False, f"Booking failed: {e.__class__.__name__}")

def show_add_movies(form):
    # set form fields 
    if form == None:
        name        = ""
        description = ""
        year        = ""
        genre       = ""
        available   = ""
    else:
        name        = (form.getfirst("name") or "").strip()
        description = (form.getfirst("description") or "").strip()
        year        = (form.getfirst("year") or "").strip()
        genre       = (form.getfirst("genre") or "").strip()
        available   = (form.getfirst("available") or "").strip()

    print(f"""<div>
      <form method="post" action="">
        <input type="hidden" name="action" value="add_movie">

        <label for="name">Movie Title:</label><br>
        <input id="name" type="text" name="name" required value="{name}"><br><br>

        <label for="description">Description:</label><br>
        <input id="description" type="text" name="description" required value="{description}"><br><br>

        <label for="year">Year:</label><br>
        <input id="year" type="number" name="year" min="1888" max="{NOW_YEAR}" required value="{year}"><br><br>

        <label for="genre">Genre:</label><br>
        <select id="genre" name="genre" required>
          <option value="" {"selected" if not genre else ""} disabled>-- select --</option>
          <option value="Sci-Fi" {"selected" if genre=="Sci-Fi" else ""}>Sci-Fi</option>
          <option value="Crime"  {"selected" if genre=="Crime"  else ""}>Crime</option>
          <option value="Drama"  {"selected" if genre=="Drama"  else ""}>Drama</option>
          <option value="Action" {"selected" if genre=="Action" else ""}>Action</option>
        </select><br><br>

        <label for="available">Available:</label><br>
        <input id="available" type="number" name="available" min="1" value="{available}" placeholder="1"><br><br>

        <button type="submit">Add movie</button>
      </form>
    </div>""")


def insert_movie(form):
    # get form values
    name = (form.getfirst("name") or "").strip()
    description = (form.getfirst("description") or "").strip() 
    genre = (form.getfirst("genre") or "").strip()
    year = (form.getfirst("year") or "").strip()  
    
    # validate fields
    year_integer = int(year)

    if year_integer > NOW_YEAR:
        print(f"Year cannot be greater than {NOW_YEAR}")
        return

    available_raw = (form.getfirst("available") or "").strip()

    if available_raw == "":
        available = 1
    else:
        available = int(available_raw)
        if available > 10:
            print("Has no room for this many movies (max 10).")
            available = 1
    
    # set payload for inserting data
    payload_movies = {
        "name": name,
        "available": available
    }

    payload_movies_details = {
        "movie_id": 0,  
        "title": name,
        "description": description,
        "year": year_integer,   
        "genre": genre
    }

    conn = getConnection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # populate movies
    cur.execute(
        """
        INSERT INTO movies (name, available)
        VALUES (?, ?)
        """,
        (payload_movies["name"], payload_movies["available"])
    )

    movie_id = cur.lastrowid
    payload_movies_details["movie_id"] = movie_id

    # populate movies_details
    cur.execute(
        """
        INSERT INTO movies_details (movie_id, title, description, year, genre)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            payload_movies_details['movie_id'],
            payload_movies_details['title'],
            payload_movies_details['description'],
            payload_movies_details['year'],
            payload_movies_details['genre']
        )
    )

    conn.commit()  
    conn.close()

    return True, f"Movie added successfully (id={movie_id})."

def __main__():
    import cgi
    form = cgi.FieldStorage()
    method = (os.environ.get("REQUEST_METHOD") or "GET").upper()

    # Handle POST actions BEFORE any output so redirects send proper HTTP headers
    if method == "POST":
        action = (form.getfirst("action") or "").strip().lower()

        if action == "add_movie":
            ok, msg = insert_movie(form)
            if ok:
                redirect(os.environ.get("SCRIPT_NAME", "/Zabac/movies.py"))
            else:
                # fall through to render page and display the error
                error_html = f"<div style='color:red'>{esc(msg)}</div>"

        elif action == "logout":
            # handle_logout should call redirect() when done
            handle_logout()
            # if handle_logout doesn't redirect, fallback:
        elif  action == "inc_available":
                    movie_id_raw = form.getfirst("movie_id")
                    cur = conn.cursor()
                    cur.execute("UPDATE movies SET available = available + 1 WHERE id = ?", (movie_id_raw,))
                    conn.commit()
                    redirect(os.environ.get("SCRIPT_NAME", "/Zabac/movies.py"))
        else:
            user_id = (form.getfirst("user_id") or "").strip()
            movie_id = (form.getfirst("movie_id") or "").strip()

            if not (user_id.isdigit() and movie_id.isdigit()):
                redirect(os.environ.get("SCRIPT_NAME", "/Zabac/movies.py") + "?err=invalid_ids")

            try:
                if action == "book_movie_for_user":
                    book_movie_for_user(int(user_id), int(movie_id))
                elif action == "book":
                    book_movie(int(user_id), int(movie_id))
                elif action == "unbook":
                    unbook_movie(int(user_id), int(movie_id))
                
                # Successful POST -> redirect to self (PRG)
                redirect(os.environ.get("SCRIPT_NAME", "/Zabac/movies.py"))
            except Exception as e:
                # redirect with an error message (or handle otherwise)
                redirect(os.environ.get("SCRIPT_NAME", "/Zabac/movies.py") + "?err=" + quote(str(e)))

    # No redirect happened -> render page (safe to print headers/body)
    print("Content-Type: text/html")
    print()
    session_id = get_session()
    session_id = get_session()

    if session_id is not None:
        user_row = get_user(session_id)
        if not user_row:
            return bad_request("User not found or session invalid")
        
        global role
        role = user_row['role']
        print("<!DOCTYPE html><html><head><link rel='stylesheet' href='./templates/global.css'><meta charset='utf-8'><title>Movies</title></head><body>")
        try:
            if role in ('admin', 'member', 'worker'):
                show_admin_content()
                show_all_users_and_their_movies()
            else:
                show_user_content(user_row['id'])
        except Exception as e:
            bad_request(f"Render error: {e}")
        print("</body></html>")
    else:
        print("<!DOCTYPE html><html><body><h3>Please log in</h3></body></html>")

    import cgi
    form = cgi.FieldStorage()

    method = (os.environ.get("REQUEST_METHOD") or "GET").upper()
    if method == "POST" and (form.getfirst("action") == "add_movie"):
        ok, msg = insert_movie(form)
        if ok:
            redirect(os.environ.get("SCRIPT_NAME", "/Zabac/movies.py"))  # no prints before this
        else:
            # now you can print headers+HTML to show the error
            print("Content-Type: text/html\r\n")
            print(f"<div style='color:red'>{esc(msg)}</div>")
        
    elif role == 'admin':
        show_add_movies(form)
    elif method == "POST" and (form.getfirst("action") == "logout"):
            handle_logout()

    if os.environ.get("REQUEST_METHOD", "GET").upper() == "POST":
        action   = (form.getfirst("action") or "").strip().lower()
        user_id  = (form.getfirst("user_id") or "").strip()
        movie_id = (form.getfirst("movie_id") or "").strip()

        print(f"<!-- Action: {esc(action)}, user_id: {esc(user_id)}, movie_id: {esc(movie_id)} -->\n")
        if not (user_id.isdigit() and movie_id.isdigit()):
            bad_request("Invalid user_id/movie_id")
        else:
            try:
                if action == "book_movie_for_user":
                   print("Booking for user...", user_id, movie_id)
                   book_movie_for_user(int(user_id), int(movie_id))
                elif action == "book": 
                   book_movie(int(user_id), int(movie_id))
                elif action == "unbook":
                    unbook_movie(int(user_id), int(movie_id))
                else:
                    bad_request("Unknown action")
            except Exception as e:
                bad_request(str(e))

__main__()