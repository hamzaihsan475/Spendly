---
# Spec: Edit Expense

## Overview
This feature allows users to modify existing expense entries. Users can update the amount, category, date, and description of an expense they have previously added. This is a critical part of the expense management flow, ensuring that users can correct mistakes or update transaction details.

## Depends on
- 07-add-expense

## Routes
- `GET /expenses/<int:id>/edit` — Renders the edit expense form with current data — logged-in
- `POST /expenses/<int:id>/edit` — Updates the expense in the database — logged-in

## Database changes
No database changes.

## Templates
- **Create:** `templates/edit_expense.html`
- **Modify:** No existing templates to modify.

## Files to change
- `app.py`: Implement the `edit_expense` route.
- `database/db.py`: Add a helper function to fetch a single expense by ID and another to update an expense.

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Ensure the user editing the expense is the owner of that expense (prevent unauthorized edits).

## Definition of done
- [ ] Navigate to `/expenses/<id>/edit` for a valid expense and see a form pre-filled with current data.
- [ ] Navigate to `/expenses/<id>/edit` for a non-existent expense and see a 404 error.
- [ ] Attempt to edit an expense belonging to another user and be blocked (e.g., 403 Forbidden or redirect).
- [ ] Successfully update an expense's amount, category, date, and description and see the changes reflected on the profile page.
- [ ] Validate that invalid input (e.g., negative amount or invalid date) triggers a validation error and doesn't update the database.
---
