# Todo REST API

A small, dependency-free REST API built with Python's standard library. Todo data is held in memory and resets when the server restarts.

## Run

Requires Python 3.8 or newer.

```sh
python3 app.py
```

The server listens on port `8000`.

Open `http://localhost:8000` in a browser to add, complete, and delete todos using plain HTML forms. No browser JavaScript or CSS is required. Todo data is in memory and resets when the server restarts.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `GET` | `/version` | API version |
| `GET` | `/todos` | List todos |
| `POST` | `/todos` | Create a todo with `{"title":"Buy milk"}` |
| `GET` | `/todos/{id}` | Get a todo |
| `PUT` | `/todos/{id}` | Update a todo with `{"title":"Buy milk","completed":true}` |
| `DELETE` | `/todos/{id}` | Delete a todo |

## Test and package

```sh
python3 -m unittest -v
python3 package.py
```

The package command creates `dist/todo-api.zip`.

## Jenkins

Create a Jenkins Pipeline or Multibranch Pipeline job connected to this repository. The declarative `Jenkinsfile` checks out the configured SCM, compiles the Python files, runs the unit tests, packages the application, and archives `dist/todo-api.zip` as a fingerprinted build artifact. Unix agents need `python3` on their PATH. On Windows agents, configure the node environment variable `PYTHON_EXE` with the full path to `python.exe`.
