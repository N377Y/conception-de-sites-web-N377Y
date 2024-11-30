from functools import wraps
import os
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_session import Session
from cs50 import SQL
import bcrypt
from werkzeug.utils import secure_filename
from routes.parties import parties_routes
from flask_cors import CORS



app = Flask(__name__)
app.register_blueprint(parties_routes)  # Register the blueprint
app.secret_key = "myKey"
CORS(app)
# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
Session(app)


# Create the SQLite database if it doesn't exist
if not os.path.exists("database.db"):
    open("database.db", "w").close()
    db = SQL("sqlite:///database.db")
    with open("database.sql", "r") as sql_file:
        db.execute(sql_file.read())
else:
    db = SQL("sqlite:///database.db")

# Set upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

  
def login_required(f): 
    
    """
    Decorator to require login
    Redirects to the login page if the user is not logged in
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:  # Correct session key
            flash("Please login first", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function



@app.route("/")
def home():
    return render_template("login.html", name=session.get("name"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        raw_pwd = request.form.get("pwd")

        # Validate input
        if not name or not raw_pwd:
            flash("Both username and password are required.", "error")
            return redirect(url_for("login"))

        # Fetch the user from the database
        rows = db.execute("SELECT * FROM users WHERE username = ?", name)
        if len(rows) != 1:
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

        user = rows[0]

        # Check the password
        if not bcrypt.checkpw(raw_pwd.encode('utf-8'), user["password"].encode('utf-8')):
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

        # Store user details in session
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user.get("role", "user")  # Default to 'user' if no role is set

        # Redirect based on user role
        if session["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("user_profile", user_id=user["id"]))

    return render_template("login.html")





@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]

    if request.method == "POST":
        # Handle profile picture upload
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}.png")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            relative_path = os.path.join('uploads', filename)  # Save relative path

            # Update the profile picture in the database
            db.execute("UPDATE users SET profile_picture = ? WHERE id = ?", relative_path, user_id)
        
        # Redirect back to the user's profile page after handling the POST request
        return redirect(url_for("user_profile", user_id=user_id)) 

    # Handle GET request: Render the user's profile
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        return "User not found", 404  # If user doesn't exist
    user = user[0]  # Extract the user row as a dictionary

    return render_template("acceuil.html", user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Collect form data
        name = request.form.get("name")
        raw_pwd = request.form.get("pwd")
        username = request.form.get("username")
        mail = request.form.get("mail")
        status_state = request.form.get("status")

        if status_state:
            status = "public"
        else:
            status = "private"

        # Validate fields
        if not name or not raw_pwd or not username or not mail:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        # Check for duplicate username or email
        existing_user = db.execute(
            "SELECT * FROM users WHERE username = ?", 
            username
        )
        if existing_user:
            flash("Username or email already exists. Please choose another.", "error")
            return redirect(url_for("register"))

        # Hash the password
        hashed_pwd = bcrypt.hashpw(raw_pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


        # Insert the user into the database
        try:
            db.execute(
                "INSERT INTO users (username, password, mail, name, status, role) VALUES (?, ?, ?, ?, ?, 'user')",
                username, hashed_pwd, mail, name, status
            )
        except Exception as e:
            print(f"Error inserting user: {e}")
            flash("An unexpected error occurred. Please try again.", "error")
            return redirect(url_for("register"))

        flash("Registration successful! Please log in.", "success")
        return redirect("/login")

    return render_template("register.html")


@app.route("/user/<int:user_id>")
@login_required
def user_profile(user_id):
    # Vérifie si l'utilisateur connecté correspond à user_id
    if session["user_id"] != user_id:
        flash("You are not authorized to view this profile.", "error")
        return redirect("/")

    # Récupération des informations utilisateur
    rows = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    users = db.execute("SELECT * FROM users ")
    if len(rows) != 1:
        return "User not found", 404
    games = db.execute("SELECT * FROM games WHERE (player1_id = ? OR player2_id = ?) AND player2_username IS NOT NULL AND player1_username IS NOT NULL", user_id, user_id)
    user = rows[0]
    return render_template("acceuil.html", user=user, games = games, users = users)

@app.route("/stats", methods=["GET"])
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

    return jsonify(games_list)


@app.route("/profile/update_status", methods=["POST"])
def update_status():
    # Check if user is logged in
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

    return jsonify({"status": new_status})


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/admin", methods=["GET"])
@admin_required
def admin_dashboard():
    users = db.execute("SELECT * FROM users")
    games = db.execute("SELECT * FROM games")
    return render_template("admin_dashboard.html", users=users, games=games)


@app.route("/admin/add_user", methods=["POST"])
@admin_required
def add_user():
    name = request.form.get("name")
    username = request.form.get("username")
    email = request.form.get("email")
    password = bcrypt.hashpw(request.form.get("password").encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    role = request.form.get("role")

    db.execute("INSERT INTO users ( name, username, mail, password, role) VALUES (?, ?, ?, ?, ?)", name, username, email, password, role)
    return jsonify({"message": "User added successfully!"})


@app.route("/admin/delete_user", methods=["POST"])
@admin_required
def delete_user():
    user_id = request.form.get("user_id")
    db.execute("DELETE FROM users WHERE id = ?", user_id)
    return jsonify({"message": "User deleted successfully!"})


@app.route("/admin/clear_database", methods=["POST"])
@admin_required
def clear_database():
    db.execute("DELETE FROM games")
    db.execute("DELETE FROM users WHERE role != 'admin'")
    return jsonify({"message": "Database cleared successfully!"})



@app.cli.command("create-admin")
def create_admin():
    name = input("Enter admin name: ")
    username = input("Enter admin username: ")
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
  # Insert the admin user into the database
    try:
        db.execute("""
            INSERT INTO users (name, username, mail, password, role)
            VALUES (?, ?, ?, ?, 'admin')
        """, name, username, email, hashed_password)
        print("Admin user created successfully.")
    except Exception as e:
        print(f"Error creating admin user: {e}")

    print("Admin user created successfully.")

if __name__ == "__main__":
    app.run(debug=True)
