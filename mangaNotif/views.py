from mangaNotif import db, app, bcrypt
from flask import request, jsonify, make_response, json
from flask.views import MethodView
import os
import jwt
from datetime import timedelta
from models import *
import string
from random import choice
from helper_functions import send_mail
from serializers import *
from email_templates import *
import requests


def is_authenticated(req):
    auth_token = req.headers.get('Authentication-Token')

    if auth_token:
        try:
            auth_token_payload = jwt.decode(auth_token, os.environ["JWT_SECRET"])
            user_id = int(auth_token_payload['user_id'])
            user = User.query.filter_by(id=user_id, is_active=True).first()

            if user:
                return user
            else:
                return False
        except jwt.ExpiredSignatureError:
            return False
    else:
        return False


@app.route('/')
def hello():
    return 'Hoodwink says Hello!'


@app.route('/check-token', methods=['PUT'])
def check_token():
    data = request.get_json()
    auth_token = data['token']

    try:
        auth_token_payload = jwt.decode(auth_token, os.environ["JWT_SECRET"])
        expiration_time = auth_token_payload['exp']
        is_valid = datetime.now() + timedelta(minutes=30) <= datetime.fromtimestamp(expiration_time)
    except jwt.ExpiredSignatureError:
        is_valid = False

    return make_response(jsonify({'isValid': is_valid})), 200


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data['email']
    send_mail_time = datetime.strptime('10:00PM', '%I:%M%p')
    activation_token = ''.join(
        choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(26))

    if User.query.filter_by(email=email).count() == 0:
        if data['viaOauth'] is True:
            username = email.split('@')[0]
            new_user = User(username=username, email=email, send_mail_time=send_mail_time, is_active=True,
                            activation_token=activation_token)
        else:
            if User.query.filter_by(username=data['username']).count() == 0:
                password_hash = bcrypt.generate_password_hash(data['password'])
                new_user = User(username=data['username'], password=password_hash, send_mail_time=send_mail_time,
                                email=email, activation_token=activation_token)
                email_template = confirm_account_template(activation_token)
                send_mail(email, email_template, "Confirm Account")
            else:
                return make_response(jsonify({"message": "Username already exists"})), 400

        db.session.add(new_user)
        db.session.commit()

        payload = {
            "message": "User created"
        }

        if data['viaOauth'] is True:
            created_user = User.query.filter(User.email == email).first()
            user_id = created_user.id
            jwt_payload = {
                "user_id": user_id,
                "exp": datetime.utcnow() + timedelta(days=7)
            }
            auth_token = jwt.encode(jwt_payload, os.environ.get('JWT_SECRET'), algorithm='HS256')
            payload['authToken'] = auth_token

        response = jsonify(payload)

        return make_response(response), 201
    else:
        response = jsonify({"message": "Another user exists with same email"})

        return make_response(response), 400


@app.route('/confirm', methods=['PUT'])
def confirm():
    activation_token = request.args.get('q')
    user = User.query.filter(User.activation_token == activation_token).first()

    if user:
        user.is_active = True
        db.session.commit()
        response = jsonify({"message": "Account activated"})

        return make_response(response), 200
    else:
        response = jsonify({"message": "User not found"})

        return make_response(response), 400


@app.route('/login', methods=['POST'])
def login():
    user = is_authenticated(request)
    if user:
        return make_response(jsonify({'message': 'User is already logged in'})), 200

    data = request.get_json()
    username_or_email = data['usernameOrEmail']
    user = None

    if data['viaOauth'] is True:
        user = User.query.filter(User.email == username_or_email, User.is_active == True).first()
    else:
        check_user = User.query.filter((User.email == username_or_email) | (User.username == username_or_email),
                                       User.is_active == True).first()

        if check_user and bcrypt.check_password_hash(check_user.password, data['password']):
            user = check_user

    if user is not None:
        user_id = user.id
        jwt_payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        auth_token = jwt.encode(jwt_payload, os.environ.get('JWT_SECRET'), algorithm='HS256')
        user.last_logged_in = datetime.now()
        db.session.commit()
        payload = {
            "authToken": auth_token
        }

        return make_response(jsonify(payload)), 200
    else:
        return make_response(jsonify({"message": "User does not exist"})), 404


@app.route('/forget-password', methods=['PUT'])
def forget_password():
    activation_token = request.headers.get('Activation-Token')
    data = request.get_json()

    if activation_token:
        user = User.query.filter_by(activation_token=activation_token, is_active=True).first()

        if user:
            new_password_hash = bcrypt.generate_password_hash(data['newPassword'])
            user.password = new_password_hash
            db.session.commit()

            return make_response(jsonify({"message": "Your password has been changed"})), 200
        else:
            return make_response(jsonify({"message": "There was some error"})), 400
    elif data.get('email'):
        user = User.query.filter_by(email=data['email'], is_active=True).first()

        if user:
            email_template = forget_password_template(user.activation_token)
            send_mail(data['email'], email_template, "Forgot Password?")

            return make_response(jsonify({"message": "An email has been sent to help you change your password. Please check your inbox"})), 200
        else:
            return make_response(jsonify({"message": "There is no user registered with the entered email address"})), 400
    else:
        return make_response(jsonify({"message": "There was something wrong"})), 400


class UserView(MethodView):
    def get(self):
        user = is_authenticated(request)
        if user is False:
            return make_response(jsonify({"message": "User is not authenticated"})), 401

        user_schema = UserSchema()
        payload = user_schema.jsonify(user)

        return make_response(payload), 200

    def put(self):
        user = is_authenticated(request)
        if user is False:
            return make_response(jsonify({"message": "User is not authenticated"})), 401

        data = request.get_json()
        check_user_username = User.query.filter(User.username == data['username'], User.id != user.id).first()
        check_user_email = User.query.filter(User.email == data['email'], User.id != user.id).first()

        if check_user_username:
            return make_response(jsonify({"message": "Username already exists"})), 400

        if check_user_email:
            return make_response(jsonify({"message": "Email is already taken"})), 400

        user.username = data['username']
        user.email = data['email']
        # user.send_mail_time = datetime.strptime(data['sendMailTime'], '%I:%M%p')

        if data['changePassword'] is True:
            if bcrypt.check_password_hash(user.password, data['oldPassword']):
                new_password_hash = bcrypt.generate_password_hash(data['newPassword'])
                user.password = new_password_hash
            else:
                return make_response(jsonify({"message": "Entered password is incorrect"})), 403

        db.session.commit()
        response = jsonify({"message": "User details updated"})

        return make_response(response), 200

    def delete(self):
        user = is_authenticated(request)
        if user is False:
            return make_response(jsonify({"message": "User is not authenticated"})), 401

        UserManga.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        response = jsonify({"message": "User deleted"})

        return make_response(response), 200


class MangaView(MethodView):
    def get(self):
        user = is_authenticated(request)
        manga_id = request.args.get('mangaId')

        if manga_id:
            manga = Manga.query.filter_by(manga_id=manga_id).first()
            manga_shema = MangaSchema()

            if manga:
                result = manga_shema.dump(manga)
            else:
                manga_info = requests.get(
                    "https://doodle-manga-scraper.p.mashape.com/mangareader.net/manga/" + manga_id + "/",
                    headers={
                        "X-Mashape-Key": "0scVXX9O09msh51PWISWbEzSK0nDp1PU7hkjsn8T3ddvspu36f",
                        "Accept": "text/plain"
                    })
                payload = json.loads(manga_info.content)
                payload['latestChapter'] = payload['chapters'][-1]['chapterId']
                del payload['chapters']
                cover_url = payload.get('cover', "http://www.makeupgeek.com/content/wp-content/themes/makeup-geek/images/placeholder-square.svg")
                cover_url = cover_url[:4] + "s" + cover_url[4:]
                new_manga = Manga(manga_id=manga_id,
                                  title=payload['name'],
                                  manga_url="http://www.mangareader.net/" + payload['href'],
                                  author=json.dumps(payload['author']),
                                  artist=json.dumps(payload['artist']),
                                  status=payload['status'],
                                  year_of_release=payload.get('yearOfRelease', 0),
                                  genres=json.dumps(payload['genres']),
                                  info=payload.get('info', 'Sorry, currently info about this manga is not available'),
                                  cover_art_url=cover_url,
                                  latest_chapter=payload['latestChapter'],
                                  last_updated=datetime.strptime(payload['lastUpdate'][:-2], '%Y-%m-%dT%H:%M:%S.%f'))
                db.session.add(new_manga)
                db.session.commit()
                manga = new_manga
                result = manga_shema.dump(new_manga)
            
            if user:
                track_listed_manga = UserManga.query.filter_by(user_id=user.id, manga_id=manga.id,
                                                           in_track_list=True).first()

                if track_listed_manga:
                    result.data['inTrackList'] = True
                else:
                    result.data['inTrackList'] = False
            else:
                result.data['inTrackList'] = False

            payload = jsonify(result.data)

            return make_response(payload), 200
        else:
            return make_response(jsonify({"message": "Manga is not specified"})), 400


class TrackListView(MethodView):
    def post(self):
        user = is_authenticated(request)
        if user is False:
            return make_response(jsonify({"message": "User is not authenticated"})), 401

        data = request.get_json()
        manga = Manga.query.filter_by(manga_id=data['mangaId']).first()

        if manga:
            user_manga = UserManga.query.filter_by(user_id=user.id, manga_id=manga.id).scalar()

            if user_manga:
                if user_manga.in_track_list is False:
                    user_manga.in_track_list = True
                    response = jsonify({"message": "Manga added to track list"})
                else:
                    response = jsonify({"message": "Manga is already in your track list"})
            else:
                user_manga_obj = UserManga(user_id=user.id, manga_id=manga.id, in_track_list=True)
                db.session.add(user_manga_obj)
                response = jsonify({"message": "Manga added to track list"})

            db.session.commit()

            return make_response(response), 200
        else:
            return make_response(jsonify({"message": "Manga not found"})), 404

    def get(self):
        user = is_authenticated(request)
        if user is False:
            return make_response(jsonify({"message": "User is not authenticated"})), 401

        page = request.args.get('page', 1)
        manga_id_list = db.session.query(UserManga.manga_id).filter_by(user_id=user.id, in_track_list=True).paginate(
            int(page), app.config['MANGA_PER_PAGE'], error_out=False)

        if len(manga_id_list.items) > 0:
            track_listed_manga = Manga.query.filter(Manga.id.in_(manga_id_list.items))
            manga_schema = MangaSchema(many=True)
            result = manga_schema.dump(track_listed_manga)

            for manga in result.data:
                manga['inTrackList'] = True

            payload = {
                'totalPages': manga_id_list.pages,
                'hasNext': manga_id_list.has_next,
                'hasPrevious': manga_id_list.has_prev,
                'mangaData': result.data
            }

            return make_response(jsonify(payload)), 200
        else:
            return make_response(jsonify({"message": "There are no manga in your track list"})), 404

    def delete(self):
        user = is_authenticated(request)
        if user is False:
            return make_response(jsonify({"message": "User is not authenticated"})), 401

        data = request.get_json()
        manga = Manga.query.filter_by(manga_id=data['mangaId']).first()

        if manga:
            user_manga_obj = UserManga.query.filter_by(user_id=user.id, manga_id=manga.id, in_track_list=True).first()

            if user_manga_obj:
                if user_manga_obj.bookmarked is True:
                    user_manga_obj.in_track_list = False
                else:
                    db.session.delete(user_manga_obj)

                db.session.commit()
                response = jsonify({"message": "Manga removed from track list"})

                return make_response(response), 200

        return make_response(jsonify({"message": "Manga not found"})), 404


class BookmarkView(MethodView):
    def post(self):
        user = is_authenticated(request)
        if user is False:
            return make_response(jsonify({"message": "User is not authenticated"})), 401

        data = request.get_json()
        manga = Manga.query.filter_by(manga_id=data['mangaId']).scalar()

        if manga:
            user_manga = UserManga.query.filter_by(user_id=user.id, manga_id=manga.id).scalar()

            if user_manga:
                user_manga.bookmarked = True
                user_manga.chapter = data['chapter']
            else:
                user_manga_obj = UserManga(user_id=user.id, manga_id=manga.id, bookmarked=True, chapter=data['chapter'])
                db.session.add(user_manga_obj)

            db.session.commit()
            response = jsonify({"message": "Bookmark added"})

            return make_response(response), 200
        else:
            return make_response(jsonify({"message": "Manga not found"})), 404

    def get(self):
        user = is_authenticated(request)
        if user is False:
            return make_response(jsonify({"message": "User is not authenticated"})), 401

        page = request.args.get('page', 1)
        user_manga_list = UserManga.query.filter_by(user_id=user.id, bookmarked=True).paginate(int(page), app.config[
            'MANGA_PER_PAGE'], error_out=False)

        if len(user_manga_list.items) > 0:
            manga_schema = MangaSchema()
            payload = {
                'totalPages': user_manga_list.pages,
                'hasNext': user_manga_list.has_next,
                'hasPrevious': user_manga_list.has_prev,
                'mangaData': []
            }

            for user_manga in user_manga_list.items:
                manga = Manga.query.filter_by(id=user_manga.manga_id).first()
                result = manga_schema.dump(manga)
                result.data['chapter'] = user_manga.chapter
                payload['mangaData'].append(result.data)

            return make_response(jsonify(payload)), 200
        else:
            return make_response(jsonify({"message": "No manga bookmarked yet"})), 404

    def delete(self):
        user = is_authenticated(request)
        if user is False:
            return make_response(jsonify({"message": "User is not authenticated"})), 401

        data = request.get_json()
        manga = Manga.query.filter_by(manga_id=data['mangaId']).first()

        if manga:
            user_manga = UserManga.query.filter_by(user_id=user.id, manga_id=manga.id, bookmarked=True).first()

            if user_manga:
                if user_manga.in_track_list is True:
                    user_manga.bookmarked = False
                else:
                    db.session.delete(user_manga)

                db.session.commit()
                response = jsonify({"message": "Manga removes from bookmarks"})

                return make_response(response), 200

        return make_response(jsonify({"message": "Manga not found"})), 404
