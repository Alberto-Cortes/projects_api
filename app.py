from flask import Flask, request, jsonify
import os
import psycopg2
from dotenv import load_dotenv
import jwt
import datetime
import bcrypt

PROJECT_COLUMN_NAMES = ["project_id", "name", "user_id", "description", "status", "created_at"]
CREATE_PROJECTS_TABLE = """CREATE TABLE IF NOT EXISTS projects (project_id SERIAL PRIMARY KEY, name VARCHAR NOT NULL, user_id INTEGER NOT NULL, description VARCHAR NOT NULL, status VARCHAR NOT NULL DEFAULT 'in progress', created_at TIMESTAMP DEFAULT NOW());"""
INSERT_PROJECT = """INSERT INTO projects (name, description, user_id, status) VALUES (%s, %s, %s, %s) RETURNING project_id;"""
GET_PROJECTS_BY_NAME = """SELECT * FROM projects WHERE name = %s LIMIT %s OFFSET %s;"""
GET_PROJECTS_BY_PROJECT_ID = """SELECT * FROM projects WHERE project_id = %s;"""
GET_PROJECTS_BY_USER_ID = """SELECT * FROM projects WHERE user_id = %s LIMIT %s OFFSET %s;"""
GET_PROJECTS_BY_TIMESTAMP = """SELECT * FROM projects WHERE created_at = %s LIMIT %s OFFSET %s;"""
EDIT_PROJECT = """UPDATE projects SET name = %s, description = %s WHERE project_id = %s;"""
DELETE_PROJECT = """DELETE FROM projects WHERE project_id = %s;"""

UPDATES_COLUMN_NAMES = ["update_id", "project_id", "update_title", "update_body", "created_at"]
CREATE_UPDATES_TABLE = """CREATE TABLE IF NOT EXISTS updates (update_id SERIAL PRIMARY KEY, project_id INTEGER NOT NULL, update_title VARCHAR NOT NULL, update_body VARCHAR NOT NULL, created_at TIMESTAMP DEFAULT NOW());"""
INSERT_UPDATE = """INSERT INTO updates (project_id, update_title, update_body) VALUES (%s, %s, %s) RETURNING update_id;"""
GET_UPDATES_BY_PROJECT_ID = """SELECT * FROM updates WHERE project_id = %s;"""

CREATE_USERS_TABLE = """CREATE TABLE IF NOT EXISTS users (user_id SERIAL PRIMARY KEY, username VARCHAR NOT NULL, email VARCHAR UNIQUE NOT NULL, password VARCHAR NOT NULL, created_at TIMESTAMP DEFAULT NOW());"""
INSERT_USERS = """INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING user_id;"""
GET_USER = """SELECT * FROM users WHERE email = %s;"""

CREATE_TOKENS_TABLE = """CREATE TABLE IF NOT EXISTS tokens (token_id SERIAL PRIMARY KEY, token VARCHAR NOT NULL, user_id INTEGER NOT NULL, created_at TIMESTAMP DEFAULT NOW(), expiration TIMESTAMP DEFAULT NOW() + INTERVAL '1 day');"""
INSERT_TOKEN = """INSERT INTO tokens (token, user_id) VALUES (%s, %s) RETURNING token_id;"""
GET_TOKEN = """SELECT * FROM tokens WHERE token = %s;"""

load_dotenv()

app = Flask(__name__)
url = os.getenv("DATABASE_URL")
secret_key = os.getenv("SECRET_KEY")
salt = str.encode(os.getenv("SALT"))
connection = psycopg2.connect(url)


@app.post("/api/auth/create_user")
def create_user():
    data = request.get_json()
    name = data["username"]
    email = data["email"]
    password = data["password"]
    hashed = bcrypt.hashpw(str.encode(password, encoding='utf8'), salt)

    try:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_USERS_TABLE)
            cursor.execute(INSERT_USERS, (name, email, hashed.decode()))
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
    hashed = bcrypt.hashpw(str.encode(password), salt)

    try:
        with connection.cursor() as cursor:
            cursor.execute(GET_USER, (email,))
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

                cursor.execute(CREATE_TOKENS_TABLE)
                cursor.execute(INSERT_TOKEN, (token, user[0]))
                connection.commit()

                return jsonify({"token": token, "status": 200})
            else:
                return jsonify({"message": "Invalid credentials", "status": 401})
    except:
        return jsonify({"message": "Invalid credentials", "status": 401})
    
@app.post("/api/create_project")
def create_project():
    data = request.get_json()
    name = data["name"]
    description = data["description"]
    status = data["status"]
    token = data["token"]

    try:
        with connection.cursor() as cursor:
            cursor.execute(GET_TOKEN, (token,))
            token = cursor.fetchone()
            user_id = token[2]
            if token and token[4] > datetime.datetime.utcnow():
                cursor.execute(CREATE_PROJECTS_TABLE)
                cursor.execute(INSERT_PROJECT, (name, description, user_id, status))
                project_id = cursor.fetchone()[0]
                connection.commit()

                return jsonify({"project_id": project_id, "status": 200})

            else:
                return jsonify({"message": "Invalid token", "status": 401})
    except:
        return jsonify({"message": "Invalid token", "status ": 401})

@app.get("/api/get_projects")
def get_projects():
    data = request.get_json()
    name = data["name"] if "name" in data else None
    project_id = data["project_id"] if "project_id" in data else None
    user_id = data["user_id"] if "user_id" in data else None
    timestamp = data["timestamp"] if "timestamp" in data else None
    per_page = data["per_page"] if "per_page" in data else None
    offset = data["offset"] if "offset" in data else 0
    token = data["token"] if "token" in data else None

    try:
        with connection.cursor() as cursor:
            cursor.execute(GET_TOKEN, (token,))
            token = cursor.fetchone()
            
            if not per_page:
                return jsonify({"message": "Missing 'per_page' parameter", "status": 400})
            elif not token:
                return jsonify({"message": "Invalid token", "status": 401})
            elif not any([name, project_id, user_id, timestamp]):
                return jsonify({"message": "Missing 'name', 'project_id', 'user_id' or 'timestamp' parameter", "status": 400})
            elif token[4] < datetime.datetime.utcnow():
                return jsonify({"message": "Token expired", "status": 401})

            queries = {name: GET_PROJECTS_BY_NAME, project_id: GET_PROJECTS_BY_PROJECT_ID, user_id: GET_PROJECTS_BY_USER_ID, timestamp: GET_PROJECTS_BY_TIMESTAMP}

            for query in queries:
                if query:
                    cursor.execute(queries[query], (query, per_page, offset))
                    projects = cursor.fetchall()
                    res = []

                    for project in projects:
                        cursor.execute(GET_UPDATES_BY_PROJECT_ID, (project[0],))
                        updates = cursor.fetchall()
                        update_list = []

                        if updates:
                            for update in updates:
                                update = dict(zip(UPDATES_COLUMN_NAMES, update))
                                update_list.append(update)

                        project = dict(zip(PROJECT_COLUMN_NAMES, project))
                        project["updates"] = update_list
                        res.append(project)

                    return jsonify({"projects": res, "status": 200, "offset": offset, "per_page": per_page})
    except:
        return jsonify({"message": "Invalid token", "status ": 401})


@app.put("/api/edit_project")
def edit_project():
    data = request.get_json()
    project_id = data["project_id"] if "project_id" in data else None
    name = data["name"] if "name" in data else None
    description = data["description"]  if "description" in data else None
    token = data["token"] if "token" in data else None

    update_title = data["update_title"] if "update_title" in data else None
    update_body = data["update_body"] if "update_body" in data else None

    try:
        with connection.cursor() as cursor:
            cursor.execute(GET_TOKEN, (token,))
            token = cursor.fetchone()

            if not (token and token[4] > datetime.datetime.utcnow()):
                return jsonify({"message": "Invalid token", "status": 401})

            if not all([update_title, update_body, project_id]):
                return jsonify({"message": "Missing 'update_title', 'update_body' or 'project_id' parameter", "status": 400})

            cursor.execute(GET_PROJECTS_BY_PROJECT_ID, (project_id,))
            project = cursor.fetchone()

            if token[2] != project[2]:
                return jsonify({"message": "You are not the owner of this project", "status": 401})

            project_id = project[0]
            name = name if name else project[1]
            description = description if description else project[2]

            cursor.execute(CREATE_UPDATES_TABLE)
            cursor.execute(INSERT_UPDATE, (project_id, update_title, update_body))
            
            cursor.execute(EDIT_PROJECT, (name, description, project_id))
            connection.commit()

            return jsonify({"message": "Project updated", "status": 200})
    except:
        return jsonify({"message": "Invalid token", "status ": 401})


@app.delete("/api/delete_project")
def delete_project():
    data = request.get_json()
    try:
        project_id = data["project_id"]
        token = data["token"]

        with connection.cursor() as cursor:
            cursor.execute(GET_TOKEN, (token,))
            token = cursor.fetchone()

            cursor.execute(GET_PROJECTS_BY_PROJECT_ID, (project_id,))
            project = cursor.fetchone()

            if not (token and token[4] > datetime.datetime.utcnow()):
                return jsonify({"message": "Invalid token", "status": 401})
            if token[2] != project[2]:
                return jsonify({"message": "You are not the owner of this project", "status": 401})

            cursor.execute(DELETE_PROJECT, (project_id,))
            connection.commit()

            return jsonify({"message": "Project deleted", "status": 200})

    except:
        return jsonify({"message": "Invalid request", "status": 404})

