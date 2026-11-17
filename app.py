import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlparse


_INDEX_HTML = Path(__file__).with_name("index.html")
_todos = {}
_next_id = 1
_lock = Lock()


def _create_todo(title):
    if not isinstance(title, str) or not title.strip():
        return None

    global _next_id
    with _lock:
        todo_id = _next_id
        _next_id += 1
        todo = {"id": todo_id, "title": title.strip(), "completed": False}
        _todos[todo_id] = todo
    return todo


class TodoHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return None
            payload = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _read_form(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            values = parse_qs(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None
        return values

    def _render_home(self, status=200, message=""):
        with _lock:
            todos = list(_todos.values())

        items = []
        for todo in todos:
            title = html.escape(todo["title"])
            state = "Completed" if todo["completed"] else "Pending"
            action_label = "Mark pending" if todo["completed"] else "Mark complete"
            items.append(
                '<li>%s — %s '
                '<form action="/todos/%s/toggle" method="post">'
                '<button type="submit">%s</button></form> '
                '<form action="/todos/%s/delete" method="post">'
                '<button type="submit">Delete</button></form></li>'
                % (title, state, todo["id"], action_label, todo["id"])
            )

        page = _INDEX_HTML.read_text(encoding="utf-8")
        page = page.replace("<!-- TODO_ITEMS -->", "\n".join(items))
        page = page.replace("<!-- MESSAGE -->", html.escape(message))
        self._send_html(status, page.encode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/":
            self._render_home()
            return
        if path == "/health":
            return self._send_json(200, {"status": "ok"})
        if path == "/todos":
            with _lock:
                return self._send_json(200, list(_todos.values()))

        todo_id = self._todo_id(path)
        if todo_id is None:
            return self._send_json(404, {"error": "Not found"})
        with _lock:
            todo = _todos.get(todo_id)
        if todo is None:
            return self._send_json(404, {"error": "Todo not found"})
        self._send_json(200, todo)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/":
            form = self._read_form()
            title = form.get("title", [""])[0] if form else ""
            if _create_todo(title) is None:
                return self._render_home(400, "A non-empty title is required.")
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if path.startswith("/todos/"):
            todo_id, action = self._todo_action(path)
            if todo_id is None or action not in ("toggle", "delete"):
                return self._send_json(404, {"error": "Not found"})
            with _lock:
                todo = _todos.get(todo_id)
                if todo is None:
                    return self._render_home(404, "Todo not found.")
                if action == "toggle":
                    todo["completed"] = not todo["completed"]
                else:
                    del _todos[todo_id]
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if path != "/todos":
            return self._send_json(404, {"error": "Not found"})
        payload = self._read_json()
        title = payload.get("title") if payload else None
        todo = _create_todo(title)
        if todo is None:
            return self._send_json(400, {"error": "A non-empty title is required"})

        self._send_json(201, todo)

    def do_PUT(self):
        todo_id = self._todo_id(urlparse(self.path).path.rstrip("/"))
        if todo_id is None:
            return self._send_json(404, {"error": "Not found"})
        payload = self._read_json()
        if not payload or not isinstance(payload.get("title"), str) or not payload["title"].strip():
            return self._send_json(400, {"error": "A non-empty title is required"})
        if "completed" in payload and not isinstance(payload["completed"], bool):
            return self._send_json(400, {"error": "completed must be a boolean"})

        with _lock:
            todo = _todos.get(todo_id)
            if todo is None:
                return self._send_json(404, {"error": "Todo not found"})
            todo["title"] = payload["title"].strip()
            if "completed" in payload:
                todo["completed"] = payload["completed"]
        self._send_json(200, todo)

    def do_DELETE(self):
        todo_id = self._todo_id(urlparse(self.path).path.rstrip("/"))
        if todo_id is None:
            return self._send_json(404, {"error": "Not found"})
        with _lock:
            if _todos.pop(todo_id, None) is None:
                return self._send_json(404, {"error": "Todo not found"})
        self.send_response(204)
        self.end_headers()

    @staticmethod
    def _todo_id(path):
        parts = path.split("/")
        if len(parts) != 3 or parts[1] != "todos":
            return None
        try:
            todo_id = int(parts[2])
            return todo_id if todo_id > 0 else None
        except ValueError:
            return None

    @staticmethod
    def _todo_action(path):
        parts = path.split("/")
        if len(parts) != 4 or parts[1] != "todos":
            return None, None
        try:
            todo_id = int(parts[2])
            return (todo_id, parts[3]) if todo_id > 0 else (None, None)
        except ValueError:
            return None, None

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))


def main():
    server = ThreadingHTTPServer(("0.0.0.0", 8000), TodoHandler)
    print("Todo API listening on http://0.0.0.0:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
