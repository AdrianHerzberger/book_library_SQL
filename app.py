from flask import Flask, render_template, flash, request, redirect, url_for
from data_models import db, Author, Book
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()
book_query_ai = os.getenv("OPEN_AI_KEY")
print(f"API Key: {book_query_ai}")


app = Flask(__name__)
app.secret_key = "supersecretkey"

if not os.path.exists("data"):
    os.makedirs("data")

database_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "data", "library.sqlite"
)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"

db.init_app(app)

with app.app_context():
    db.create_all()


def get_book_cover(isbn):
    """Fetch book cover image URL using an external API like Open Library"""
    api_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
    return api_url


def find_book_by_id(book_id):
    book_query = query.filter(Book.id.ilike(f"%{book_id}%"))


@app.route("/", methods=["GET"])
def home():
    if request.method == "GET":
        sort_by_author = request.args.get("sort_by_author")
        sort_by_book = request.args.get("sort_by_book")
        search_by_book_title = request.args.get("search_book_title")

        query = Book.query

    if sort_by_author == "author_id":
        books = Book.query.order_by(Book.author_id).all()
    else:
        books = Book.query.all()

    if sort_by_book == "book_id":
        books = Book.query.all()

    for book in books:
        book.cover_image = get_book_cover(book.isbn)

    if search_by_book_title:
        book_query = query.filter(Book.title.ilike(f"%{search_by_book_title}%"))
        return render_template(
            "search_book.html", book_query=book_query, cover=book.cover_image
        )

    return render_template("home.html", books=books)


@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    if request.method == "POST":
        name = request.form["name"]
        birth_date = request.form["birthdate"]
        date_of_death = (
            request.form["date_of_death"] if request.form["date_of_death"] else None
        )

        birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        if date_of_death:
            date_of_death = datetime.strptime(date_of_death, "%Y-%m-%d").date()

        new_author = Author(
            name=name, birth_date=birth_date, date_of_death=date_of_death
        )
        db.session.add(new_author)
        db.session.commit()

        flash(f"Author {name} added successfully!")

        return redirect(url_for("add_author"))

    return render_template("add_author.html")


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"]
        isbn = request.form["isbn"]
        publication_year = request.form["publication_year"]
        author_id = request.form["author_id"]

        new_book = Book(
            title=title,
            isbn=isbn,
            publication_year=publication_year,
            author_id=author_id,
        )

        db.session.add(new_book)
        db.session.commit()

        flash(f'Book "{title}" added successfully!')

        return redirect(url_for("add_book"))

    authors = Author.query.all()
    return render_template("add_book.html", authors=authors)


@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    if request.method == "POST":
        book = Book.query.get(book_id)

    if book:
        db.session.delete(book)
        db.session.commit()

    return redirect(url_for("home"))


@app.route("/author/<int:author_id>/delete", methods=["POST"])
def delete_author(author_id):
    if request.method == "POST":
        author = Author.query.get(author_id)

        if not author:
            return "Author not founds", 404

        books = Book.query.filter_by(author_id=author_id).all()
        for book in books:
            db.session.delete(book)

        if author:
            db.session.delete(author)
            db.session.commit()

        flash("Author and all their books have been deleted.")
        return redirect(url_for("home"))


@app.route("/book/<int:book_id>/details", methods=["GET"])
def book_details(book_id):
    book = Book.query.get(book_id)

    if not book:
        return "Book not found", 404

    details = {
        "title": book.title,
        "isbn": book.isbn,
        "publication_year": book.publication_year,
        "author": book.author.name,
        "birth_date": book.author.birth_date,
        "death_date": book.author.date_of_death,
    }

    return render_template("book_details.html", book_details=details)


@app.route("/recommend", methods=["GET"])
def recommend():
    books = Book.query.all()

    book_titles = [book.title for book in books]
    books_string = ", ".join(book_titles)

    api_url = "https://api.openai.com/v1/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {book_query_ai}",
    }

    prompt = f"I have read the following books: {books_string}. Can you recommend me another book?"
    data = {"model": "text-davinci-003", "prompt": prompt, "max_tokens": 150}
    response = requests.post(api_url, headers=headers, json=data)

    if response.status_code == 200:
        recommendation = response.json().get("choices", [{}])[0].get("text", "").strip()
    else:
        recommendation = "Sorry, I couldn't fetch a recommendation at the moment."

    return render_template("recommendation.html", recommendation=recommendation)


if __name__ == "__main__":
    app.run(debug=True)
