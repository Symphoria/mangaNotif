from mangaNotif import db


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    username = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    send_mail_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    activation_token = db.Column(db.String(64))


class Manga(db.Model):
    __tablename__ = 'manga'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(240), unique=True)
    manga_url = db.Column(db.String(360))
    author = db.Column(db.String(240))
    artist = db.Column(db.String(240))
    status = db.Column(db.String(50))
    year_of_release = db.Column(db.String(10))
    genres = db.Column(db.String(240))
    info = db.Column(db.Text)
    cover_art_url = db.Column(db.String(240))
    latest_chapter = db.Column(db.Integer)


class UserManga(db.Model):
    __tablename__ = 'user_manga'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'))
    chapter = db.Column(db.Integer)
    bookmarked = db.Column(db.Boolean, default=False)
    in_track_list = db.Column(db.Boolean, default=False)
    send_mail = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='manga', lazy='dynamic')
    manga = db.relationship('Manga', backref='users', lazy='dynamic')
