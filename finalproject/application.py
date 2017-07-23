from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
import csv
import urllib.request

from functools import wraps

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///thoughtwall.db")

# from CS50 Finance helpers.py
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Gather necessary information to be displayed on HTML5 Canvas
def displayWall(post_count, posts): 
    
    listofposts = []
    listoftitles = []
    listofnames = []
    listofemails = []
    post_length = []
    
    # Gather necessary information from SQL database.
    for item in posts:
        listofposts.append(item["post"])
        listoftitles.append(item["title"])
        listofnames.append(item["name"])
        listofemails.append(item["email"])
        post_length.append(len(item["post"]))

    # Determine length of canvas page depending on # of posts
    canvas_length = post_count[0]["COUNT(*)"] * 200 + 400
    
    # Renders template to the Canvas.
    return render_template("index.html", post_count=post_count[0]["COUNT(*)"], 
    listofposts = listofposts, listoftitles=listoftitles, listofnames=listofnames, 
    listofemails=listofemails, canvas_length=canvas_length, post_length=post_length)

# for specific walls, filter the query depending on specifics (requested wall)
def partialWallDisplay(walltype):
    
    # Identify which specific group the user belongs to (i.e. Lives in Mather House)
    query = db.execute("SELECT " + walltype + " FROM users WHERE email = :email", 
    email = str(session["email"]))
    
    user_spec = query[0][walltype]
    
    # Gather posts from all users who share that spec
    post_count = db.execute("SELECT COUNT(*) FROM posts WHERE wall = :category AND specifics = :user_spec",
    category = walltype, user_spec = user_spec)
    
    posts = db.execute("SELECT * FROM posts WHERE wall = :category AND specifics = :user_spec", 
    category = walltype, user_spec = user_spec)
    
    # Imports in reverse chronological order, newest to oldest
    posts.reverse()
    
    return displayWall(post_count, posts)

@app.route("/year")
@login_required
def year(): 
    return partialWallDisplay("year")

@app.route("/house")
@login_required
def house(): 
    return partialWallDisplay("house")

@app.route("/concentration")
@login_required
def concentration(): 
    return partialWallDisplay("concentration")
    
@app.route("/")
@login_required
# displays the general wall
def index():
    post_count = db.execute("SELECT COUNT(*) FROM posts WHERE wall = :wall", wall = "general")
    posts = db.execute("SELECT * FROM posts WHERE wall = :wall", wall = "general")
    
    # Switches "posts" to reverse chronological order
    posts.reverse()
    return displayWall(post_count, posts)

@app.route("/login", methods = ["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST 
    if request.method == "POST":
            
        # Requests email input from page. (Intentionally allows for raw email name, without @college)    
        email = request.form.get("email")
        email = email.strip("@college.harvard.edu")

        # ensure username was submitted, otherwise alert and refresh
        if not email:
            flash("Must provide valid email")
            return render_template("login.html")
        
        # ensure password was submitted, otherwise alert and refresh
        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("login.html")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE email = :email", email = email)

        # ensure username doesn't exist or password is incorrect
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["password"]):
            flash("Invalid username and/or password")
            return render_template("login.html")

        # remember which user has logged in, and save specific user info
        session["email"] = rows[0]["email"]
        session["name"] = rows[0]["name"]
        session["user_id"] = session["email"]

        # redirect user to Canvas
        flash("Welcome back!")

        return redirect(url_for("index"))

    # else if user reached route via GET
    else:
        return render_template("login.html")
        
        
@app.route("/post", methods = ["GET", "POST"])
@login_required
def post():
    """Allows user to create a post"""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        title = request.form.get("title")
        post = request.form.get("post")
        wall = request.form.get("wall")
        email = session["email"]
        name = session["name"]
        
        # ensure that post has a title, otherwise alert and refresh page
        if not title: 
            flash("Title required")
            return render_template("post.html")
            
        # ensure title isn't above 15 chars, otherwise alert and refresh page   
        if len(title) > 15: 
            flash("Title must be 15 characters or less in length")
            return render_template("post.html")
        
        # Ensures post isn't above 500 chars
        if len(post) > 500: 
            flash("Post must be 500 characters or less in length")
            return render_template("post.html")

        # If user designates a certain wall, specify it.
        if wall != 'general':
            query = db.execute("SELECT * from users WHERE email = :userid", userid = email)
            spec = query[0][wall]
            db.execute("INSERT INTO posts (email, wall, title, post, name, specifics)"
            + "VALUES (:email, :wall, :title, :post, :name, :specifics)", email = email, 
            wall = wall, title = title, post = post, name = name, specifics = spec)
        
        # otherwise there is no specific field and we can disregard. 
        else: 
            db.execute("INSERT INTO posts (email, wall, title, post, name)"
            + "VALUES (:email, :wall, :title, :post, :name)", email = email, wall = wall, 
            title = title, post = post, name = name)

        # redirect user to designated page
        flash("You made a new post!")
        if wall == 'year':
            return redirect(url_for("year"))
        elif wall == 'house':
            return redirect(url_for("house"))
        elif wall == 'concentration': 
            return redirect(url_for("concentration"))
        else: 
            return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("post.html")        
        

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/register", methods = ["GET", "POST"])
def register():
    """Register user."""
    
    if request.method == "POST": 

        email = request.form.get("email")
        password = request.form.get("password")
        retypedPass = request.form.get("retypedPass")     
        house = request.form.get("house")
        year = request.form.get("year")
        concentration = request.form.get("concentration")
        name = request.form.get("name")        
        
        # ensure all fields are filled
        if not password or not retypedPass or not year or not house or not name or not concentration or not email:
            flash("Please fill in all fields")
            return render_template("register.html")
        
        # Only allows for Harvard emails
        if not email.endswith("@college.harvard.edu"):
            flash("You must use a Harvard College email. Sorry!")
            return render_template("register.html")
        
        email = email.split("@")
        email = email[0] 
        
        # ensure username isn't already used. If it is, alert.
        results = db.execute("SELECT * FROM users WHERE email = :email", email = email)
        if results:
            flash("You already have an account with that email address")
            return render_template("register.html")
            
        # else, if password and retyped don't match
        elif password != retypedPass:
            flash("Passwords must match")
            return render_template("register.html")
        
        # proceed to insert user info into SQL databases
        password = pwd_context.encrypt(password)
        db.execute("INSERT INTO users (email, password, house, year, concentration, name)" 
        + "VALUES (:email, :password, :house, :year, :concentration, :name)", email = email, 
        password = password, house = house, year = year, concentration = concentration, name = name)

        # remember which user has logged in, and save specific user info
        session["email"] = email
        session["name"] = name
        session["user_id"] = email
        
        # redirect user to Canvas
        flash("Welcome!")
        return redirect(url_for("index"))

    else:
        return render_template("register.html")

@app.route("/settings")
@login_required
def settings(): 
    return render_template("settings.html")
    
@app.route("/changeConcentration", methods = ["GET", "POST"])
@login_required
def changeConcentration():
    if request.method == "POST": 
        concentration = request.form.get("concentration")
        # Ensure concentration field is full
        if not concentration: 
            flash("Please select a new concentration")
            return render_template("changeConcentration.html")
        
        # Update SQL database with user's new concentration
        db.execute("UPDATE users SET concentration = :concentration WHERE email = :email", 
        concentration = concentration, email = session["email"])
        flash("You successfully changed your concentration!")
        
        return redirect(url_for("settings"))
    else: 
        return render_template("changeConcentration.html")
    
@app.route("/changeHouse", methods = ["GET", "POST"])
@login_required
def changeHouse():
    if request.method == "POST": 
        house = request.form.get("house")
        
        # Ensure that user filled out house field
        if not house: 
            flash("Please add a house")
            return render_template("changeHouse.html")
            
        # Update SQL database with user's new house info    
        db.execute("UPDATE users SET house = :house WHERE email = :email", house = house, 
        email = session["email"])
        flash("You successfully changed your house!")
        
        return redirect(url_for("settings"))
    else: 
        return render_template("changeHouse.html")
    
@app.route("/changePassword", methods = ["GET", "POST"])
@login_required
def changePassword():
    if request.method == "POST":
        oldPass = request.form.get("oldPass")
        newPass = request.form.get("newPass")
        retypedNew = request.form.get("retypedNew")
        
        # Ensure fields are all filled
        if not oldPass or not newPass or not retypedNew:
            flash("All fields must be filled")
            return render_template("changePassword.html")
            
        # Ensure the inputted passwords match
        elif newPass != retypedNew:
            flash("New passwords don't match")
            return render_template("changePassword.html")
        
        # Ensure user inputted correct old password
        email = str(session["email"])
        storedPass = db.execute("SELECT password FROM users WHERE email = :email", email = email)
        
        if not pwd_context.verify(oldPass, storedPass[0]["password"]): 
            flash("That's an incorrect password.")
            return render_template("changePassword.html")
            
        # Change password in SQL database
        hashedNew = pwd_context.encrypt(newPass)
        db.execute("UPDATE users SET password = :hashedNew WHERE email = :email", 
        hashedNew = hashedNew, email = email)
        flash("Changed password!")
        
        return redirect(url_for("index"))
        
    else:
        
        return render_template("changePassword.html")
        
@app.route("/remove", methods = ["GET", "POST"])
def remove():
    """Log user in."""

    if request.method == "POST":
            
        title = request.form.get("title")
        email = session["email"]
        
        # ensure title is submitted
        if not title:
            flash("Must write post's title")
            return render_template("removePost.html")

        # Query for post. ONLY accept if it is originally from the user
        posts = db.execute("SELECT * FROM posts WHERE title = :title AND email = :email", 
        title = title, email = email)

        # ensure the post exists
        if not posts:
            flash("The post doesn't exist. Remember, title is Caps sensitive and you can"
            + "only delete your own posts")
            return render_template("removePost.html")
            
        # Proceed to remove post from SQL database
        if posts: 
            db.execute("DELETE FROM posts WHERE title = :title AND email = :email", 
            title = title, email = email)
            flash("You successfully removed a post!")

        return redirect(url_for("index"))

    else:
        return render_template("removePost.html")