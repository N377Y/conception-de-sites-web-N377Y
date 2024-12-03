from functools import wraps
import os
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_session import Session
from cs50 import SQL
import bcrypt
from werkzeug.utils import secure_filename
from routes.parties import parties_routes  # Import the parties blueprint
from routes.user import user_routes  # Import the user blueprint
from routes.log import login_routes  # Import the login blueprint
from routes.admin import admin_routes  # Import the admin blueprint
from flask_cors import CORS  # Enable Cross-Origin Resource Sharing (CORS)

# Initialize the Flask app
app = Flask(__name__)

# Register blueprints for modular routing
app.register_blueprint(parties_routes)  # Register game-related routes
app.register_blueprint(user_routes)  # Register user-related routes
app.register_blueprint(login_routes)  # Register authentication-related routes
app.register_blueprint(admin_routes)  # Register admin-related routes

# Set a secret key for session management
app.secret_key = "myKey"

# Enable CORS for handling cross-origin requests
CORS(app)

# Configure session settings
app.config['SESSION_TYPE'] = 'filesystem'  # Use the filesystem to store session data
app.config['SESSION_PERMANENT'] = False  # Do not make sessions permanent
app.config['SESSION_USE_SIGNER'] = True  # Use a secure signer for sessions
app.config['SESSION_COOKIE_SECURE'] = True  # Ensure cookies are only sent over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Restrict cookies to same-site requests
Session(app)  # Initialize session handling

# Create the SQLite database if it doesn't exist
if not os.path.exists("database.db"):  # Check if the database file exists
    open("database.db", "w").close()  # Create an empty database file if not
    db = SQL("sqlite:///database.db")  # Connect to the SQLite database
    with open("database.sql", "r") as sql_file:  # Execute SQL statements to initialize tables
        db.execute(sql_file.read())
else:
    db = SQL("sqlite:///database.db")  # Connect to the existing SQLite database

# Configure upload folder and allowed file extensions
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Define allowed file extensions

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Set the upload folder in app configuration

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)  # Create the upload folder if it doesn't exist

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    """
    Render the home page (login page by default).
    """
    return render_template("login.html", name=session.get("name"))  # Pass the session name to the template

if __name__ == "__main__":
    # Run the app in debug mode for easier development and debugging
    app.run(debug=True)
