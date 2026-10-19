import os
from functools import wraps

import bcrypt
import pymysql
from dotenv import load_dotenv
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.exceptions import HTTPException

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "my_super_secret_key_12345")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(BASE_DIR, "flask_session")
app.config["SESSION_PERMANENT"] = False
Session(app)


def get_db():
    if "db" not in g:
        g.db = pymysql.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "20052005"),
            database=os.getenv("DB_NAME", "registration"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def validate_register(name, email, password, confirm):
    errors = []
    if not name:
        errors.append("Name is required")
    elif len(name) > 100:
        errors.append("Name is too long (100 characters at most)")
    if not email:
        errors.append("Email is required")
    elif len(email) > 255:
        errors.append("Email is too long (255 characters at most)")
    if not password:
        errors.append("Password is required")
    elif len(password.encode("utf-8")) > 72:
        errors.append("Password is too long (72 bytes at most)")
    if not confirm:
        errors.append("Confirm password is required")
    elif password and password != confirm:
        errors.append("Passwords do not match")
    return errors


def validate_login(email, password):
    errors = []
    if not email:
        errors.append("Email is required")
    if not password:
        errors.append("Password is required")
    return errors


def validate_title(title):
    if not title:
        return ["Title is required"]
    if len(title) > 200:
        return ["Title is too long (200 characters at most)"]
    return []


def render_index(add_errors=None, add_value="", edit_id=None, edit_errors=None, edit_value=""):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT todo_id, title, is_done, created_at FROM todos WHERE user_id = %s ORDER BY todo_id DESC",
            (session["user_id"],),
        )
        todos = cur.fetchall()
    return render_template(
        "index.html",
        todos=todos,
        add_errors=add_errors or [],
        add_value=add_value,
        edit_id=edit_id,
        edit_errors=edit_errors or [],
        edit_value=edit_value,
    )


@app.route("/")
@login_required
def index():
    return render_index()


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        errors = validate_register(name, email, password, confirm)
        if errors:
            return render_template("register.html", errors=errors, name=name, email=email)
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                    (email, name, password_hash),
                )
                user_id = cur.lastrowid
            db.commit()
        except pymysql.err.IntegrityError as e:
            db.rollback()
            if e.args[0] == 1062:
                return render_template(
                    "register.html", errors=["Email Already Exists"], name=name, email=email
                )
            raise
        session.clear()
        session["user_id"] = user_id
        session["name"] = name
        flash("Welcome, " + name + "! Your account has been created.", "success")
        return redirect(url_for("index"))
    return render_template("register.html", errors=[], name="", email="")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        errors = validate_login(email, password)
        if errors:
            return render_template("login.html", errors=errors, email=email)
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "SELECT user_id, name, password_hash FROM users WHERE email = %s",
                (email,),
            )
            user = cur.fetchone()
        valid = False
        if user:
            try:
                valid = bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8"))
            except ValueError:
                valid = False
        if not valid:
            return render_template("login.html", errors=["Invalid email or password"], email=email)
        session.clear()
        session["user_id"] = user["user_id"]
        session["name"] = user["name"]
        return redirect(url_for("index"))
    return render_template("login.html", errors=[], email="")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/todos/add", methods=["POST"])
@login_required
def add_todo():
    raw = request.form.get("title", "")
    title = raw.strip()
    errors = validate_title(title)
    if errors:
        return render_index(add_errors=errors, add_value=raw)
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO todos (user_id, title) VALUES (%s, %s)",
            (session["user_id"], title),
        )
    db.commit()
    flash("To-do added.", "success")
    return redirect(url_for("index"))


@app.route("/todos/<int:todo_id>/edit", methods=["POST"])
@login_required
def edit_todo(todo_id):
    raw = request.form.get("title", "")
    title = raw.strip()
    errors = validate_title(title)
    if errors:
        return render_index(edit_id=todo_id, edit_errors=errors, edit_value=raw)
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s",
            (title, todo_id, session["user_id"]),
        )
    db.commit()
    flash("To-do updated.", "success")
    return redirect(url_for("index"))


@app.route("/todos/<int:todo_id>/toggle", methods=["POST"])
@login_required
def toggle_todo(todo_id):
    value = request.form.get("is_done", "")
    if value not in ("0", "1"):
        return redirect(url_for("index"))
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
            (int(value), todo_id, session["user_id"]),
        )
    db.commit()
    return redirect(url_for("index"))


@app.route("/todos/<int:todo_id>/delete", methods=["POST"])
@login_required
def delete_todo(todo_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
            (todo_id, session["user_id"]),
        )
    db.commit()
    flash("To-do deleted.", "info")
    return redirect(url_for("index"))


@app.errorhandler(Exception)
def handle_error(e):
    if isinstance(e, HTTPException):
        code = e.code
        message = e.name
    else:
        code = 500
        message = "Something went wrong. Please try again later."
    return render_template("error.html", code=code, message=message), code


if __name__ == "__main__":
    app.run(debug=False)