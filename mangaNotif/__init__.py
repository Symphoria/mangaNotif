from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_apscheduler import APScheduler
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object('config')

CORS(app);
db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
scheduler = APScheduler()
scheduler.init_app(app)

from views import *
from models import *
from urls import *

db.create_all()
