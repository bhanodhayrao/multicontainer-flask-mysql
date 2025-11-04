from flask import Flask, jsonify
import os
import pymysql
import time

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("MYSQL_USER", "flaskuser")
DB_PASS = os.getenv("MYSQL_PASSWORD", "flaskpass")
DB_NAME = os.getenv("MYSQL_DATABASE", "flaskdb")

def get_conn(retries=10, delay=2):
    # simple retry to wait for MySQL to be ready
    for i in range(retries):
        try:
            return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, cursorclass=pymysql.cursors.DictCursor)
        except Exception as e:
            time.sleep(delay)
    raise RuntimeError("Could not connect to database after retries.")

@app.route("/")
def hello():
    return jsonify(message="Flask is up. Try /init and /users.")

@app.route("/init")
def init():
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  name VARCHAR(64) NOT NULL
                );
            """)
            cur.execute("INSERT INTO users (name) VALUES ('Bhanodhay') ON DUPLICATE KEY UPDATE name = name;")
        conn.commit()
    return jsonify(status="ok", info="Table ensured and sample user added.")

@app.route("/users")
def users():
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM users;")
            rows = cur.fetchall()
    return jsonify(rows)

if __name__ == "__main__":
    # Bind to all interfaces so Docker can expose it
    app.run(host="0.0.0.0", port=5000)
