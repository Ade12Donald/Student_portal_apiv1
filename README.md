# Student Portal API (Flask+MongoDB)

## Features

- Create a student account (name, registration number, email)
- Retrieve a student's own details by ID
- Update a student's own profile — **name only**; registration number and
  email can never be changed after creation
- Permanently delete a student's own account
- Students can only read, update, or delete **their own** record

## Stack

- **Flask** — routing and request/response handling
- **PyMongo** — talks directly to MongoDB (no ORM layer in between)
- **python-dotenv** — loads `MONGO_URI`/`MONGO_DB_NAME` from `.env`
- **pytest + mongomock** — test suite, run against an in-memory Mongo
  stand-in so it doesn't need a live server. The real app (`run.py`)
  always uses a genuine MongoDB connection — mongomock only exists
  inside the test suite.

## How "own information only" is enforced

Each student is issued a random `access_token` at account creation,
returned **once** in the create response. Every request touching a
specific student's record must include it:

```
Authorization: Token <access_token>
```

Missing or wrong token → `403 Forbidden`. This is a lightweight API-key
pattern rather than a full login system, matching the scope of the
assignment.

## Project layout

```
app/
  __init__.py     Flask app factory
  db.py           MongoDB connection + collection helper (PyMongo)
  routes.py       All CRUD endpoints
  validators.py   Plain-Python request validation (no framework needed)
run.py            Entry point — loads .env, starts the app
tests/
  test_api.py     pytest suite covering CRUD + ownership restrictions
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
copy .env.example .env         # Windows: copy, macOS/Linux: cp
```

You need a MongoDB server to point at — either:
- **Local**: install MongoDB Community Server (Compass is just the GUI
  viewer, it needs a real `mongod` to connect to), then the default
  `mongodb://localhost:27017` in `.env.example` works as-is.
- **MongoDB Atlas** (no local install): free cluster, then paste its
  connection string into `MONGO_URI` in `.env`.

Then:

```bash
python run.py
```

The API is available at `http://127.0.0.1:5000/api/students`.

### Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite runs against mongomock automatically — no MongoDB server
needed just to run `pytest`.

## Endpoints

### Create an account

```
POST /api/students
Content-Type: application/json

{
  "name": "Ada Lovelace",
  "reg_no": "ENG/20/0001",
  "email": "ada@example.com"
}
```

**201 Created**

```json
{
  "id": "66f1a2b3c4d5e6f7a8b9c0d1",
  "name": "Ada Lovelace",
  "reg_no": "ENG/20/0001",
  "email": "ada@example.com",
  "access_token": "3c9f2b1a...hex...",
  "created_at": "2026-09-04T10:00:00+00:00",
  "updated_at": "2026-09-04T10:00:00+00:00"
}
```

Save the `access_token` — it's the only time it's returned.

### Get a student's own details

```
GET /api/students/<id>
Authorization: Token <access_token>
```

200 with the student's details (no token in the response), 403 if the
token is missing/wrong, 404 if the id doesn't exist.

### Update a profile (name only)

```
PATCH /api/students/<id>
Authorization: Token <access_token>
Content-Type: application/json

{ "name": "Ada K. Lovelace" }
```

`reg_no` and `email` are never read from the body here — even if included,
they're ignored and the stored values stay untouched.

### Delete an account

```
DELETE /api/students/<id>
Authorization: Token <access_token>
```

**200 OK** — `{"detail": "Account deleted successfully."}`

## Testing it manually (curl)

```bash
curl -X POST http://127.0.0.1:5000/api/students -H "Content-Type: application/json" -d "{\"name\":\"Ada\",\"reg_no\":\"ENG/20/0001\",\"email\":\"ada@example.com\"}"

curl http://127.0.0.1:5000/api/students/<id> -H "Authorization: Token <access_token>"

curl -X PATCH http://127.0.0.1:5000/api/students/<id> -H "Authorization: Token <access_token>" -H "Content-Type: application/json" -d "{\"name\":\"New Name\"}"

curl -X DELETE http://127.0.0.1:5000/api/students/<id> -H "Authorization: Token <access_token>"
```

Open MongoDB Compass alongside this and watch the `student_portal` →
`students` collection change as you run each request.
