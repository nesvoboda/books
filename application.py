import os

from flask import (Flask, session, request, render_template, redirect,
                   url_for, jsonify, abort)
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import requests

from passlib.hash import pbkdf2_sha256

hash = pbkdf2_sha256.hash("toomanysecrets")

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


class Alert:
    def __init__(self, text, status):
        self.text = text
        self.status = status


class Book:
    def __init__(self, isbn=None, title=None, author=None, year=None):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.year = year
        self.average_rating = None
        self.reviews_count = None
        self.reviews = []

    def find_isbn(self, isbn):

        self.isbn = isbn

        match = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                           {"isbn": isbn}).first()

        if match is None:
            return False

        else:

            self.title = match["title"]
            self.author = match["author"]
            self.year = match["year"]
            return True

    def get_goodreads(self):

        try:
            res = requests.get(
                "https://www.goodreads.com/book/review_counts.json",
                params={"key": "cowabunga",
                        "isbns": self.isbn})

        except requests.exceptions.ConnectionError:
            return -1, -1
        if res.status_code == 200:
            a = res.json()
            self.average_rating = a['books'][0]['average_rating']
            self.reviews_count = a['books'][0]['reviews_count']

        else:

            self.average_rating = -1
            self.reviews_count = -1

    def get_reviews(self):

        self.reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": self.isbn}).fetchall()

    def add_review(self, review_text, rating, user_id):

        db.execute(
            "INSERT INTO reviews (user_id, rating, review_text, isbn) VALUES (:user_id, :rating, :review_text, :isbn)",
            {"user_id": user_id, "rating": rating, "review_text": review_text,
             "isbn": self.isbn})
        db.commit()


class User:

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.id = None

    def register(self):

        match = db.execute("SELECT * FROM users WHERE username = :username",
                           {"username": self.username}).first()

        if match is None:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)",
                {"username": self.username,
                 "password_hash": pbkdf2_sha256.hash(self.password)})
            db.commit()
            return True

        else:
            return False

    def signin(self):

        match = db.execute("SELECT * FROM users WHERE username = :username",
                           {"username": self.username}).first()
        if match is not None:
            if pbkdf2_sha256.verify(self.password, match['password_hash']):
                return True
        return False

    def get_id(self):

        match = db.execute("SELECT * FROM users WHERE username = :username",
                           {"username": self.username}).first()
        self.id = match["id"]


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


nav = ['Home', 'Register', 'Login', 'Search']


@app.route("/")
def Home():
    if 'username' in session:
        return redirect(url_for('Search'))
    else:
        return render_template("index.html", title="Home")


@app.route("/register")
def Register():
    return render_template("register.html", title="Register")


@app.route("/login")
def Login():
    if 'username' in session:
        return redirect(url_for('Search'))
    else:
        return render_template("login.html", title="Login")


@app.route("/search")
def Search():
    if 'username' in session:
        return render_template("search.html", title="Search")
    else:
        return redirect(url_for('Login'))


@app.route("/submit", methods=["POST"])
def submit():
    username = request.form.get("username")
    password = request.form.get("password")

    new_user = User(username, password)
    if new_user.register():

        text = f'Welcome, {username}! You can now log in with your username and password.'

        return render_template("register.html", title="Register",
                               alert=Alert(status=0, text=text))

    else:

        text = 'This username seems to be already taken. Please try another one.'

        return render_template("register.html", title="Register",
                               alert=Alert(status=1, text=text))


@app.route("/signin", methods=["POST"])
def signin():

    username = request.form.get("username")
    password = request.form.get("password")

    new_user = User(username, password)
    if new_user.signin():
        session['username'] = new_user.username
        return redirect(url_for('Search'))
    else:
        return render_template("login.html", title="Login",
                               alert=Alert(text="Entered credentials seem to be incorrect", status=1))


@app.route("/search_results", methods=["GET"])
def search_results():

    isbn = request.args.get('isbn', '')
    author = request.args.get('author', '')
    title = request.args.get('title', '')

    if isbn is not "":
        isbn = f'%{isbn}%'
    if author is not "":
        author = f'%{author}%'
    if title is not "":
        title = f'%{title}%'

    match = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn OR author LIKE :author OR title LIKE :title", {"isbn": isbn, "author": author, "title": title})

    results = match.fetchall()

    if len(results) == 0:
        return render_template("search.html", title="Search results", alert=Alert(text="Sorry, there seems to be no such book in our database.", status=1))

    else:
        return render_template("search_results.html", title="Search results", results = results)

@app.route("/book_page/<string:isbn>")
def book_page(isbn):

    bk = Book()

    bk.find_isbn(isbn)
    bk.get_goodreads()
    bk.get_reviews()

    current_user = User(session["username"])
    current_user.get_id()

    review_added = False

    for review in bk.reviews:
        if review[0] == current_user.id:
            review_added = True

    return render_template("book_page.html", title="Book page", book=bk, review_added=review_added)

@app.route("/api/<string:isbn>")
def api(isbn):

    bk = Book()

    if bk.find_isbn(isbn):

        bk.get_goodreads()

        result = {
            'title': bk.title,
            'author': bk.author,
            'year': bk.year,
            'isbn': bk.isbn,
            'review_count': bk.reviews_count,
            'average_rating': bk.average_rating
                }

        return jsonify(result)

    else:

        abort(404)

@app.route("/add_review/<string:isbn>", methods=["POST"])
def add_review(isbn):
    rating = request.form.get("rating")
    review_text = request.form.get("review_text")

    bk = Book()
    bk.find_isbn(isbn)

    current_user=User(session["username"])
    current_user.get_id()

    bk.add_review(review_text, rating, current_user.id)
    
    return redirect(url_for('book_page', isbn = isbn))

@app.route("/logout")
def logout():
    if 'username' in session:
        session.pop('username', None)
        return redirect(url_for('Home'))
    else:
        return redirect(url_for('Home'))

