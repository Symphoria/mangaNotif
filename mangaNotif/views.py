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
    send_mail_time = datetime.strptime(data['sendMailTime'], '%I:%M%p')
    activation_token = ''.join(
        choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(26))

    if data['viaOauth'] is True:
        username = email.split('@')[0]
        new_user = User(username=username, email=email, send_mail_time=send_mail_time, is_active=True,
                        activation_token=activation_token)
    else:
        password_hash = bcrypt.generate_password_hash(data['password'])
        new_user = User(username=data['username'], password=password_hash, send_mail_time=send_mail_time, email=email,
                        activation_token=activation_token)
        send_mail(email, activation_token)

    db.session.add(new_user)
    db.session.commit()

    created_user = User.query.filter(User.email == email).first()
    user_id = created_user.id
    jwt_payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    auth_token = jwt.encode(jwt_payload, os.environ.get('JWT_SECRET'), algorithm='HS256')

    payload = {
        "message": "User created",
        "authToken": auth_token
    }
    response = jsonify(payload)

    return make_response(response), 201


@app.route('/login', methods=['POST'])
def login():
    if 'Authorization_Token' in request.headers:
        auth_token_payload = jwt.decode(request.headers['Authorization_Token'], os.environ["JWT_SECRET"])
        if auth_token_payload['exp'] > datetime.now():
            response = jsonify({'message': 'User is already logged in'})
            return make_response(response), 204
