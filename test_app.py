import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode

import app


class TodoApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), app.TodoHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        with app._lock:
            app._todos.clear()
            app._next_id = 1

    def request(self, method, path, payload=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port)
        body = json.dumps(payload) if payload is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        content = response.read()
        connection.close()
        return response.status, json.loads(content) if content else None

    def request_form(self, path, payload):
        connection = http.client.HTTPConnection("127.0.0.1", self.port)
        body = urlencode(payload)
        connection.request(
            "POST",
            path,
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = connection.getresponse()
        content = response.read()
        connection.close()
        return response.status, content

    def test_create_list_update_and_delete_todo(self):
        status, created = self.request("POST", "/todos", {"title": "  Ship it  "})
        self.assertEqual(status, 201)
        self.assertEqual(created, {"id": 1, "title": "Ship it", "completed": False})

        status, todos = self.request("GET", "/todos")
        self.assertEqual(status, 200)
        self.assertEqual(todos, [created])

        status, updated = self.request(
            "PUT", "/todos/1", {"title": "Done", "completed": True}
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["title"], "Done")
        self.assertTrue(updated["completed"])

        status, _ = self.request("DELETE", "/todos/1")
        self.assertEqual(status, 204)
        self.assertEqual(self.request("GET", "/todos/1")[0], 404)

    def test_rejects_missing_or_invalid_title(self):
        self.assertEqual(self.request("POST", "/todos", {})[0], 400)
        self.assertEqual(self.request("POST", "/todos", {"title": "  "})[0], 400)
        self.assertEqual(self.request("POST", "/todos", {"title": 42})[0], 400)

    def test_health_endpoint(self):
        self.assertEqual(self.request("GET", "/health"), (200, {"status": "ok"}))

    def test_homepage_serves_todo_app(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port)
        connection.request("GET", "/")
        response = connection.getresponse()
        content = response.read().decode("utf-8")
        connection.close()

        self.assertEqual(response.status, 200)
        self.assertTrue(response.getheader("Content-Type").startswith("text/html"))
        self.assertIn("<title>Todo List</title>", content)
        self.assertIn('<form action="/" method="post">', content)
        self.assertNotIn("<script", content)
        self.assertNotIn("<style", content)

    def test_plain_html_forms_create_complete_and_delete_todos(self):
        status, _ = self.request_form("/", {"title": "Plain HTML task"})
        self.assertEqual(status, 303)
        self.assertEqual(self.request("GET", "/todos")[1][0]["title"], "Plain HTML task")

        status, _ = self.request_form("/todos/1/toggle", {})
        self.assertEqual(status, 303)
        self.assertTrue(self.request("GET", "/todos/1")[1]["completed"])

        status, _ = self.request_form("/todos/1/delete", {})
        self.assertEqual(status, 303)
        self.assertEqual(self.request("GET", "/todos")[1], [])


if __name__ == "__main__":
    unittest.main()
