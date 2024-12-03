from functools import wraps
import os
from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_session import Session
from cs50 import SQL
import bcrypt
from werkzeug.utils import secure_filename
from flask_cors import CORS

# Create a Blueprint for admin-related routes
admin_routes = Blueprint('admin', __name__)

# Initialize the database
if not os.path.exists("database.db"):  # Check if the database file exists
    open("database.db", "w").close()  # Create an empty database file if not
    db = SQL("sqlite:///database.db")  # Connect to the SQLite database
    # Create tables if they don't already exist
    with open("database.sql", "r") as sql_file:
        sql_statements = sql_file.read().split(';')
        for statement in sql_statements:
            if statement.strip():  # Avoid executing empty statements
                db.execute(statement)
else:
    db = SQL("sqlite:///database.db")  # Connect to the existing SQLite database

def admin_required(f):
    """
    Decorator to enforce admin access.
    Redirects to the homepage if the user is not an admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":  # Check if the user's role is 'admin'
            return redirect(url_for("home"))  # Redirect to the homepage
        return f(*args, **kwargs)
    return decorated_function

@admin_routes.route("/admin", methods=["GET"])
@admin_required  # Enforce admin access
def admin_dashboard():
    """
    Render the admin dashboard displaying all users and games.
    """
    users = db.execute("SELECT * FROM users")  # Fetch all users
    games = db.execute("SELECT * FROM games")  # Fetch all games
    return render_template("admin_dashboard.html", users=users, games=games)

@admin_routes.route("/admin/add_user", methods=["POST"])
@admin_required  # Enforce admin access
def add_user():
    """
    Add a new user to the database.
    """
    # Collect form data
    name = request.form.get("name")
    username = request.form.get("username")
    email = request.form.get("email")
    password = bcrypt.hashpw(request.form.get("password").encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    role = request.form.get("role")  # Get the user's role

    # Insert the new user into the database
    db.execute("INSERT INTO users (name, username, mail, password, role) VALUES (?, ?, ?, ?, ?)", 
               name, username, email, password, role)
    return jsonify({"message": "User added successfully!"})  # Return a success message as JSON

@admin_routes.route("/admin/delete_user", methods=["POST"])
@admin_required  # Enforce admin access
def delete_user():
    """
    Delete a user from the database.
    """
    user_id = request.form.get("user_id")  # Get the user ID from the form data
    db.execute("DELETE FROM users WHERE id = ?", user_id)  # Delete the user from the database
    return jsonify({"message": "User deleted successfully!"})  # Return a success message as JSON

@admin_routes.route("/admin/clear_database", methods=["POST"])
@admin_required  # Enforce admin access
def clear_database():
    """
    Clear all non-admin users and games from the database.
    """
    db.execute("DELETE FROM games")  # Delete all games
    db.execute("DELETE FROM users WHERE role != 'admin'")  # Delete all non-admin users
    return jsonify({"message": "Database cleared successfully!"})  # Return a success message as JSON

@admin_routes.cli.command("create-admin")
def create_admin():
    """
    Command-line function to create an admin user.
    """
    # Collect admin details from the command line
    name = input("Enter admin name: ")
    username = input("Enter admin username: ")
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Hash the password

    # Insert the admin user into the database
    try:
        db.execute("""
            INSERT INTO users (name, username, mail, password, role)
            VALUES (?, ?, ?, ?, 'admin')
        """, name, username, email, hashed_password)
        print("Admin user created successfully.")
    except Exception as e:
        print(f"Error creating admin user: {e}")

    print("Admin user created successfully.")  # Confirm success
