from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecret"

DB = "social.db"

# Helper functions
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )""")
    # Posts table
    c.execute("""CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author TEXT NOT NULL,
                    content TEXT NOT NULL,
                    likes INTEGER DEFAULT 0
                )""")
    # Comments table
    c.execute("""CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER,
                    author TEXT NOT NULL,
                    comment TEXT NOT NULL
                )""")
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

init_db()  # create tables if not exist

# Routes
@app.route("/")
def home():
    username = session.get("username")
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    comments = {}
    for post in posts:
        comments[post["id"]] = conn.execute("SELECT * FROM comments WHERE post_id=?", (post["id"],)).fetchall()
    conn.close()
    return render_template("index.html", posts=posts, comments=comments, username=username)

# Signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            session["username"] = username
            return redirect("/")
        except sqlite3.IntegrityError:
            return "Username already exists!"
    return render_template("signup.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        if user:
            session["username"] = username
            return redirect("/")
        else:
            return "Invalid username or password!"
    return render_template("login.html")

# Logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

# Create post
@app.route("/post", methods=["POST"])
def post():
    if "username" not in session:
        return redirect("/login")
    content = request.form.get("content", "")
    if content:
        conn = get_db_connection()
        conn.execute("INSERT INTO posts (author, content) VALUES (?, ?)", (session["username"], content))
        conn.commit()
        conn.close()
    return redirect("/")

# Like post
@app.route("/like/<int:post_id>")
def like(post_id):
    conn = get_db_connection()
    conn.execute("UPDATE posts SET likes = likes + 1 WHERE id=?", (post_id,))
    conn.commit()
    conn.close()
    return redirect("/")

# Comment
@app.route("/comment/<int:post_id>", methods=["POST"])
def comment(post_id):
    if "username" not in session:
        return redirect("/login")
    comment_text = request.form.get("comment", "")
    if comment_text:
        conn = get_db_connection()
        conn.execute("INSERT INTO comments (post_id, author, comment) VALUES (?, ?, ?)", 
                     (post_id, session["username"], comment_text))
        conn.commit()
        conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, port=8000, use_reloader=False)
