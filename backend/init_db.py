import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "social_connect.db")

schema = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS influencers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    platform TEXT NOT NULL,
    followers INTEGER NOT NULL,
    promotions TEXT,
    email TEXT
);

CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    influencer_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(influencer_id) REFERENCES influencers(id)
);
"""

sample_data = [
    ("Tech Trends", "YouTube", 87000, "Unboxing, Tech Reviews, Sponsored Ads", "contact@techtrends.media"),
    ("Samantha Styles", "Instagram", 25400, "Fashion Reviews, Lifestyle Promotions", "samantha.styles@collab.com"),
    ("Malathi", "Instagram", 20000, "Skincare (30 promotions)", "malathimalathi5016@gmail.com"),
    ("WanderWave", "Facebook", 18300, "Travel Content, Destination Promotions", "connect@wanderwave.com")
]

def init_db():
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("SELECT name FROM sqlite_master LIMIT 1")
            # Check if username column exists
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'username' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
                # Update existing users with username from email or something
                cursor.execute("UPDATE users SET username = email WHERE username IS NULL")
            conn.commit()
            conn.close()
        except sqlite3.DatabaseError:
            os.remove(DB_PATH)

    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executescript(schema)

        # Insert admin user
        cursor.execute("INSERT OR IGNORE INTO users (username, email, password) VALUES (?, ?, ?)", ("admin", "admin@test.com", "admin"))

        # Insert sample influencers
        cursor.executemany(
            "INSERT INTO influencers (name, platform, followers, promotions, email) VALUES (?, ?, ?, ?, ?)",
            sample_data
        )

        conn.commit()
        conn.close()
        print("Database initialized with sample data and favorites table.")
    else:
        print("Database already exists. Initialization skipped.")

if __name__ == "__main__":
    init_db()
