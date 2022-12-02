from flask import Flask, request, jsonify
import os
import psycopg2
from dotenv import load_dotenv
import jwt
import datetime

CREATE_PROJECTS_TABLE = """CREATE TABLE IF NOT EXISTS projects (id SERIAL PRIMARY KEY, name VARCHAR NOT NULL, user_id INTEGER NOT NULL, description VARCHAR NOT NULL, created_at TIMESTAMP DEFAULT NOW());"""
INSERT_PROJECT = """INSERT INTO projects (name, description, user_id) VALUES (%s, %s, %s) RETURNING id;"""
GET_PROJECTS_BY_NAME = """SELECT * FROM projects WHERE name = %s;"""
GET_PROJECTS_BY_PROJECT_ID = """SELECT * FROM projects WHERE id = %s;"""
GET_PROJECTS_BY_USER_ID = """SELECT * FROM projects WHERE user_id = %s;"""
GET_PROJECTS_BY_TIMESTAMP = """SELECT * FROM projects WHERE created_at = %s;"""
EDIT_PROJECT = """UPDATE projects SET name = %s, description = %s WHERE id = %s;"""
DELETE_PROJECT = """DELETE FROM projects WHERE id = %s;"""

CREATE_USERS_TABLE = """CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR NOT NULL, email VARCHAR UNIQUE NOT NULL, password VARCHAR NOT NULL, created_at TIMESTAMP DEFAULT NOW());"""
INSERT_USERS = """INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id;"""
GET_USER = """SELECT * FROM users WHERE email = %s;"""

CREATE_TOKENS_TABLE = """CREATE TABLE IF NOT EXISTS tokens (id SERIAL PRIMARY KEY, token VARCHAR NOT NULL, user_id INTEGER NOT NULL, created_at TIMESTAMP DEFAULT NOW(), expiration TIMESTAMP DEFAULT NOW() + INTERVAL '1 day');"""
INSERT_TOKEN = """INSERT INTO tokens (token, user_id) VALUES (%s, %s) RETURNING id;"""
GET_TOKEN = """SELECT * FROM tokens WHERE token = %s;"""

load_dotenv()

app = Flask(__name__)
url = os.getenv("DATABASE_URL")
secret_key = os.getenv("SECRET_KEY")
connection = psycopg2.connect(url)

@app.post("/api/auth/create_user")
def create_user():
    data = request.get_json()
    name = data["username"]
    email = data["email"]
    password = data["password"]
    try:
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
            cursor.execute(INSERT_TOKEN, (token, user_id))
            connection.commit()
    except:
        return jsonify({"error": "User already exists", "status": 400})
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
            cursor.execute(INSERT_TOKEN, (token, user[0]))
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
            user_id = token[2]
            if token and token[4] > datetime.datetime.utcnow():
                cursor.execute(CREATE_PROJECTS_TABLE)
                cursor.execute(INSERT_PROJECT, (name, description, user_id))
                project_id = cursor.fetchone()[0]
                connection.commit()

                return jsonify({"id": project_id, "status": 200})

            else:
                return jsonify({"message": "Invalid token", "status": 401})
            
        except:
            return jsonify({"message": "Invalid token", "status": 401})

@app.get("/api/get_projects")
def get_projects():
    data = request.get_json()
    name = data["name"] if "name" in data else None
    id = data["id"] if "id" in data else None
    user_id = data["user_id"] if "user_id" in data else None
    timestamp = data["timestamp"] if "timestamp" in data else None
    token = data["token"] if "token" in data else None

    try:
        with connection.cursor() as cursor:
            cursor.execute(GET_TOKEN, (token,))
            token = cursor.fetchone()

            if token and any([name, id, user_id, timestamp]) and token[4] > datetime.datetime.utcnow():
                if name:
                    cursor.execute(GET_PROJECTS_BY_NAME, (name,))
                    projects = cursor.fetchall()
                    return jsonify({"projects": projects, "status": 200})
                elif id:
                    cursor.execute(GET_PROJECTS_BY_PROJECT_ID, (id,))
                    projects = cursor.fetchall()
                    return jsonify({"projects": projects, "status": 200})
                elif user_id:
                    cursor.execute(GET_PROJECTS_BY_USER_ID, (user_id,))
                    projects = cursor.fetchall()
                    return jsonify({"projects": projects, "status": 200})
                elif timestamp:
                    cursor.execute(GET_PROJECTS_BY_TIMESTAMP, (timestamp,))
                    projects = cursor.fetchall()
                    return jsonify({"projects": projects, "status": 200})
            else:
                return jsonify({"message": "Empty request, please provide data for lookup", "status": 404})
    except:
        return jsonify({"message": "Invalid token", "status ": 401})
    
@app.put("/api/edit_project")
def edit_project():
    data = request.get_json()
    id = data["id"] if "id" in data else None
    name = data["name"] if "name" in data else None
    description = data["description"]  if "description" in data else None
    token = data["token"] if "token" in data else None

    try:
        with connection.cursor() as cursor:
            cursor.execute(GET_TOKEN, (token,))
            token = cursor.fetchone()

            if token and token[4] > datetime.datetime.utcnow():
                cursor.execute(GET_PROJECTS_BY_PROJECT_ID, (id,))
                project = cursor.fetchone()

                id = project[0]
                name = name if name else project[1]
                description = description if description else project[2]
                
                cursor.execute(EDIT_PROJECT, (name, description, id))
                connection.commit()
                return jsonify({"message": "Project updated", "status": 200})
            else:
                return jsonify({"message": "Invalid token", "status": 401})
    except:
        return jsonify({"message": "Invalid token", "status": 401})

@app.delete("/api/delete_project")
def delete_project():
    data = request.get_json()
    try:
        id = data["id"]
        token = data["token"]

        with connection.cursor() as cursor:
            cursor.execute(GET_TOKEN, (token,))
            token = cursor.fetchone()

            if token and token[4] > datetime.datetime.utcnow():
                cursor.execute(DELETE_PROJECT, (id,))
                connection.commit()
                return jsonify({"message": "Project deleted", "status": 200})
            else:
                return jsonify({"message": "Invalid token", "status": 401})
    except:
        return jsonify({"message": "Invalid request", "status": 404})

