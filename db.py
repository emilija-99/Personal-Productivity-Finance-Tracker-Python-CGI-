import sqlite3

def getConnection():
    conn = sqlite3.connect('db.db')
    conn.row_factory = sqlite3.Row
    if(conn):
        return conn
    else:
        print("Failed to connect to database")
        raise Exception("Database connection failed")

def closeConnection(conn):
    conn.close()
