from mangaNotif import db, app, bcrypt
from flask import request, jsonify, make_response, json
from flask.views import MethodView
import os
import jwt
from datetime import datetime, timedelta
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
                send_mail(email, email_template)
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
        else:
            return make_response(jsonify({"message": "There was some error"})), 400
    elif data.get('email'):
        user = User.query.filter_by(email=data['email'], is_active=True).first()

        if user:
            email_template = forget_password_template(user.activation_token)
            send_mail(data['email'], email_template)
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
        user.username = data['username']
        user.email = data['email']
        user.send_mail_time = datetime.strptime(data['sendMailTime'], '%I:%M%p')

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

        db.session.delete(user)
        db.session.commit()
        response = jsonify({"message": "User deleted"})

        return make_response(response), 200


class MangaView(MethodView):
    def get(self):
        user = is_authenticated(request)
        if user is False:
            return make_response(jsonify({"message": "User is not authenticated"})), 401

        manga_id = request.args.get('mangaId')

        if manga_id:
            manga = Manga.query.filter_by(manga_id=manga_id).first()

            if manga:
                manga_shema = MangaSchema()
                payload = manga_shema.jsonify(manga)
            else:
                manga_info = requests.get(
                    "https://doodle-manga-scraper.p.mashape.com/mangafox.me/manga/" + manga_id + "/",
                    headers={
                        "X-Mashape-Key": "0scVXX9O09msh51PWISWbEzSK0nDp1PU7hkjsn8T3ddvspu36f",
                        "Accept": "text/plain"
                    })
                payload = json.loads(manga_info.content)
                payload['latestChapter'] = payload['chapters'][-1]['chapterId']
                del payload['chapters']
                new_manga = Manga(manga_id=manga_id,
                                  title=payload['name'],
                                  manga_url=payload['href'],
                                  author=json.dumps(payload['author']),
                                  artist=json.dumps(payload['artist']),
                                  status=payload['status'],
                                  year_of_release=payload['yearOfRelease'],
                                  genres=json.dumps(payload['genres']),
                                  info=payload['info'],
                                  cover_art_url=payload['cover'],
                                  latest_chapter=payload['latestChapter'],
                                  last_updated=datetime.strptime(payload['lastUpdate'][:-2], '%Y-%m-%dT%H:%M:%S.%f'))
                db.session.add(new_manga)
                db.session.commit()
                payload = jsonify(payload)

            return make_response(payload), 200
