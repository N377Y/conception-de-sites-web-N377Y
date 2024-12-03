from functools import wraps
import os
from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_session import Session
from cs50 import SQL
import bcrypt
from werkzeug.utils import secure_filename
from flask_cors import CORS

# Create a Blueprint for authentication-related routes
login_routes = Blueprint('log', __name__)

# Initialize the database if it doesn't already exist
if not os.path.exists("database.db"):  # Check if the database file exists
    open("database.db", "w").close()  # Create an empty database file if not
    db = SQL("sqlite:///database.db")  # Connect to the SQLite database
    with open("database.sql", "r") as sql_file:  # Create tables from the SQL schema
        db.execute(sql_file.read())
else:
    db = SQL("sqlite:///database.db")  # Connect to the existing SQLite database

def login_required(f):
    """
    Decorator to enforce login.
    Redirects users to the login page if they are not logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:  # Check if the user is logged in
            flash("Please login first", "error")
            return redirect(url_for("log.login"))  # Redirect to the login page
        return f(*args, **kwargs)
    return decorated_function

@login_routes.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login.
    Validates user credentials and redirects them to the appropriate page based on their role.
    """
    if request.method == "POST":
        # Get username and password from the form
        name = request.form.get("name")
        raw_pwd = request.form.get("pwd")

        # Validate input
        if not name or not raw_pwd:
            flash("Both username and password are required.", "error")
            return redirect(url_for("log.login"))

        # Fetch the user from the database
        rows = db.execute("SELECT * FROM users WHERE username = ?", name)
        if len(rows) != 1:
            flash("Invalid username or password.", "error")
            return redirect(url_for("log.login"))

        user = rows[0]  # Get the user record

        # Check if the password is correct
        if not bcrypt.checkpw(raw_pwd.encode('utf-8'), user["password"].encode('utf-8')):
            flash("Invalid username or password.", "error")
            return redirect(url_for("log.login"))

        # Store user information in the session
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user.get("role", "user")  # Default role is 'user'

        # Redirect the user based on their role
        if session["role"] == "admin":
            return redirect(url_for("admin.admin_dashboard"))  # Redirect admins to the admin dashboard
        else:
            return redirect(url_for("user.user_profile", user_id=user["id"]))  # Redirect regular users to their profile

    return render_template("login.html")  # Render the login page for GET requests

@login_routes.route("/logout")
def logout():
    """
    Handle user logout.
    Clears the session and redirects to the homepage.
    """
    session.clear()  # Clear all session data
    return redirect("/")  # Redirect to the homepage

@login_routes.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle user registration.
    Validates input, checks for duplicates, and creates a new user.
    """
    if request.method == "POST":
        # Collect form data
        name = request.form.get("name")
        raw_pwd = request.form.get("pwd")
        username = request.form.get("username")
        mail = request.form.get("mail")
        status_state = request.form.get("status")  # Get the user's privacy status preference

        # Determine the user's initial status
        if status_state:
            status = "public"
        else:
            status = "private"

        # Validate all required fields
        if not name or not raw_pwd or not username or not mail:
            flash("All fields are required.", "error")
            return redirect(url_for("log.register"))

        # Check for duplicate usernames
        existing_user = db.execute(
            "SELECT * FROM users WHERE username = ?", 
            username
        )
        if existing_user:
            flash("Username or email already exists. Please choose another.", "error")
            return redirect(url_for("log.register"))

        # Hash the user's password
        hashed_pwd = bcrypt.hashpw(raw_pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert the new user into the database
        try:
            db.execute(
                "INSERT INTO users (username, password, mail, name, status, role) VALUES (?, ?, ?, ?, ?, 'user')",
                username, hashed_pwd, mail, name, status
            )
        except Exception as e:
            print(f"Error inserting user: {e}")
            flash("An unexpected error occurred. Please try again.", "error")
            return redirect(url_for("log.register"))

        flash("Registration successful! Please log in.", "success")
        return redirect("/login")  # Redirect to the login page after successful registration

    return render_template("register.html")  # Render the registration page for GET requests
