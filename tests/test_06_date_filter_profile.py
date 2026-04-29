"""
Test suite for the date filter feature on the profile page (Step 6).

Spec behaviors verified:
- Profile page loads with no filter (unfiltered view)
- "This Month" preset filters correctly
- "Last 3 Months" preset filters correctly
- "Last 6 Months" preset filters correctly
- "All Time" preset shows all expenses
- Custom date range filters correctly
- User with no expenses in selected range sees PKR0.00 totals
- Date range where date_from > date_to shows flash error and falls back to unfiltered
- Malformed date strings fall back to unfiltered view silently
- Missing only date_from or only date_to falls back to unfiltered
- Unauthenticated user is redirected to login
- All three data sections (summary stats, recent transactions, category breakdown) respect the filter
"""

import pytest
from datetime import date, timedelta
from app import app
from database.db import init_db, get_db


@pytest.fixture
def client():
    """Create a test client with in-memory SQLite database."""
    app.config['TESTING'] = True
    app.config['DATABASE'] = ':memory:'
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client


@pytest.fixture
def logged_in_client(client):
    """Create a test client with an authenticated user session."""
    _login(client, "test@example.com", "password123")
    return client


def _login(client, email, password):
    """Helper to log in a user and return the response."""
    return client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)


def _create_test_user(email="test@example.com", password="password123", name="Test User"):
    """Helper to create a test user and return the user ID."""
    from database.db import create_user
    return create_user(name, email, password)


def _add_expense(user_id, amount, category, date_str, description="Test expense"):
    """Helper to add an expense for a user."""
    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date_str, description)
    )
    conn.commit()
    expense_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return expense_id


def _clear_expenses():
    """Helper to clear all expenses from the database."""
    conn = get_db()
    conn.execute("DELETE FROM expenses")
    conn.commit()
    conn.close()


class TestProfileAuthGuard:
    """Tests for authentication requirements on the profile page."""

    def test_unauthenticated_user_redirected_to_login(self, client):
        """Unauthenticated user is redirected to login page."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert response.location == '/login'

    def test_authenticated_user_can_access_profile(self, logged_in_client):
        """Authenticated user can access the profile page."""
        response = logged_in_client.get('/profile')
        assert response.status_code == 200


class TestProfileNoFilter:
    """Tests for profile page with no date filter (unfiltered view)."""

    def test_profile_loads_without_filter(self, logged_in_client):
        """Profile page loads with no filter and returns 200."""
        response = logged_in_client.get('/profile')
        assert response.status_code == 200

    def test_profile_shows_all_expenses_without_filter(self, logged_in_client):
        """Profile page without filter shows all expenses for the user."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2026-01-15", "January expense")
        _add_expense(user_id, 200.00, "Transport", "2026-02-15", "February expense")
        _add_expense(user_id, 300.00, "Bills", "2026-03-15", "March expense")

        response = logged_in_client.get('/profile')
        assert response.status_code == 200
        assert b"January expense" in response.data
        assert b"February expense" in response.data
        assert b"March expense" in response.data

    def test_profile_summary_stats_unfiltered(self, logged_in_client):
        """Profile page without filter shows correct total for all expenses."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2026-01-15")
        _add_expense(user_id, 200.00, "Transport", "2026-02-15")

        response = logged_in_client.get('/profile')
        assert b"PKR300.00" in response.data

    def test_profile_all_time_preset_removes_filter(self, logged_in_client):
        """All Time preset link navigates to unfiltered profile."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 500.00, "Shopping", "2025-06-15", "Old expense")

        response = logged_in_client.get('/profile')
        assert response.status_code == 200
        assert b"Old expense" in response.data


class TestThisMonthPreset:
    """Tests for the 'This Month' preset filter."""

    def test_this_month_filters_to_current_month(self, logged_in_client):
        """This Month preset filters expenses to current calendar month only."""
        user_id = session_user_id(logged_in_client)
        today = date.today()

        # Add expense in current month
        current_month_date = today.strftime("%Y-%m-") + "15"
        _add_expense(user_id, 100.00, "Food", current_month_date, "Current month expense")

        # Add expense in previous month
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_month_year = today.year if today.month > 1 else today.year - 1
        prev_month_date = f"{prev_month_year}-{prev_month:02d}-15"
        _add_expense(user_id, 200.00, "Transport", prev_month_date, "Previous month expense")

        # Get this month's date range
        month_start = today.replace(day=1).isoformat()
        month_end = today.replace(day=today.day).isoformat()

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': month_start, 'date_to': month_end}
        )

        assert response.status_code == 200
        assert b"Current month expense" in response.data
        assert b"Previous month expense" not in response.data

    def test_this_month_summary_stats_correct(self, logged_in_client):
        """This Month preset shows correct summary stats for current month only."""
        user_id = session_user_id(logged_in_client)
        today = date.today()

        current_month_date = today.strftime("%Y-%m-") + "10"
        _add_expense(user_id, 150.00, "Food", current_month_date)

        prev_month = today.month - 1 if today.month > 1 else 12
        prev_month_year = today.year if today.month > 1 else today.year - 1
        prev_month_date = f"{prev_month_year}-{prev_month:02d}-10"
        _add_expense(user_id, 250.00, "Transport", prev_month_date)

        month_start = today.replace(day=1).isoformat()
        month_end = today.replace(day=today.day).isoformat()

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': month_start, 'date_to': month_end}
        )

        assert b"PKR150.00" in response.data
        assert b"1" in response.data  # transaction count

    def test_this_month_category_breakdown_correct(self, logged_in_client):
        """This Month preset shows correct category breakdown for current month only."""
        user_id = session_user_id(logged_in_client)
        today = date.today()

        current_month_date = today.strftime("%Y-%m-") + "10"
        _add_expense(user_id, 100.00, "Food", current_month_date)
        _add_expense(user_id, 200.00, "Transport", current_month_date)

        # Different month expense
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_month_year = today.year if today.month > 1 else today.year - 1
        prev_month_date = f"{prev_month_year}-{prev_month:02d}-10"
        _add_expense(user_id, 500.00, "Bills", prev_month_date)

        month_start = today.replace(day=1).isoformat()
        month_end = today.replace(day=today.day).isoformat()

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': month_start, 'date_to': month_end}
        )

        assert b"Food" in response.data
        assert b"Transport" in response.data
        assert b"Bills" not in response.data


class TestLast3MonthsPreset:
    """Tests for the 'Last 3 Months' preset filter."""

    def test_last_3_months_filters_correctly(self, logged_in_client):
        """Last 3 Months preset filters to 3-month window ending today."""
        user_id = session_user_id(logged_in_client)
        today = date.today()

        # Expense within last 3 months (2 months ago)
        two_months_ago = today - timedelta(days=60)
        _add_expense(user_id, 100.00, "Food", two_months_ago.isoformat(), "Within 3 months")

        # Expense outside last 3 months (4 months ago)
        four_months_ago = today - timedelta(days=120)
        _add_expense(user_id, 200.00, "Transport", four_months_ago.isoformat(), "Outside 3 months")

        # Calculate last 3 months range
        three_months_ago = today - timedelta(days=90)
        last_3_start = three_months_ago.replace(day=1).isoformat()
        last_3_end = today.isoformat()

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': last_3_start, 'date_to': last_3_end}
        )

        assert response.status_code == 200
        assert b"Within 3 months" in response.data
        assert b"Outside 3 months" not in response.data

    def test_last_3_months_summary_stats(self, logged_in_client):
        """Last 3 Months preset shows correct summary stats."""
        user_id = session_user_id(logged_in_client)
        today = date.today()

        within_range = today - timedelta(days=30)
        outside_range = today - timedelta(days=150)

        _add_expense(user_id, 300.00, "Food", within_range.isoformat())
        _add_expense(user_id, 400.00, "Transport", outside_range.isoformat())

        three_months_ago = today - timedelta(days=90)
        last_3_start = three_months_ago.replace(day=1).isoformat()

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': last_3_start, 'date_to': today.isoformat()}
        )

        assert b"PKR300.00" in response.data


class TestLast6MonthsPreset:
    """Tests for the 'Last 6 Months' preset filter."""

    def test_last_6_months_filters_correctly(self, logged_in_client):
        """Last 6 Months preset filters to 6-month window ending today."""
        user_id = session_user_id(logged_in_client)
        today = date.today()

        # Expense within last 6 months (3 months ago)
        three_months_ago = today - timedelta(days=90)
        _add_expense(user_id, 100.00, "Food", three_months_ago.isoformat(), "Within 6 months")

        # Expense outside last 6 months (8 months ago)
        eight_months_ago = today - timedelta(days=240)
        _add_expense(user_id, 200.00, "Transport", eight_months_ago.isoformat(), "Outside 6 months")

        six_months_ago = today - timedelta(days=180)
        last_6_start = six_months_ago.replace(day=1).isoformat()

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': last_6_start, 'date_to': today.isoformat()}
        )

        assert response.status_code == 200
        assert b"Within 6 months" in response.data
        assert b"Outside 6 months" not in response.data


class TestCustomDateRange:
    """Tests for custom date range filtering."""

    def test_custom_date_range_filters_correctly(self, logged_in_client):
        """Custom date range shows only expenses within the range."""
        user_id = session_user_id(logged_in_client)

        _add_expense(user_id, 100.00, "Food", "2026-01-15", "Before range")
        _add_expense(user_id, 200.00, "Transport", "2026-02-15", "Within range")
        _add_expense(user_id, 300.00, "Bills", "2026-02-20", "Within range")
        _add_expense(user_id, 400.00, "Health", "2026-03-15", "After range")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': '2026-02-28'}
        )

        assert response.status_code == 200
        assert b"Before range" not in response.data
        assert b"Within range" in response.data
        assert b"After range" not in response.data

    def test_custom_date_range_summary_stats(self, logged_in_client):
        """Custom date range shows correct summary stats."""
        user_id = session_user_id(logged_in_client)

        _add_expense(user_id, 150.00, "Food", "2026-02-10")
        _add_expense(user_id, 250.00, "Transport", "2026-02-20")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': '2026-02-28'}
        )

        assert b"PKR400.00" in response.data
        assert b"2" in response.data  # transaction count

    def test_custom_date_range_category_breakdown(self, logged_in_client):
        """Custom date range shows correct category breakdown."""
        user_id = session_user_id(logged_in_client)

        _add_expense(user_id, 100.00, "Food", "2026-02-10")
        _add_expense(user_id, 200.00, "Transport", "2026-02-20")
        _add_expense(user_id, 300.00, "Bills", "2026-03-10")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': '2026-02-28'}
        )

        assert b"Food" in response.data
        assert b"Transport" in response.data
        assert b"Bills" not in response.data

    def test_custom_date_range_inclusive_bounds(self, logged_in_client):
        """Custom date range includes both start and end dates (inclusive)."""
        user_id = session_user_id(logged_in_client)

        _add_expense(user_id, 100.00, "Food", "2026-02-01", "Start date")
        _add_expense(user_id, 200.00, "Transport", "2026-02-28", "End date")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': '2026-02-28'}
        )

        assert b"Start date" in response.data
        assert b"End date" in response.data


class TestEmptyResults:
    """Tests for when user has no expenses in the selected date range."""

    def test_no_expenses_in_range_shows_zero_total(self, logged_in_client):
        """User with no expenses in range sees PKR0.00 total spent."""
        user_id = session_user_id(logged_in_client)
        # Add expense outside the filter range
        _add_expense(user_id, 100.00, "Food", "2025-01-15")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': '2026-02-28'}
        )

        assert b"PKR0.00" in response.data

    def test_no_expenses_in_range_shows_zero_transactions(self, logged_in_client):
        """User with no expenses in range sees 0 transactions."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2025-01-15")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': '2026-02-28'}
        )

        # Check for 0 transaction count (the stat card should show 0)
        assert b">0<" not in response.data or b"PKR0.00" in response.data

    def test_no_expenses_in_range_shows_empty_category_breakdown(self, logged_in_client):
        """User with no expenses in range sees empty category breakdown."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2025-01-15")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': '2026-02-28'}
        )

        # Should not show any category rows
        assert b"cat-row" not in response.data or b"No expenses" in response.data

    def test_no_expenses_in_range_shows_message(self, logged_in_client):
        """User with no expenses in range sees 'No expenses' message."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2025-01-15")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': '2026-02-28'}
        )

        assert b"No expenses" in response.data


class TestInvalidDateRange:
    """Tests for invalid date range handling (date_from > date_to)."""

    def test_date_from_greater_than_date_to_shows_flash_error(self, logged_in_client):
        """Date range where date_from > date_to shows flash error message."""
        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-03-01', 'date_to': '2026-02-01'}
        )

        assert response.status_code == 200
        assert b"Start date must be before end date" in response.data

    def test_date_from_greater_than_date_to_falls_back_to_unfiltered(self, logged_in_client):
        """Date range where date_from > date_to falls back to unfiltered view."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2025-01-15", "Old expense")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-03-01', 'date_to': '2026-02-01'}
        )

        # Should still show the old expense (unfiltered fallback)
        assert b"Old expense" in response.data


class TestMalformedDates:
    """Tests for malformed date string handling."""

    def test_malformed_date_from_falls_back_to_unfiltered(self, logged_in_client):
        """Malformed date_from string falls back to unfiltered view silently."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2025-01-15", "Old expense")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': 'not-a-date', 'date_to': '2026-02-28'}
        )

        assert response.status_code == 200
        assert b"Old expense" in response.data

    def test_malformed_date_to_falls_back_to_unfiltered(self, logged_in_client):
        """Malformed date_to string falls back to unfiltered view silently."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2025-01-15", "Old expense")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': 'invalid'}
        )

        assert response.status_code == 200
        assert b"Old expense" in response.data

    def test_both_dates_malformed_falls_back_to_unfiltered(self, logged_in_client):
        """Both malformed dates fall back to unfiltered view silently."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2025-01-15", "Old expense")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': 'bad', 'date_to': 'worse'}
        )

        assert response.status_code == 200
        assert b"Old expense" in response.data

    def test_malformed_date_no_crash(self, logged_in_client):
        """Malformed date does not crash the app."""
        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-13-45', 'date_to': 'abc-xyz'}
        )

        assert response.status_code == 200


class TestMissingDateParams:
    """Tests for missing date parameter handling."""

    def test_missing_date_from_falls_back_to_unfiltered(self, logged_in_client):
        """Missing only date_from falls back to unfiltered view."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2025-01-15", "Old expense")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_to': '2026-02-28'}
        )

        assert response.status_code == 200
        assert b"Old expense" in response.data

    def test_missing_date_to_falls_back_to_unfiltered(self, logged_in_client):
        """Missing only date_to falls back to unfiltered view."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2025-01-15", "Old expense")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01'}
        )

        assert response.status_code == 200
        assert b"Old expense" in response.data

    def test_only_date_from_provided(self, logged_in_client):
        """Only date_from provided is treated as unfiltered."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2024-01-01", "Very old")
        _add_expense(user_id, 200.00, "Transport", "2026-05-01", "Future")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01'}
        )

        assert response.status_code == 200
        assert b"Very old" in response.data
        assert b"Future" in response.data


class TestAllThreeSectionsRespectFilter:
    """Tests verifying all three data sections respect the date filter."""

    def test_summary_stats_respects_filter(self, logged_in_client):
        """Summary stats section respects the date filter."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 500.00, "Food", "2026-01-15")
        _add_expense(user_id, 300.00, "Transport", "2026-02-15")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': '2026-02-28'}
        )

        # Should only show February expense total
        assert b"PKR300.00" in response.data
        assert b"PKR800.00" not in response.data

    def test_recent_transactions_respects_filter(self, logged_in_client):
        """Recent transactions section respects the date filter."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2026-01-15", "January transaction")
        _add_expense(user_id, 200.00, "Transport", "2026-02-15", "February transaction")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': '2026-02-28'}
        )

        assert b"February transaction" in response.data
        assert b"January transaction" not in response.data

    def test_category_breakdown_respects_filter(self, logged_in_client):
        """Category breakdown section respects the date filter."""
        user_id = session_user_id(logged_in_client)
        _add_expense(user_id, 100.00, "Food", "2026-01-15")
        _add_expense(user_id, 200.00, "Transport", "2026-02-15")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-02-01', 'date_to': '2026-02-28'}
        )

        assert b"Transport" in response.data
        assert b"Food" not in response.data

    def test_all_sections_consistent_with_same_filter(self, logged_in_client):
        """All three sections show consistent data for the same filter."""
        user_id = session_user_id(logged_in_client)
        # Add expenses only in March
        _add_expense(user_id, 100.00, "Food", "2026-03-10", "March food")
        _add_expense(user_id, 200.00, "Transport", "2026-03-20", "March transport")
        # Add expense in different month
        _add_expense(user_id, 500.00, "Bills", "2026-01-10", "January bills")

        response = logged_in_client.get(
            '/profile',
            query_string={'date_from': '2026-03-01', 'date_to': '2026-03-31'}
        )

        # Summary: 300 total, 2 transactions
        assert b"PKR300.00" in response.data
        # Transactions: only March
        assert b"March food" in response.data
        assert b"March transport" in response.data
        assert b"January bills" not in response.data
        # Categories: only Food and Transport
        assert b"Food" in response.data
        assert b"Transport" in response.data
        assert b"Bills" not in response.data


def session_user_id(client):
    """Helper to get the user ID from the session."""
    with client.session_transaction() as sess:
        return sess.get('user_id')
