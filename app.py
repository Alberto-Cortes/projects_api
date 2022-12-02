from flask import Flask, request, jsonify
import os
import psycopg2
from dotenv import load_dotenv
import jwt
import datetime

CREATE_PROJECTS_TABLE = """CREATE TABLE IF NOT EXISTS projects (id SERIAL PRIMARY KEY, name VARCHAR NOT NULL, owner VARCHAR NOT NULL, description VARCHAR NOT NULL, created_at TIMESTAMP DEFAULT NOW());"""
INSERT_PROJECT = """INSERT INTO projects (name, description, owner) VALUES (%s, %s, %s) RETURNING id;"""
GET_PROJECTS_BY_NAME = """SELECT * FROM projects WHERE name = %s;"""
GET_PROJECTS_BY_ID = """SELECT * FROM projects WHERE id = %s;"""
GET_PROJECTS_BY_OWNER = """SELECT * FROM projects WHERE owner = %s;"""
GET_PROJECTS_BY_TIMESTAMP = """SELECT * FROM projects WHERE created_at = %s;"""
EDIT_PROJECT = """UPDATE projects SET name = %s, description = %s, owner = %s WHERE id = %s;"""
DELETE_PROJECT = """DELETE FROM projects WHERE id = %s;"""

CREATE_USERS_TABLE = """CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name VARCHAR NOT NULL, email VARCHAR NOT NULL UNIQUE, password VARCHAR NOT NULL, created_at TIMESTAMP DEFAULT NOW());"""
INSERT_USERS = """INSERT INTO users (name, email, password) VALUES (%s, %s, %s) RETURNING id;"""
GET_USER = """SELECT * FROM users WHERE email = %s;"""

CREATE_TOKENS_TABLE = """CREATE TABLE IF NOT EXISTS tokens (id SERIAL PRIMARY KEY, token VARCHAR NOT NULL UNIQUE, created_at TIMESTAMP DEFAULT NOW()), expiration TIMESTAMP DEFAULT NOW() + interval '1 day';"""
INSERT_TOKEN = """INSERT INTO tokens (token) VALUES (%s) RETURNING id;"""
GET_TOKEN = """SELECT * FROM tokens WHERE token = %s;"""

load_dotenv()

app = Flask(__name__)
url = os.getenv("DATABASE_URL")
secret_key = os.getenv("SECRET_KEY")
connection = psycopg2.connect(url)

@app.post("/api/auth/create_user")
def create_user():
    data = request.get_json()
    name = data["name"]
    email = data["email"]
    password =data["password"]
    with connection.cursor() as cursor:
        cursor.execute(CREATE_USERS_TABLE)
        cursor.execute(INSERT_USERS, (name, email, password))
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

        cursor.execute(CREATE_TOKENS_TABLE)
        cursor.execute(INSERT_TOKEN, (token,))
        connection.commit()

    return jsonify({"token": token, "status": 200})


@app.post("/api/auth/login")
def login():
    data = request.get_json()
    email = data["email"]
    password = data["password"]
    with connection.cursor() as cursor:
        cursor.execute(GET_USER, (email,))
        user = cursor.fetchone()
        if user[3] == password:
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

            cursor.execute(CREATE_TOKENS_TABLE)
            cursor.execute(INSERT_TOKEN, (token,))
            connection.commit()

            return jsonify({"token": token, "status": 200})
        else:
            return jsonify({"message": "Invalid credentials", "status": 401})
    
@app.post("/api/create_project")
def create_project():
    data = request.get_json()
    name = data["name"]
    description = data["description"]
    token = data["token"]
    with connection.cursor() as cursor:
        try:
            cursor.execute(GET_TOKEN, (token,))
            token = cursor.fetchone()
            owner = token[1]
            if token:
                cursor.execute(CREATE_PROJECTS_TABLE)
                cursor.execute(INSERT_PROJECT, (name, description, owner))
                project_id = cursor.fetchone()[0]
                connection.commit()

                return jsonify({"id": project_id, "status": 200})
        
        except:
            return jsonify({"message": "Invalid token", "status": 401})

@app.get("/api/get_projects")
def get_projects():
    data = request.get_json()
    try:
        name = data["name"] if "name" in data else None
        id = data["id"] if "id" in data else None
        owner = data["owner"] if "owner" in data else None
        timestamp = data["timestamp"] if "timestamp" in data else None
        token = data["token"] if "token" in data else None

        cursor.execute(GET_TOKEN, (token,))
        token = cursor.fetchone()

        if token and any([name, id, owner, timestamp]):
            with connection.cursor() as cursor:
                if name:
                    cursor.execute(GET_PROJECTS_BY_NAME, (name,))
                    projects = cursor.fetchall()
                    return jsonify({"projects": projects, "status": 200})
                elif id:
                    cursor.execute(GET_PROJECTS_BY_ID, (id,))
                    projects = cursor.fetchall()
                    return jsonify({"projects": projects, "status": 200})
                elif owner:
                    cursor.execute(GET_PROJECTS_BY_OWNER, (owner,))
                    projects = cursor.fetchall()
                    return jsonify({"projects": projects, "status": 200})
                elif timestamp:
                    cursor.execute(GET_PROJECTS_BY_TIMESTAMP, (timestamp,))
                    projects = cursor.fetchall()
                    return jsonify({"projects": projects, "status": 200})
        else:
            return jsonify({"message": "Empty request, please provide data for lookup", "status": 404})
            
    except:
        return jsonify({"message": "Invalid token", "status": 401})
        
@app.get("/api/edit_project")
def edit_project():
    data = request.get_json()
    try:
        id = data["id"]
        name = data["name"]
        description = data["description"]
        owner = data["owner"]
        token = data["token"]

        cursor.execute(GET_TOKEN, (token,))
        token = cursor.fetchone()

        if token:
            with connection.cursor() as cursor:
                cursor.execute(EDIT_PROJECT, (name, description, owner, id))
                connection.commit()
                return jsonify({"message": "Project updated", "status": 200})
        else:
            return jsonify({"message": "Invalid token", "status": 401})
    except:
        return jsonify({"message": "Invalid request", "status": 404})


@app.get("/api/delete_project")
def delete_project():
    data = request.get_json()
    try:
        id = data["id"]
        token = data["token"]

        cursor.execute(GET_TOKEN, (token,))
        token = cursor.fetchone()

        if token:
            with connection.cursor() as cursor:
                cursor.execute(DELETE_PROJECT, (id,))
                connection.commit()
                return jsonify({"message": "Project deleted", "status": 200})
        else:
            return jsonify({"message": "Invalid token", "status": 401})
    except:
        return jsonify({"message": "Invalid request", "status": 404})

