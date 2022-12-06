# Project Manager API
A simple API to manage projects, this works by handling http requests and using SQL queries to interact with a postgresql database that holds the following tables:

1. users
2. projects
3. updates
4. tokens

## Requirements
You will need to install the requirements.txt file using pip
The command you can use to install them is:

`python -m pip install -r requirements.txt`

## Endpoints
The app consists of the following endpoints with their respective parameters sent through the body of the http request. 
Every endpoint that interacts with the tables requires a valid token to execute the requested action, users may not modify or delete projects that do not belong to them.
Alongside every endpoint will have an example request as well as an example response.

### POST /api/create_user
This endpoint is used to create a user, it requires the following parameters:
- name: the name of the user
- email: the email of the user
- password: the password of the user

Example request:
```
{
    "username": "user",
    "email": "user@mail.com",
    "password": "p4ssw0rd"
}
```
Example response:
```
{
    "status": 200,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NzAzMDY4NzEsImlhdCI6MTY3MDMwNjg2Niwic3ViIjo1fQ.ojyD-_W-T2nlPXBhFwVC5-6UUkVHRsI4lieacGwWl84"
}
```

### POST /api/login
This endpoint is used to login a user, this returns a fresh token, it requires the following parameters:
- email: the email of the user
- password: the password of the user

Example request:
```
{
    "email": "user@mail.com",
    "password": "p4ssw0rd"
}
```
Example response:
```
{
    "status": 200,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NzAzMDY4NzEsImlhdCI6MTY3MDMwNjg2Niwic3ViIjo1fQ.ojyD-_W-T2nlPXBhFwVC5-6UUkVHRsI4lieacGwWl84"
}
```
### POST /api/create_project
This endpoint is used to create a project, it requires a token and the following parameters:
- name: the name of the project
- description: the description of the project

Example request:
```
{
    "name": "project",
    "description": "this is not a real project",
    "status": "in progress",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NzAzMDY4NzEsImlhdCI6MTY3MDMwNjg2Niwic3ViIjo1fQ.ojyD-_W-T2nlPXBhFwVC5-6UUkVHRsI4lieacGwWl84"
}
```
Example response:
```
{
    "project_id": 1,
    "status": 200
}
```

### GET /api/get_projects
This endpoint is used to get projects from the database, it requires a token and at least one of the following parameters:
- name: the name of the project to be searched
- project_id: the id of the project to be searched
- user_id: the id of the user that owns the project
- timestamp: the timestamp of the project
- per_page: the number of projects to be returned
- offset: the number of projects to skip
Example request:
```
{
    "user_id": 1,
    "per_page": 10,
    "offset": 0,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NzAzMDY4NzEsImlhdCI6MTY3MDMwNjg2Niwic3ViIjo1fQ.ojyD-_W-T2nlPXBhFwVC5-6UUkVHRsI4lieacGwWl84"
}
```
Example response:
```
{
    "offset": 0,
    "per_page": 10,
    "projects": [
        {
            "created_at": "Tue, 06 Dec 2022 06:11:30 GMT",
            "description": "5",
            "name": "new name",
            "project_id": 3,
            "status": "in progress",
            "updates": [
                {
                    "created_at": "Tue, 06 Dec 2022 06:12:51 GMT",
                    "project_id": 3,
                    "update_body": "new update noteeeeeeeee",
                    "update_id": 2,
                    "update_title": "new descriptionnnnnnnnn"
                }
            ],
            "user_id": 5
        }
    ],
    "status": 200
}
```
### PUT /api/edit_project
This endpoint is used to edit a project, it requires a token and the following parameters:
- project_id: the id of the project to be edited
- name: the new name of the project
- description: the new description of the project
- update_title: the title of the update
- update_body: the body of the update
Example request:
```
{
    "name" : "new name",
    "update_title" : "new descriptionnnnnnnnn",
    "update_body" : "new update noteeeeeeeee",
    "project_id": 3,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NzAzMDY4NzEsImlhdCI6MTY3MDMwNjg2Niwic3ViIjo1fQ.ojyD-_W-T2nlPXBhFwVC5-6UUkVHRsI4lieacGwWl84"
}
```
Example response:
```
{
    "message": "Project updated",
    "status": 200
}
```
### DELETE /api/delete_project
This endpoint is used to delete a project, it requires a token and the following parameters:
- project_id: the id of the project to be deleted
Example request:
```
{
    "project_id": "3",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NzAzMDY4NzEsImlhdCI6MTY3MDMwNjg2Niwic3ViIjo1fQ.ojyD-_W-T2nlPXBhFwVC5-6UUkVHRsI4lieacGwWl84"
}
```
Example response:
```
{
    "message": "Project deleted",
    "status": 200
}
```

