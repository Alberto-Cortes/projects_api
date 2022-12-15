import jwt
import datetime
import bcrypt
from flask import jsonify
import re
import src.queries as QUERIES

email_regex = re.compile(r"^[^@]+@[^@]+\.[a-zA-Z]{2,}$")

def create_user(connection, salt, secret_key, request):
    data = request.get_json()
    name = data["username"] if "username" in data else None
    email = data["email"] if "email" in data else None
    password = data["password"] if "password" in data else None

    if not all([name, email, password]):
        return jsonify({"message": "Missing parameters", "status": 400})
    if not email_regex.match(email):
        return jsonify({"message": "Invalid email", "status": 400})

    hashed = bcrypt.hashpw(str.encode(password, encoding='utf8'), salt)

    with connection.cursor() as cursor:
        cursor.execute(QUERIES.CREATE_USERS_TABLE)
        cursor.execute(QUERIES.INSERT_USERS, (name, email, hashed.decode()))
        user_id = cursor.fetchone()[0]

        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
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
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
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