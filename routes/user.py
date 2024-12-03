from functools import wraps
import os
from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_session import Session
from cs50 import SQL
import bcrypt
from werkzeug.utils import secure_filename
from flask_cors import CORS
from routes.log import login_required  # Import custom login_required decorator

# Define a blueprint for user-related routes
user_routes = Blueprint('user', __name__)

# Database initialization
if not os.path.exists("database.db"):  # Check if the database file exists
    open("database.db", "w").close()  # Create an empty database file if not
    db = SQL("sqlite:///database.db")  # Connect to the SQLite database
    # Execute SQL statements from the database.sql file
    with open("database.sql", "r") as sql_file:
        sql_statements = sql_file.read().split(';')
        for statement in sql_statements:
            if statement.strip():  # Avoid empty statements
                db.execute(statement)
else:
    db = SQL("sqlite:///database.db")  # Connect to the existing SQLite database

# Set upload folder and allowed file extensions
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)  # Create the folder if it doesn't exist

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Profile route for viewing and updating user profiles
@user_routes.route("/profile", methods=["GET", "POST"])
@login_required  # Require the user to be logged in
def profile():
    user_id = session["user_id"]  # Get the current user's ID from the session

    if request.method == "POST":
        # Handle profile picture upload
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}.png")  # Secure the file name
            file_path = os.path.join(UPLOAD_FOLDER, filename)  # Determine the file path
            file.save(file_path)  # Save the file to the upload folder
            relative_path = os.path.join('uploads', filename)  # Save relative path

            # Update the profile picture in the database
            db.execute("UPDATE users SET profile_picture = ? WHERE id = ?", relative_path, user_id)
        
        # Redirect back to the user's profile page after handling the POST request
        return redirect(url_for("user.user_profile", user_id=user_id))

    # Handle GET request: Render the user's profile
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        return "User not found", 404  # If the user doesn't exist
    user = user[0]  # Extract the user row as a dictionary

    return render_template("acceuil.html", user=user)  # Render the profile page

# Route to view another user's profile
@user_routes.route("/user/<int:user_id>")
@login_required  # Require the user to be logged in
def user_profile(user_id):
    # Check if the logged-in user matches the user_id
    if session["user_id"] != user_id:
        flash("You are not authorized to view this profile.", "error")
        return redirect("/")

    # Retrieve user information
    rows = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    users = db.execute("SELECT * FROM users")  # Fetch all users
    if len(rows) != 1:
        return "User not found", 404
    games = db.execute("""
        SELECT * FROM games
        WHERE (player1_id = ? OR player2_id = ?)
          AND player2_username IS NOT NULL
          AND player1_username IS NOT NULL
    """, user_id, user_id)
    user = rows[0]  # Extract the user details
    return render_template("acceuil.html", user=user, games=games, users=users)

# Route to fetch user stats
@user_routes.route("/stats", methods=["GET"])
def stats():
    username = request.args.get("username")  # Retrieve the `username` parameter from the URL
    if not username:
        return jsonify({"error": "Username parameter is required"}), 400  # Error if no username is provided

    # Check if the logged-in user is an admin
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if len(user) != 1:
        return jsonify({"error": "Unauthorized"}), 401
    is_admin = user[0].get("role") == "admin"

    # SQL query: If admin, fetch all games; otherwise, apply privacy restrictions
    if is_admin:
        # Fetch all games for the given username (admin override)
        games = db.execute("""
            SELECT g.*
            FROM games g
            WHERE g.player1_username = ? OR g.player2_username = ?
        """, username, username)
    else:
        # Fetch games with privacy restrictions for regular users
        games = db.execute("""
            SELECT g.* 
            FROM games g
            JOIN users u1 ON g.player1_username = u1.username
            JOIN users u2 ON g.player2_username = u2.username
            WHERE (g.player1_username = ? OR g.player2_username = ?)
              AND (
                  (g.player1_username = ? AND u1.status = "public") OR 
                  (g.player2_username = ? AND u2.status = "public")
              )
              AND g.player2_username IS NOT NULL 
              AND g.player1_username IS NOT NULL
        """, username, username, username, username)

    # Convert the results to a list of dictionaries for JSON response
    games_list = [dict(row) for row in games]

    return jsonify(games_list)  # Return the games as JSON

# Route to update the user's privacy status
@user_routes.route("/profile/update_status", methods=["POST"])
def update_status():
    # Check if the user is logged in
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Get the new status from the request
    data = request.get_json()
    new_status = data.get("status")

    if new_status not in ["public", "private"]:
        return jsonify({"error": "Invalid status"}), 400

    # Update the status in the database
    db.execute("UPDATE users SET status = ? WHERE id = ?", new_status, user_id)

    return jsonify({"status": new_status})  # Return the new status as JSON
