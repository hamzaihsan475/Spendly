import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "spendly.db"


def get_db():
    """
    Open a connection to the SQLite database.
    Sets row_factory for dict-like access and enables foreign key enforcement.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Create the users and expenses tables if they don't exist.
    Safe to call multiple times.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')))"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')))"""
    )

    conn.commit()
    conn.close()


def seed_db():
    """
    Insert demo user and sample expenses if they don't already exist.
    Idempotent - safe to call multiple times without duplicating data.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Check if users table already has data
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Create demo user
    password_hash = generate_password_hash("demo123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash)
    )

    # Get the demo user's ID
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",))
    user_id = cursor.fetchone()[0]

    # Insert 8 sample expenses across different categories
    sample_expenses = [
        (50.00, "Food", "2026-04-01", "Lunch at cafe"),
        (25.50, "Transport", "2026-04-02", "Uber ride"),
        (120.00, "Bills", "2026-04-03", "Electric bill"),
        (45.00, "Health", "2026-04-05", "Pharmacy"),
        (35.00, "Entertainment", "2026-04-07", "Movie tickets"),
        (89.99, "Shopping", "2026-04-08", "New shirt"),
        (15.00, "Food", "2026-04-09", "Groceries"),
        (200.00, "Other", "2026-04-10", "Gift for friend"),
    ]

    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [(user_id, *expense) for expense in sample_expenses]
    )

    conn.commit()
    conn.close()
