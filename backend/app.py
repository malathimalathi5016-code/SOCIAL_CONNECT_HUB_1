from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os

# Import the init_db function
from init_db import init_db

# Initialize the database (creates tables + inserts sample data if missing)
init_db()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret")

DB_PATH = os.path.join(os.path.dirname(__file__), "social_connect.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        existing_user = conn.execute("SELECT * FROM users WHERE email=? OR username=?", (email, username)).fetchone()
        if existing_user:
            conn.close()
            return render_template("register.html", error="Email or username already registered")

        conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        conn.close()
        session["user"] = email
        return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
        conn.close()
        if user:
            session["user"] = email
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid email or password")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if "user" in session:
        conn = get_db()
        user = conn.execute("SELECT username FROM users WHERE email=?", (session["user"],)).fetchone()
        conn.close()
        username = user["username"] if user else session["user"]
        return render_template("dashboard.html", user=username)
    return redirect(url_for("login"))

@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect(url_for("login"))
    if session["user"] != "admin@test.com":
        return redirect(url_for("dashboard"))

    conn = get_db()
    user = conn.execute("SELECT username FROM users WHERE email=?", (session["user"],)).fetchone()
    username = user["username"] if user else session["user"]
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    influencer_count = conn.execute("SELECT COUNT(*) FROM influencers").fetchone()[0]
    favorite_count = conn.execute("SELECT COUNT(*) FROM favorites").fetchone()[0]
    influencers = conn.execute("SELECT * FROM influencers").fetchall()
    conn.close()
    return render_template(
        "admin.html",
        user=username,
        user_count=user_count,
        influencer_count=influencer_count,
        favorite_count=favorite_count,
        influencers=influencers,
    )

@app.route("/profiles")
def profiles():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    influencers = conn.execute("SELECT * FROM influencers").fetchall()
    conn.close()
    return render_template("profiles.html", influencers=influencers)

@app.route("/all-profiles")
def all_profiles():
    conn = get_db()
    influencers = conn.execute("SELECT * FROM influencers").fetchall()
    conn.close()
    return render_template("all_profiles.html", influencers=influencers)

@app.route("/upload-profile", methods=["GET", "POST"])
def upload_profile():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name")
        platform = request.form.get("platform")
        followers = request.form.get("followers")
        promotions = request.form.get("promotions")
        email = request.form.get("email")

        if not name or not platform or not followers:
            return render_template("upload_profile.html", error="Name, platform, and followers are required.")

        conn = get_db()
        conn.execute(
            "INSERT INTO influencers (name, platform, followers, promotions, email) VALUES (?, ?, ?, ?, ?)",
            (name, platform, int(followers), promotions or "", email or "")
        )
        conn.commit()
        conn.close()
        return redirect(url_for("all_profiles"))

    return render_template("upload_profile.html")

@app.route("/favorite/<int:influencer_id>")
def favorite(influencer_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE email=?", (session["user"],)).fetchone()
    if user:
        conn.execute(
            "INSERT INTO favorites (user_id, influencer_id) VALUES (?, ?)",
            (user["id"], influencer_id),
        )
        conn.commit()
    conn.close()
    return redirect(url_for("profiles"))

@app.route("/favorites")
def favorites():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE email=?", (session["user"],)).fetchone()
    influencers = []
    if user:
        influencers = conn.execute(
            """
            SELECT i.* FROM influencers i
            JOIN favorites f ON i.id = f.influencer_id
            WHERE f.user_id=?
            """,
            (user["id"],),
        ).fetchall()
    conn.close()
    return render_template("favorites.html", influencers=influencers)

@app.route("/search", methods=["GET", "POST"])
def search():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    query = "SELECT * FROM influencers WHERE 1=1"
    params = []
    sort_by = request.form.get("sort_by", "name")  # Default sort by name
    if request.method == "POST":
        name = request.form.get("name")
        platform = request.form.get("platform")
        followers = request.form.get("followers")
        keyword = request.form.get("keyword")

        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        if platform:
            query += " AND platform=?"
            params.append(platform)
        if followers:
            query += " AND followers >= ?"
            params.append(followers)
        if keyword:
            query += " AND promotions LIKE ?"
            params.append(f"%{keyword}%")

    # Add sorting
    if sort_by == "name":
        query += " ORDER BY name"
    elif sort_by == "followers":
        query += " ORDER BY followers DESC"
    elif sort_by == "platform":
        query += " ORDER BY platform"

    influencers = conn.execute(query, params).fetchall()
    all_influencers = conn.execute("SELECT * FROM influencers").fetchall()
    conn.close()
    return render_template("search.html", influencers=influencers, all_influencers=all_influencers)

if __name__ == "__main__":
    app.run(debug=True)
