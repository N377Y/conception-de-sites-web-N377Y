from functools import wraps
import os
from flask import Flask, render_template, redirect, url_for, flash, request, session
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
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
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
        # Collecte les données du formulaire
        name = request.form.get("name")
        raw_pwd = request.form.get("pwd")

        # Vérifie si les champs sont remplis
        if not name or not raw_pwd:
            flash("Both username and password are required.", "error")
            return redirect(url_for("login"))

        # Récupère l'utilisateur depuis la base de données
        rows = db.execute("SELECT * FROM users WHERE username = ?", name)
        if len(rows) != 1:
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

        user = rows[0]

        # Vérifie le mot de passe
        if not bcrypt.checkpw(raw_pwd.encode('utf-8'), user["password"].encode('utf-8')):
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

        # Stocke les informations utilisateur dans la session
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        # Redirige vers le profil de l'utilisateur
        return redirect(url_for("user_profile", user_id = user["id"]))

    return render_template("login.html")




@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session["user_id"]
    file = request.files["file"]

    # Handle profile picture upload
    relative_path = None
    if file and allowed_file(file.filename):
        filename = secure_filename(str(user_id)+".png")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        relative_path = os.path.join('uploads', filename)  # Save relative path
        print(relative_path)
        db.execute(
                "UPDATE users SET profile_picture= ? WHERE id= ?",
                relative_path,user_id
            )
        return redirect(url_for("user_profile", user_id=user_id))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Collect form data
        name = request.form.get("name")
        raw_pwd = request.form.get("pwd")
        username = request.form.get("username")
        mail = request.form.get("mail")

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
                "INSERT INTO users (username, password, mail, name) VALUES (?, ?, ?, ?)",
                username, hashed_pwd, mail, name
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
    if len(rows) != 1:
        return "User not found", 404

    user = rows[0]
    return render_template("acceuil.html", user=user)



if __name__ == "__main__":
    app.run(debug=True)
