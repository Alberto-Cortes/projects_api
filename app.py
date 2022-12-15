from flask import Flask, request
import os
import psycopg2
from dotenv import load_dotenv
import src.endpoints.users as users
import src.endpoints.projects as projects


# Load the environment variables from the .env file
load_dotenv()

# Create the flask app, connect to the database
app = Flask(__name__)
url = os.getenv("DATABASE_URL")
secret_key = os.getenv("SECRET_KEY")
salt = str.encode(os.getenv("SALT"))
connection = psycopg2.connect(url)

# All the routes are handled by the functions defined on the src/endpoints folder
# On this folder there are files for each main entity of the API, USERS and PROJECTS

# This route is used to create a new user and returns a status code alongside a fresh token
@app.post("/api/auth/create_user")
def create_user():
    return users.create_user(connection, salt, secret_key, request)

# This route is used to login a user and returns a status code alongside a fresh token
# The required parameters are the email and the password
@app.post("/api/auth/login")
def login():
    return users.login(connection, salt, secret_key, request)

# This route is used to create a new project and returns a status code alongside the project_id
# The required parameters are the name, description, status and token
@app.post("/api/create_project")
def create_project():
    return projects.create_project(connection, request)

# This route is used to get all the projects of a user according to the input value and returns a status code alongside the projects
# The projects are fetched in order of the parameters given
# Said order is: name, project_id, user_id, timestamp
# The parameters optional are the name, project_id, user_id, timestamp, per_page and offset
# The per_page parameter is used to limit the number of projects returned
# The offset parameter is used to skip a number of projects
# The parameters that must be provided are the token and the per_page and at least one of the other parameters
@app.get("/api/get_projects")
def get_projects():
    return projects.get_projects(connection, request)

# This route is used to edit a project, receives a project_id, name, description and token
# The parameters that are not given are not updated
# The parameters that must be given are project_id, name, description and token
@app.put("/api/edit_project")
def edit_project():
    return projects.edit_project(connection, request)
    
# This route is used to delete a project, receives a project_id and a token
@app.delete("/api/delete_project")
def delete_project():
    return projects.delete_project(connection, request)

# TODO: Create all tables when running main
if __name__ == "__main__":
    app.run()   