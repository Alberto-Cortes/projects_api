import jwt
import datetime
import bcrypt
from flask import jsonify

import src.queries as QUERIES

def create_user(connection, salt, secret_key, request):
    data = request.get_json()
    name = data["username"]
    email = data["email"]
    password = data["password"]
    hashed = bcrypt.hashpw(str.encode(password, encoding='utf8'), salt)

    with connection.cursor() as cursor:
        cursor.execute(QUERIES.CREATE_USERS_TABLE)
        cursor.execute(QUERIES.INSERT_USERS, (name, email, hashed.decode()))
        user_id = cursor.fetchone()[0]

        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=5),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        token = jwt.encode(
            payload,
            secret_key,
            algorithm='HS256'
        )

        cursor.execute(QUERIES.CREATE_TOKENS_TABLE)
        cursor.execute(QUERIES.INSERT_TOKEN, (token, user_id))
        connection.commit()
    return jsonify({"token": token, "status": 200})

def login(connection, salt, secret_key, request):
    data = request.get_json()
    email = data["email"]
    password = data["password"]
    hashed = bcrypt.hashpw(str.encode(password), salt)

    with connection.cursor() as cursor:
        cursor.execute(QUERIES.GET_USER, (email,))
        user = cursor.fetchone()
        if hashed.decode() == user[3]:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=5),
                'iat': datetime.datetime.utcnow(),
                'sub': user[1]
            }
            token = jwt.encode(
                payload,
                secret_key,
                algorithm='HS256'
            )

            cursor.execute(QUERIES.CREATE_TOKENS_TABLE)
            cursor.execute(QUERIES.SINSERT_TOKEN, (token, user[0]))
            connection.commit()

            return jsonify({"token": token, "status": 200})
        else:
            return jsonify({"message": "Invalid credentials", "status": 401})