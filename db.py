import os
import psycopg2

def connect():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    database = os.getenv("DB_NAME")
    
    db = psycopg2.connect(
        database=database,
        user=user,
        password=password,
        host=host,
        port=port)

    return db

def migrate():
    conn = connect()
    cur = conn.cursor()

    cur.execute(open("dump.sql", "r").read())

    conn.commit()
    cur.close()
    conn.close()