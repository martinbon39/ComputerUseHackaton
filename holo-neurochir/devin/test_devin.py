"""Offline tests: a fake Devin v3 server on localhost, the real client and run_missions.follow against it.

    python -m unittest test_devin -v
"""
import io
import json
import pathlib
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import devin_client
from devin_client import Devin, state_of

KEY = "cog_test_secret_value_123456"
KEY_V1 = "apk_test_secret_value_123456"


class Fake(BaseHTTPRequestHandler):
    polls = 0
    seen = []

    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b)

    def _auth(self):
        if self.headers.get("Authorization") not in (f"Bearer {KEY}", f"Bearer {KEY_V1}"):
            self._send(403, {"detail": "Unauthorized"})
            return False
        return True

    def do_GET(self):
        Fake.seen.append(("GET", self.path))
        if not self._auth():
            return
        if self.path == "/v1/sessions?limit=1":
            return self._send(200, {"sessions": [{"session_id": "devin-old"}]})
        if self.path.startswith("/v3/organizations/org-1/sessions/devin-1/messages"):
            if "after=c1" in self.path:
                return self._send(200, {"items": [{"event_id": "e2", "source": "devin", "message": "two"}],
                                        "end_cursor": None, "has_next_page": False})
            return self._send(200, {"items": [{"event_id": "e1", "source": "devin", "message": "one"}],
                                    "end_cursor": "c1", "has_next_page": True})
        if self.path == "/v3/self":
            return self._send(200, {"org_id": "org-1", "principal_type": "service_user"})
        if self.path.startswith("/v3/organizations/org-1/sessions/devin-1/attachments"):
            return self._send(200, [{"name": "REPORT.md", "url": "https://x/REPORT.md", "source": "devin"},
                                    {"name": "in.tgz", "url": "https://x/in.tgz", "source": "user"}])
        if self.path == "/v3/organizations/org-1/sessions/devin-1":
            Fake.polls += 1
            done = Fake.polls >= 3
            return self._send(200, {"session_id": "devin-1", "url": "https://app.devin.ai/sessions/1",
                                    "status": "running", "status_detail": "finished" if done else "working",
                                    "acus_consumed": 1.5 * Fake.polls, "pull_requests": [],
                                    "structured_output": {"mission": "M1", "overall": "PASS"} if done else None})
        self._send(404, {"detail": "nope", "echo": self.headers.get("Authorization")})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        Fake.seen.append(("POST", self.path, body))
        if not self._auth():
            return
        if self.path == "/v3/organizations/org-1/attachments":
            assert b'name="file"' in body
            return self._send(200, {"attachment_id": "a1", "name": "f", "url": "https://att/f"})
        if self.path == "/v3/organizations/org-1/sessions":
            return self._send(200, {"session_id": "devin-1", "url": "https://app.devin.ai/sessions/1", "status": "new"})
        self._send(404, {"detail": "nope"})


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Fake)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        devin_client.API = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_states(self):
        self.assertEqual(state_of({"status": "running", "status_detail": "working"}, "v3"), "running")
        self.assertEqual(state_of({"status": "running", "status_detail": "finished"}, "v3"), "finished")
        self.assertEqual(state_of({"status": "running", "status_detail": "waiting_for_user"}, "v3"), "needs_input")
        self.assertEqual(state_of({"status": "exit"}, "v3"), "finished")
        self.assertEqual(state_of({"status": "suspended", "status_detail": "inactivity"}, "v3"), "suspended")
        self.assertEqual(state_of({"status": "error"}, "v3"), "failed")
        self.assertEqual(state_of({"status_enum": "blocked"}, "v1"), "needs_input")
        self.assertEqual(state_of({"status_enum": "finished"}, "v1"), "finished")

    def test_dry_run_never_shows_key(self):
        out = io.StringIO()
        d = Devin(dry_run=True, out=out)
        d.create_session("p", session_secrets=[{"key": "GH_TOKEN", "value": "ghp_supersecret", "sensitive": True}])
        self.assertNotIn("ghp_supersecret", out.getvalue())
        self.assertIn("<redacted>", out.getvalue())

    def test_live_flow_against_fake_server(self):
        d = Devin(key=KEY)
        self.assertEqual(d.org_id, "org-1")
        with tempfile.NamedTemporaryFile(suffix=".tgz") as f:
            f.write(b"data")
            f.flush()
            url = d.upload(f.name)
        self.assertEqual(url, "https://att/f")
        s = d.create_session("hello", schema={"type": "object"}, attachment_urls=[url], max_acu_limit=3)
        body = json.loads(Fake.seen[-1][2])
        self.assertEqual(body["attachment_urls"], ["https://att/f"])
        self.assertEqual(body["structured_output_schema"], {"type": "object"})
        self.assertNotIn("session_secrets", body)
        final = d.wait(s["session_id"], poll_s=0.01, timeout_s=10)
        self.assertEqual(final["state"], "finished")
        self.assertEqual(final["structured_output"]["overall"], "PASS")

    def test_check_auth_is_read_only(self):
        n = len(Fake.seen)
        self.assertEqual(Devin(key=KEY_V1).check_auth(), {"api_version": "v1", "authenticated": True, "sessions_listed": 1})
        r = Devin(key=KEY).check_auth()
        self.assertEqual((r["api_version"], r["authenticated"], r["org_id_present"]), ("v3", True, True))
        self.assertTrue(all(x[0] == "GET" for x in Fake.seen[n:]))

    def test_messages_follow_cursor(self):
        msgs = Devin(key=KEY, org_id="org-1").messages("devin-1")
        self.assertEqual([m["message"] for m in msgs], ["one", "two"])

    def test_blocked_details_are_not_running(self):
        self.assertEqual(state_of({"status": "running", "status_detail": "out_of_credits"}, "v3"), "suspended")

    def test_errors_do_not_leak_key(self):
        d = Devin(key=KEY, org_id="org-1")
        with self.assertRaises(devin_client.DevinError) as e:
            d.session("devin-unknown")
        self.assertNotIn(KEY, str(e.exception))

    def test_follow_writes_status(self):
        import run_missions
        Fake.polls = 0
        with tempfile.TemporaryDirectory() as tmp:
            run_missions.STATUS = pathlib.Path(tmp) / "STATUS.json"
            run_missions.PAGE = pathlib.Path(tmp) / "page.html"
            status = {"mode": "live", "api_version": "v3", "commit": "abc", "sessions": [
                {"mission": "M1", "title": "M1", "session_id": "devin-1", "url": None, "state": "running",
                 "max_acu": 3, "bundle": {"name": "b.tgz", "sha256": "0" * 64, "bytes": 1}}]}
            run_missions.follow(Devin(key=KEY, org_id="org-1"), status, poll_s=0.01, timeout_s=10, publish=False)
            saved = json.loads(run_missions.STATUS.read_text())
            s = saved["sessions"][0]
            self.assertEqual(s["state"], "finished")
            self.assertTrue(s["final"])
            self.assertEqual([a["name"] for a in s["attachments"]], ["REPORT.md"])
            self.assertIn("terminée", run_missions.PAGE.read_text())

    def test_schema_from_example(self):
        import run_missions
        sch = run_missions.example_to_schema({"a": "x", "b": [{"c": 1, "d": True}], "e": {}})
        self.assertEqual(sch["required"], ["a", "b", "e"])
        self.assertEqual(sch["properties"]["b"]["items"]["properties"]["d"], {"type": "boolean"})


if __name__ == "__main__":
    unittest.main()
