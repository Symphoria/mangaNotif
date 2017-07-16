from mangaNotif import db, app, bcrypt
from flask import request, jsonify, make_response, url_for
import os
import jwt
from datetime import datetime, timedelta
from models import *
import string
from random import choice
from helper_functions import send_mail


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
                send_mail(email, activation_token)
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
    auth_token = request.headers.get('Authorization-Token')
    if auth_token:
        try:
            auth_token_payload = jwt.decode(auth_token, os.environ["JWT_SECRET"])
            response = jsonify({'message': 'User is already logged in'})

            return make_response(response), 200
        except jwt.ExpiredSignatureError:
            pass

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
