# Project 1
This is a small student project on Flask and SQLAlchemy. It is a books database that retrieves Goodreads average scores for a book and can search through its database. 

# Classes
The app has 3 classes:

*User* class defines all interactions with users: sign-up, sign-in, and also retrieves id from username to add a review. 

*Alert* defines an alert that can have a text and a status (0 stands for a positive, green alert, 1 — a red danger alert)

*Book* handles all interactions with books: finding a book by isbn and getting Goodreads info. 

User.register(), User.signin() and Book.find_isbn() return true if everything is fine and false if something went wrong. Book.get_goodreads(), on the contrary, returns -1 in self.average_rating and reviews_count if Goodreads info is unavailable (connection error or a book isn’t in Goodreads database)

# Functions
All functions beginning with a capital letter only return templates (like Home(), Login(), Register()), and those starting with a small letter do something important like submit() and signin().

# Templates
So the templates for the app are in the Templates folder. They are all based on /layout.html/, which imports Bootstrap CSS and JS and Google Fonts, and introduces the block structure. 

The main page, index.html, inherits layout.html directly while all other pages extend /page_layout.html/, which determines the overall page design with a bulky header and a main card with all necessary information. 

The most complicated page is /book_page.html/, which has more than 3 cards: one with main information about the book, a card with Goodreads information, a card with option to add a review, and a card for each review left by a user. 

Additional CSS is stored in the /‘static’/ folder. 