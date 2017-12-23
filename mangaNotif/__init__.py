from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_apscheduler import APScheduler
from flask_cors import CORS
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config.from_object('config')

CORS(app);
db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
scheduler = APScheduler()
scheduler.init_app(app)
admin = Admin(app, template_mode='bootstrap3')

from views import *
from models import *
from urls import *

db.create_all()

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Manga, db.session))
admin.add_view(ModelView(UserManga, db.session))

scheduler.start()