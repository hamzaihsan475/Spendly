import random
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

# Import the shared DB helpers
import sys
sys.path.insert(0, '.')
from database.db import get_db


# Common Pakistani first names (mixed regions/ethnicities)
FIRST_NAMES = [
    "Ahmed", "Ali", "Hassan", "Usman", "Bilal", "Omar", "Yusuf", "Ibrahim",
    "Ayesha", "Fatima", "Zainab", "Maryam", "Sana", "Hira", "Mahnoor",
    "Muhammad", "Hamza", "Saad", "Khalid", "Tariq", "Naveed", "Shahid",
    "Amna", "Khadija", "Amina", "Zubair", "Farhan", "Adnan", "Waleed"
]

# Common Pakistani last names
LAST_NAMES = [
    "Khan", "Malik", "Ahmed", "Ali", "Hussain", "Butt", "Sheikh", "Qureshi",
    "Siddiqui", "Farooqui", "Ansari", "Chaudhry", "Raza", "Haider", "Mirza",
    "Iqbal", "Akhtar", "Hassan", "Abbas", "Zaidi", "Naqvi", "Bukhari"
]

# Common email domains in Pakistan
DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]


def generate_pakistani_user():
    """Generate a realistic Pakistani user profile."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"

    # Email: Name.Number@domain format
    number_suffix = random.randint(10, 99)
    email_username = f"{first_name.lower()}.{last_name.lower()}{number_suffix}"
    domain = random.choice(DOMAINS)
    email = f"{email_username}@{domain}"

    # Standard password for testing
    password_hash = generate_password_hash("password123")

    # Current datetime
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "created_at": created_at
    }


def email_exists(conn, email):
    """Check if email already exists in users table."""
    cursor = conn.execute("SELECT id FROM users WHERE email = ?", (email,))
    return cursor.fetchone() is not None


def seed_user():
    """Seed a single Pakistani user into the database."""
    conn = get_db()

    max_attempts = 10
    for attempt in range(max_attempts):
        user = generate_pakistani_user()

        if not email_exists(conn, user["email"]):
            break
        else:
            print(f"Email {user['email']} already exists, regenerating...")
    else:
        print("Could not generate unique email after 10 attempts")
        conn.close()
        return None

    # Insert the user
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (user["name"], user["email"], user["password_hash"], user["created_at"])
    )
    conn.commit()

    user_id = cursor.lastrowid

    print(f"User seeded successfully!")
    print(f"  id: {user_id}")
    print(f"  name: {user['name']}")
    print(f"  email: {user['email']}")

    conn.close()
    return user_id


if __name__ == "__main__":
    seed_user()
