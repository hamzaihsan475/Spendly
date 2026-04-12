import random
import sqlite3
from datetime import datetime, timedelta
import sys

# Import the shared DB helpers
sys.path.insert(0, '.')
from database.db import get_db


# Category definitions with realistic Indian descriptions and amount ranges
CATEGORIES = {
    "Food": {"min": 150, "max": 1800, "weight": 25, "descriptions": [
        "Groceries from local sabzi mandi", "Lunch at office canteen",
        "Dinner at family restaurant", "Street food and snacks",
        "Groceries from D-Mart", "Breakfast at home", "Weekend biryani",
        "Pizza delivery", "Chai and samosas", "South Indian tiffin"
    ]},
    "Transport": {"min": 80, "max": 1500, "weight": 15, "descriptions": [
        "Metro card recharge", "Uber ride to office", "Auto rickshaw fare",
        "Petrol for scooter", "Monthly bus pass", "Taxi to airport",
        "Bike service", "Ola cab", "Train ticket", "Parking fees"
    ]},
    "Bills": {"min": 600, "max": 3000, "weight": 15, "descriptions": [
        "Electricity bill", "Internet broadband", "Mobile phone recharge",
        "Water bill", "Cooking gas cylinder", "DTH subscription",
        "Society maintenance", "Credit card payment", "Loan EMI", "Insurance premium"
    ]},
    "Health": {"min": 500, "max": 20000, "weight": 5, "descriptions": [
        "Pharmacy — vitamins", "Doctor consultation", "Gym membership",
        "Medical test lab", "Physiotherapy session", "Health supplements",
        "Dental checkup", "Eye examination", "Medicines for flu", "Yoga classes"
    ]},
    "Entertainment": {"min": 100, "max": 1500, "weight": 8, "descriptions": [
        "Movie tickets", "Netflix subscription", "Concert tickets",
        "Gaming subscription", "Book purchase", "Amusement park",
        "Bowling night", "Escape room", "Comedy show", "Sports event"
    ]},
    "Shopping": {"min": 200, "max": 5000, "weight": 12, "descriptions": [
        "New earphones", "Clothes from FabIndia", "Shoes from Bata",
        "Home decor items", "Kitchen appliances", "Gift for friend",
        "Cosmetics", "Watch accessories", "Bag purchase", "Electronics"
    ]},
    "Other": {"min": 50, "max": 1000, "weight": 10, "descriptions": [
        "Miscellaneous", "Tips to house help", "Donation to temple",
        "Stationery", "Pet supplies", "Car wash", "Laundry service",
        "Key duplication", "Courier charges", "Small repairs"
    ]}
}


def get_category_weights():
    """Return categories weighted by probability."""
    categories = list(CATEGORIES.keys())
    weights = [CATEGORIES[cat]["weight"] for cat in categories]
    return categories, weights


def generate_expense(user_id, date):
    """Generate a single realistic expense."""
    categories, weights = get_category_weights()
    category = random.choices(categories, weights=weights)[0]

    cat_info = CATEGORIES[category]
    amount = round(random.uniform(cat_info["min"], cat_info["max"]), 2)
    description = random.choice(cat_info["descriptions"])

    return (user_id, amount, category, date.strftime("%Y-%m-%d"), description)


def seed_expenses(user_id, count, months):
    """Seed multiple expenses for a user across specified months."""
    conn = get_db()

    # Step 2: Verify user exists
    cursor = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        print(f"No user found with id {user_id}.")
        conn.close()
        return False

    try:
        # Calculate date range
        today = datetime.now().date()
        start_date = today - timedelta(days=months * 30)

        expenses = []
        for _ in range(count):
            # Random date within the range
            random_days = random.randint(0, months * 30 - 1)
            expense_date = start_date + timedelta(days=random_days)
            expenses.append(generate_expense(user_id, expense_date))

        # Sort by date for cleaner output
        expenses.sort(key=lambda x: x[3])

        # Step 3: Insert all in single transaction
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses
        )
        conn.commit()

        # Step 4: Confirm
        print(f"\n[OK] Successfully inserted {count} expenses for user {user_id}")
        print(f"Date range: {expenses[0][3]} to {expenses[-1][3]}")
        print(f"\nSample of 5 inserted records:")
        print("-" * 80)

        # Show 5 random samples
        sample = random.sample(expenses, min(5, len(expenses)))
        for exp in sample:
            print(f"  Rs.{exp[1]:.2f} | {exp[2]:<15} | {exp[3]} | {exp[4]}")

        print("-" * 80)
        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        print(f"Error inserting expenses: {e}")
        conn.close()
        return False


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) != 4:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
        count = int(sys.argv[2])
        months = int(sys.argv[3])
    except ValueError:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)

    seed_expenses(user_id, count, months)
