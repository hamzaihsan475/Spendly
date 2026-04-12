# Spec: Registration

## Overview
This feature implements user registration for the Spendly expense tracker. Users can create an account by providing their name, email, and password. The registration form validates input and stores user credentials securely in the database with hashed passwords.

## Depends on
- Step 1: Database setup (users table already exists)

## Routes
- `POST /register` — handles registration form submission — public

## Database changes
No database changes — the `users` table already exists from Step 1.

## Templates
- **Modify:** `templates/register.html` — add form with fields for name, email, password; add error/success message display

## Files to change
- `app.py` — add POST route handler for `/register`
- `templates/register.html` — add registration form
- `static/css/style.css` — add form styling if needed

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- Use `werkzeug.security.generate_password_hash()` for password hashing
- Use parameterized queries only (`?` placeholders) — never f-strings in SQL
- Validate that email is unique before inserting
- Validate that password is at least 6 characters
- Validate that all fields are provided
- Use `flash()` for error/success messages
- All templates extend `base.html`
- Use CSS variables — never hardcode hex values
- Redirect to login page on successful registration

## Definition of done
- [ ] Registration form displays with fields: name, email, password
- [ ] Submitting empty fields shows an error message
- [ ] Submitting a duplicate email shows an error message
- [ ] Submitting a password under 6 characters shows an error message
- [ ] Successful registration hashes the password and inserts into `users` table
- [ ] Successful registration redirects to `/login` with a success message
- [ ] Form uses POST method
- [ ] All links use `url_for()`
