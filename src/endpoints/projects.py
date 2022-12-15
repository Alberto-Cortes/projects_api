import datetime
from flask import jsonify
import jwt
import src.queries as QUERIES
from dotenv import load_dotenv
import os

load_dotenv()

secret_key = os.getenv("SECRET_KEY")

status_options = {0: "Not started", 1: "In progress", 2: "Finished", 3: "Archived"}

def create_project(connection, request):
    data = request.get_json()
    name = data["name"] if "name" in data else None
    description = data["description"] if "description" in data else None
    status = data["status"] if "status" in data else None
    token = data["token"] if "token" in data else None

    try:
        jwt.decode(token, secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired", "status": 401})
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token", "status": 401})

    if not all([name, description, status, token]):
        return jsonify({"message": "Missing parameters", "status": 400})
    if not status in status_options:
        return jsonify({"message": "Invalid status", "status": 400})

    with connection.cursor() as cursor:
        cursor.execute(QUERIES.GET_TOKEN, (token,))
        token = cursor.fetchone()
        user_id = token[2]
        cursor.execute(QUERIES.CREATE_PROJECTS_TABLE)
        cursor.execute(QUERIES.INSERT_PROJECT, (name, description, user_id, status_options[status]))
        project_id = cursor.fetchone()[0]
        connection.commit()

        return jsonify({"project_id": project_id, "status": 200})

def get_projects(connection, request):
    data = request.get_json()
    name = data["name"] if "name" in data else None
    project_id = data["project_id"] if "project_id" in data else None
    user_id = data["user_id"] if "user_id" in data else None
    timestamp = data["timestamp"] if "timestamp" in data else None
    per_page = data["per_page"] if "per_page" in data else None
    offset = data["offset"] if "offset" in data else 0
    token = data["token"] if "token" in data else None

    try:
        jwt.decode(token, secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired", "status": 401})
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token", "status": 401})

    with connection.cursor() as cursor:
        cursor.execute(QUERIES.GET_TOKEN, (token,))
        token = cursor.fetchone()
        
        # Various conditions have to be met so the projects are fethced correctly,
        # Each condition returns a specific message about what went wrong
        if not per_page:
            return jsonify({"message": "Missing 'per_page' parameter", "status": 400})
        elif not token:
            return jsonify({"message": "Invalid token", "status": 401})
        elif not any([name, project_id, user_id, timestamp]):
            return jsonify({"message": "Missing 'name', 'project_id', 'user_id' or 'timestamp' parameter", "status": 400})

        # This dictionary helps to fetch the projects in the correct order with
        # a clean code by iterating over the dictionary of queries
        queries = {name: QUERIES.GET_PROJECTS_BY_NAME, 
                project_id: QUERIES.GET_PROJECTS_BY_PROJECT_ID, 
                user_id: QUERIES.GET_PROJECTS_BY_USER_ID, 
                timestamp: QUERIES.GET_PROJECTS_BY_TIMESTAMP
                }

        for query in queries:
            if query:
                cursor.execute(queries[query], (query, per_page, offset))
                projects = cursor.fetchall()
                res = []

                for project in projects:
                    cursor.execute(QUERIES.GET_UPDATES_BY_PROJECT_ID, (project[0],))
                    updates = cursor.fetchall()
                    update_list = []

                    if updates:
                        for update in updates:
                            # Column names are used to build a dictionary with clear keys
                            # that will be later returned as a JSON
                            update = dict(zip(QUERIES.UPDATES_COLUMN_NAMES, update))
                            update_list.append(update)

                    project = dict(zip(QUERIES.PROJECT_COLUMN_NAMES, project))
                    project["updates"] = update_list
                    res.append(project)

                return jsonify({"projects": res, "status": 200, "offset": offset, "per_page": per_page})

def edit_project(connection, request):
    data = request.get_json()
    project_id = data["project_id"] if "project_id" in data else None
    name = data["name"] if "name" in data else None
    description = data["description"]  if "description" in data else None
    token = data["token"] if "token" in data else None

    # Updates require a project_id, name and description of the update
    update_title = data["update_title"] if "update_title" in data else None
    update_body = data["update_body"] if "update_body" in data else None

    try:
        jwt.decode(token, secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired", "status": 401})
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token", "status": 401})

    with connection.cursor() as cursor:
        cursor.execute(QUERIES.GET_TOKEN, (token,))
        token = cursor.fetchone()

        if not all([update_title, update_body, project_id]):
            return jsonify({"message": "Missing 'update_title', 'update_body' or 'project_id' parameter", "status": 400})


        cursor.execute(QUERIES.GET_PROJECTS_BY_PROJECT_ID, (project_id,))
        project = cursor.fetchone()

        if not project:
            return jsonify({"message": "Project not found", "status": 404})

        # Another important validation is to check if the user is the owner of the project
        if token[2] != project[2]:
            return jsonify({"message": "You are not the owner of this project", "status": 401})

        project_id = project[0]
        name = name if name else project[1]
        description = description if description else project[2]

        cursor.execute(QUERIES.CREATE_UPDATES_TABLE)
        cursor.execute(QUERIES.INSERT_UPDATE, (project_id, update_title, update_body))
        
        cursor.execute(QUERIES.EDIT_PROJECT, (name, description, project_id))
        connection.commit()

        return jsonify({"message": "Project updated", "status": 200})

def delete_project(connection, request):
    data = request.get_json()
    project_id = data["project_id"] if "project_id" in data else None
    token = data["token"] if "token" in data else None

    try:
        jwt.decode(token, secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired", "status": 401})
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token", "status": 401})

    with connection.cursor() as cursor:
        cursor.execute(QUERIES.GET_TOKEN, (token,))
        token = cursor.fetchone()

        cursor.execute(QUERIES.GET_PROJECTS_BY_PROJECT_ID, (project_id,))
        project = cursor.fetchone()

        if token[2] != project[2]:
            return jsonify({"message": "You are not the owner of this project", "status": 401})

        cursor.execute(QUERIES.DELETE_PROJECT, (project_id,))
        connection.commit()

        return jsonify({"message": "Project deleted", "status": 200})