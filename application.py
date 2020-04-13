import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from flask_uploads import UploadSet, configure_uploads, IMAGES
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///picshare.db")





# Photo upload setup
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/images'
configure_uploads(app, photos)


@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        if not request.form.get("password"):
            return apology("must provide password", 403)

        password = request.form.get("password")
        hash = generate_password_hash(password)
        filename = request.files['photo']
        filename = photos.save(filename)
        db.execute("INSERT INTO photos (filename, username, password) VALUES (?, ?, ?)", filename, username, hash)
        return redirect('/')

    return render_template('/upload.html', username=username)

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    if request.method == "POST":
        id = request.form.get("photoid")
        db.execute(f"DELETE FROM photos WHERE filename= '{id}'")
        return redirect("/")
    else:
        return redirect("/")

@app.route("/view", methods=["GET", "POST"])
@login_required
def view():
    if request.method == "POST":
        global id
        id = request.form.get("id")
        global photo
        photo = db.execute(f"SELECT * FROM photos WHERE id = '{id}'")
        # print(photo[0]["filename"])
        # Ensure username exists and password is correct
        if len(photo) != 1 or not check_password_hash(photo[0]["password"], request.form.get("password")):
            return apology("invalid username and/or password", 403)
        return render_template("/viewed.html", photo = ("static/images/" + photo[0]["filename"]), username=username, filename = photo[0]["filename"])
    else:
        return render_template("/view.html", username=username)

@app.route("/viewed", methods=["GET", "POST"])
@login_required
def viewed():
    if request.method == "POST":
        comment = request.form.get("comment")
        photoid = id
        db.execute("INSERT INTO comments (photoid, comment, username) VALUES (?, ?, ?)", photoid, comment, username)
        return render_template("/viewed.html", photo = ("static/images/" + photo[0]["filename"]), username=username)
    else:
        return render_template("/viewed.html", photo = ("static/images/" + photo[0]["filename"]), username=username)

@app.route("/about")
@login_required
def about():
    return render_template("/about.html", username=username)

@app.route("/")
@login_required
def index():
    # if not request.environ.get('HTTP_X_REAL_IP', request.remote_addr) == ip:
    #     session.clear()
    #     return redirect('/login')
    photoload = db.execute(f"SELECT * FROM photos WHERE username= '{username}'")
    comments = db.execute(f"SELECT * FROM comments")
    return render_template("index.html", photoload=photoload, username=username,comments=comments)

@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        global username
        username = request.form.get("username")
        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        global session_id
        session_id = rows[0]["id"]

        session["user_id"] = session_id
        # global ip
        # ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        # print(ip)
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password was confirmed
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation of password", 403)

        print('x')

        # Insert password into database
        password = request.form.get("password")
        username = request.form.get("username")
        hashval = generate_password_hash(password)

        # Ensure username was submitted
        if not password == request.form.get("confirmation"):
            return apology("must provide username", 403)

        # Insert username into database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashval)
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
