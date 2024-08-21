from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Author(db.Model):
    __tablename__ = 'author'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    date_of_death = db.Column(db.Date, nullable=True)

    books = db.relationship('Book', back_populates='author', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.name}', birth_date={self.birth_date}, date_of_death={self.date_of_death})>"

    def __str__(self):
        return f"{self.name} (Born: {self.birth_date}, Died: {self.date_of_death if self.date_of_death else 'Still Alive'})"


class Book(db.Model):
    __tablename__ = 'book'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String, unique=True, nullable=False)  
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.String, nullable=False)
    
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)

    author = db.relationship('Author', back_populates='books')

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', author_id={self.author_id})>"

    def __str__(self):
        return f"'{self.title}' by {self.author.name}"
