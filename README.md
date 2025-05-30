# Cleaning service

A specialized service where users can act as contractors and post cleaning offers, or register as a customer
and find a contractor.


### Motivation
To build an CRUD API with FastAPI, SQLAlchemy, Postgres, Docker

#### Core technologies
- FastAPI - web framework for building APIs with Python 3.12+ based on standard Python type hints.
- SQLAlchemy - Object Relational Mapper.
- Pydantic -  Data validation library for Python and FastAPI models.
- Uvicorn - ASGI web server implementation for Python.
- Gunicorn - python WSGI HTTP Server for UNIX.
- Alembic - lightweight database migration tool for usage with the SQLAlchemy Database Toolkit for Python.
- Docker - tool to package and run an application in a loosely isolated environment.
- Docker Compose - tool for defining and running multi-container Docker applications.
- Postgres - open source object-relational database.
- Nginx - HTTP web server, reverse proxy, content cache, load balancer, TCP/UDP proxy server, and mail proxy server.
- For testing:
    - pytest
    - pytest-cov
    - pytest-asyncio
    - pytest-mock
    - pytest-postgresql
- For development
    - precommit-hook
    - isort
    - black
    - flake8
    - poetry
    - venv

### Implemented functionalities
- JWT Authentication
- Password Hashing
- Login & Register Endpoints
- ORM Objects representing SQL tables and relationships
- Pydantic schemas
- CRUD module for reading, updating, deleting objects in/from database
- Cursor-based pagination
- OAuth2 scopes
- Email verification
- Dependencies - active user, cleaner, customer, database
- Separate database for testing

additionally:
- NGINX with basic settings and CORS support
- Logging
- Gunicorn for performance optimization


**Entity Relationship Diagram**

![ER Diagram](media/cleaning_erd.png?raw=true "ER Diagram")

## How to run

### You should have
- Running Docker
- Installed Make (not mandatory) - use makefile to run all commands
- Installed OpenSSL


clone repository:

```bash
git clone https://github.com/bizoxe/cleaning-service.git
```
and navigate to cloned project

### create private and public keys (used to sign json web tokens):
```bash
# you should have OpenSSL installed
make keys
```

alternatively:
```bash
# you should have OpenSSL installed
# commands must be run inside the fastapi-application directory
mkdir certs
cd certs
openssl genrsa -out jwt-private.pem 2048
openssl rsa -in jwt-private.pem -outform PEM -pubout -out jwt-public.pem
```

### build project in production mode:
```bash
# this command will build docker images, up containers in detached mode;
# the app will be launched on gunicorn + uvicorn workers
make prod
```

alternatively:
```bash
TARGET_ENV=production docker compose build
POSTGRES_PASSWORD=supersecretpassword docker compose up -d
```

### or in development mode:
```bash
# the application will only run on uvicorn
make dev
```

alternatively:
```bash
TARGET_ENV=development docker compose build
POSTGRES_PASSWORD=supersecretpassword docker compose up -d
```

### run Alembic migrations, initialize user roles and permissions:
```bash
make init_roles
```

alternatively:
```bash
docker exec -it fastapi-cleaning-service alembic upgrade head
docker exec -it fastapi-cleaning-service python commands.py
```

### next time if you already have build container you can just type:
```bash
# will start containers in the background and leave them running
make up
# stop services only
make stop
# stop and remove containers
make down
```

alternatively:
```bash
docker compose up -d
docker compose stop
docker compose down
```

### to run tests:
```bash
make test
```

alternatively:
```bash
docker compose run app test
```

## First steps:

new user registration:
```bash
curl -X 'POST' \
  'http://0.0.0.0:8000/api/v1/auth/signup' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "dolgorukaya@gmail.com",
  "password": "elenastringL1@",
  "confirm_password": "elenastringL1@"
}'
```

So, after creating the first user, you need to generate a JWT token to access the various endpoints.
To do this, use:
```bash
curl -X 'POST' \
  'http://0.0.0.0:8000/api/v1/auth/signin' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=dolgorukaya%40gmail.com&password=elenastringL1%40'
```

In response you will receive something like this:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwic3ViIjoiYzUwNTg1OTctNjkwN...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInN1YiI6ImM1MDU4NTk3LTY5...",
  "token_type": "Bearer"
}
```

And you need to use access token in headers when calling other endpoints eg:
(refresh token is used to refresh the access token)
```bash
curl -X 'GET' \
  'http://0.0.0.0:8000/api/v1/profiles' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwic3ViIjoiYzUwNTg1OTctNjkwN...'
```

You can also do everything using FastAPI docs, which are more convenient and easy to use.
For this, check http://localhost:8000/docs
