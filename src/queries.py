# The following lines describe the table `projects` and the queries used to interact with the db through postgresql
PROJECT_COLUMN_NAMES = ["project_id", "name", "user_id", "description", "status", "created_at"]
CREATE_PROJECTS_TABLE = """CREATE TABLE IF NOT EXISTS projects (project_id SERIAL PRIMARY KEY, name VARCHAR NOT NULL, user_id INTEGER NOT NULL, description VARCHAR NOT NULL, status VARCHAR NOT NULL DEFAULT 'in progress', created_at TIMESTAMP DEFAULT NOW());"""
INSERT_PROJECT = """INSERT INTO projects (name, description, user_id, status) VALUES (%s, %s, %s, %s) RETURNING project_id;"""
# limit and offset are used for pagination
GET_PROJECTS_BY_NAME = """SELECT * FROM projects WHERE name = %s LIMIT %s OFFSET %s;"""
GET_PROJECTS_BY_PROJECT_ID = """SELECT * FROM projects WHERE project_id = %s;"""
GET_PROJECTS_BY_USER_ID = """SELECT * FROM projects WHERE user_id = %s LIMIT %s OFFSET %s;"""
GET_PROJECTS_BY_TIMESTAMP = """SELECT * FROM projects WHERE created_at = %s LIMIT %s OFFSET %s;"""
EDIT_PROJECT = """UPDATE projects SET name = %s, description = %s WHERE project_id = %s;"""
DELETE_PROJECT = """DELETE FROM projects WHERE project_id = %s;"""

# These next lines describe the table `updates` and the queries used to interact with the db through postgresql
# Updates are separated from the projects for more efficient handling and storing
UPDATES_COLUMN_NAMES = ["update_id", "project_id", "update_title", "update_body", "created_at"]
CREATE_UPDATES_TABLE = """CREATE TABLE IF NOT EXISTS updates (update_id SERIAL PRIMARY KEY, project_id INTEGER NOT NULL, update_title VARCHAR NOT NULL, update_body VARCHAR NOT NULL, created_at TIMESTAMP DEFAULT NOW());"""
INSERT_UPDATE = """INSERT INTO updates (project_id, update_title, update_body) VALUES (%s, %s, %s) RETURNING update_id;"""
GET_UPDATES_BY_PROJECT_ID = """SELECT * FROM updates WHERE project_id = %s;"""

# These next lines describe the table `users` and the queries used to interact with the db through postgresql
CREATE_USERS_TABLE = """CREATE TABLE IF NOT EXISTS users (user_id SERIAL PRIMARY KEY, username VARCHAR NOT NULL, email VARCHAR UNIQUE NOT NULL, password VARCHAR NOT NULL, created_at TIMESTAMP DEFAULT NOW());"""
INSERT_USERS = """INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING user_id;"""
GET_USER = """SELECT * FROM users WHERE email = %s;"""

# These next lines describe the table `tokens` and the queries used to interact with the db through postgresql
CREATE_TOKENS_TABLE = """CREATE TABLE IF NOT EXISTS tokens (token_id SERIAL PRIMARY KEY, token VARCHAR NOT NULL, user_id INTEGER NOT NULL, created_at TIMESTAMP DEFAULT NOW());"""
INSERT_TOKEN = """INSERT INTO tokens (token, user_id) VALUES (%s, %s) RETURNING token_id;"""
GET_TOKEN = """SELECT * FROM tokens WHERE token = %s;"""