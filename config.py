# Define the application directory
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the database - we are working with
# SQLite for this example
SQLALCHEMY_DATABASE_URI = "postgresql://postgres:root@localhost:5432/manga_notif"
SQLALCHEMY_TRACK_MODIFICATIONS = False
DATABASE_CONNECT_OPTIONS = {}

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = os.environ['CSRF_SESSION_KEY']

# Secret key for signing cookies
SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = True

MANGA_PER_PAGE = 15

JOBS = [
    {
        'id': 'scrape_manga_data',
        'func': 'mangaNotif.helper_functions:scrape_manga_data',
        'trigger': 'interval',
        'seconds': 20
    }
]
