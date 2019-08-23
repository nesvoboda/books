import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


with open('books.csv') as csvfile:
    reader = csv.reader(csvfile)

    next(reader, None)
    for row in reader:

        print(row[1])
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                   {"isbn": row[0], "title": row[1], "author": row[2],
                    "year": int(row[3])})

    db.commit()

