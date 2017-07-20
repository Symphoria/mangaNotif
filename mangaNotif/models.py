from mangaNotif import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    username = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    send_mail_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    activation_token = db.Column(db.String(64), nullable=True)
    created_on = db.Column(db.DateTime, default=datetime.now())
    last_logged_in = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return self.email


class Manga(db.Model):
    __tablename__ = 'manga'

    id = db.Column(db.Integer, primary_key=True)
    manga_id = db.Column(db.String(240), unique=True)
    title = db.Column(db.String(240), unique=True)
    manga_url = db.Column(db.String(360))
    author = db.Column(db.String(240))
    artist = db.Column(db.String(240))
    status = db.Column(db.String(50))
    year_of_release = db.Column(db.Integer)
    genres = db.Column(db.String(240))
    info = db.Column(db.Text)
    cover_art_url = db.Column(db.String(240))
    latest_chapter = db.Column(db.Float)
    last_updated = db.Column(db.DateTime)

    def __repr__(self):
        return self.title


class UserManga(db.Model):
    __tablename__ = 'user_manga'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'))
    chapter = db.Column(db.Integer)
    bookmarked = db.Column(db.Boolean, default=False)
    in_track_list = db.Column(db.Boolean, default=False)
    send_mail = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='manga')
    manga = db.relationship('Manga', backref='users')
