#!/usr/bin/env python3
"""Small client for the Devin API (Cognition), stdlib only.

API v3 (current): https://docs.devin.ai/api-reference/overview.md, spec https://docs.devin.ai/v3-openapi.yaml
  base https://api.devin.ai/v3/organizations/{org_id}, header "Authorization: Bearer <key>", keys prefixed cog_
  (service user or personal access token). org_id comes from DEVIN_ORG_ID or GET /v3/self.
API v1 (legacy, keys apk_ / apk_user_): https://docs.devin.ai/api-reference/v1/overview.md, base https://api.devin.ai/v1

Key: DEVIN_API_KEY, else ~/.devin_key. It is never printed, logged or written. --dry-run needs no key and prints the
requests that would be sent, with the key replaced by <redacted>.

    python devin_client.py check-auth      # read-only, creates no session, costs no ACU
    python devin_client.py self
    python devin_client.py create --prompt-file p.md [--schema s.json] [--attach f.tgz] [--title T] [--max-acu 10] [--dry-run]
    python devin_client.py status <session_id> | wait <session_id> | message <session_id> "text" | messages <session_id>
    python devin_client.py attachments <session_id> | download <attachment_url> <dest>
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

API = "https://api.devin.ai"
KEY_FILE = pathlib.Path.home() / ".devin_key"
DRY_KEY = "<redacted>"
STATES = ("running", "needs_input", "finished", "failed", "suspended")
TERMINAL = {"needs_input", "finished", "failed", "suspended"}  # wait() returns on these
FINAL = {"finished", "failed", "suspended"}  # nothing more will happen without a message
BLOCKED_DETAILS = {"usage_limit_exceeded", "out_of_credits", "out_of_quota", "no_quota_allocation", "payment_declined"}


class DevinError(RuntimeError):
    pass


def load_key() -> str | None:
    key = os.environ.get("DEVIN_API_KEY", "").strip()
    if not key and KEY_FILE.exists():
        key = KEY_FILE.read_text().strip()
    return key or None


def state_of(s: dict, version: str) -> str:
    """One of STATES. v3: status new|claimed|running|exit|error|suspended|resuming, status_detail working|
    waiting_for_user|waiting_for_approval|finished|<suspension reason>. v1: status_enum working|blocked|expired|finished|
    suspend_requested*|resume_requested*|resumed."""
    if version == "v1":
        e = s.get("status_enum") or ""
        return {"blocked": "needs_input", "finished": "finished", "expired": "failed"}.get(
            e, "suspended" if e.startswith("suspend") else "running")
    st, detail = s.get("status"), s.get("status_detail")
    if st == "exit" or detail == "finished":
        return "finished"
    if st == "error" or detail == "error":
        return "failed"
    if st == "suspended":
        return "suspended"
    if detail in ("waiting_for_user", "waiting_for_approval"):
        return "needs_input"
    if detail in BLOCKED_DETAILS:
        return "suspended"
    return "running"


def pr_urls(s: dict) -> list[str]:
    prs = s.get("pull_requests") or ([s["pull_request"]] if s.get("pull_request") else [])
    return [p.get("pr_url") or p.get("url") for p in prs if p]


class Devin:
    def __init__(self, key: str | None = None, org_id: str | None = None, dry_run: bool = False, out=sys.stdout):
        self.dry_run, self.out = dry_run, out
        self._key = key if key is not None else (None if dry_run else load_key())
        if not self._key and not dry_run:
            raise DevinError(f"no key: set DEVIN_API_KEY or write it to {KEY_FILE}")
        self.version = "v1" if (self._key or "").startswith("apk_") else "v3"
        self.org_id = org_id or os.environ.get("DEVIN_ORG_ID") or None
        if self.version == "v3" and not self.org_id:
            me = {} if dry_run else self.whoami()
            self.org_id = "<org_id>" if dry_run else (me.get("org_id") or me.get("devin_sessions_org_id"))
            if not self.org_id:
                raise DevinError("GET /v3/self returned no org_id; set DEVIN_ORG_ID")

    # transport
    def _url(self, path: str) -> str:
        if self.version == "v1":
            return f"{API}/v1{path}"
        return f"{API}/v3{path}" if path == "/self" else f"{API}/v3/organizations/{self.org_id}{path}"

    def _call(self, method: str, path: str, body: dict | None = None, query: dict | None = None,
              upload: pathlib.Path | None = None, retries: int = 4):
        url = self._url(path)
        if query:
            url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None}, doseq=True)
        headers = {"Authorization": f"Bearer {DRY_KEY if self.dry_run else self._key}", "Accept": "application/json"}
        data = None
        if upload is not None:
            boundary = uuid.uuid4().hex
            ctype = mimetypes.guess_type(upload.name)[0] or "application/octet-stream"
            data = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{upload.name}\"\r\n"
                    f"Content-Type: {ctype}\r\n\r\n").encode() + (b"" if self.dry_run else upload.read_bytes()) + \
                f"\r\n--{boundary}--\r\n".encode()
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        elif body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if self.dry_run:
            shown = {"file": f"{upload} ({upload.stat().st_size} bytes)"} if upload else dict(body or {})
            if shown.get("session_secrets"):
                shown["session_secrets"] = [{**x, "value": DRY_KEY} for x in shown["session_secrets"]]
            print(json.dumps({"dry_run": True, "method": method, "url": url, "headers": headers, "body": shown},
                             indent=2, ensure_ascii=False), file=self.out)
            return None
        for attempt in range(retries + 1):
            req = urllib.request.Request(url, data=data, method=method, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    raw = r.read().decode()
                    try:
                        return json.loads(raw) if raw else None
                    except json.JSONDecodeError:
                        return raw.strip().strip('"')
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:500].replace(self._key, DRY_KEY)
                if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                    time.sleep(min(60, 5 * 2 ** attempt))
                    continue
                raise DevinError(f"{method} {path} -> HTTP {e.code}: {detail}") from None
            except urllib.error.URLError as e:
                if attempt < retries:
                    time.sleep(5 * 2 ** attempt)
                    continue
                raise DevinError(f"{method} {path} -> {e.reason}") from None

    # endpoints
    def whoami(self) -> dict:
        """GET /v3/self: principal and org_id of the key (v3 only)."""
        return self._call("GET", "/self") or {}

    def check_auth(self) -> dict:
        """Read-only authentication check that creates nothing: v3 GET /v3/self, v1 GET /v1/sessions?limit=1."""
        if self.version == "v1":
            r = self._call("GET", "/sessions", query={"limit": 1}) or {}
            items = r.get("sessions", r) if isinstance(r, dict) else r
            return {"api_version": "v1", "authenticated": True, "sessions_listed": len(items or [])}
        me = self.whoami()
        return {"api_version": "v3", "authenticated": True, "principal_type": me.get("principal_type"),
                "org_id_present": bool(self.org_id)}

    def upload(self, path: str | os.PathLike) -> str:
        """POST /attachments (multipart 'file'). Returns the attachment URL (v3: .url, v1: plain string)."""
        r = self._call("POST", "/attachments", upload=pathlib.Path(path))
        if r is None:
            return f"https://dry-run.invalid/attachments/{pathlib.Path(path).name}"
        return r["url"] if isinstance(r, dict) else r

    def create_session(self, prompt: str, *, title: str | None = None, tags: list[str] | None = None,
                       schema: dict | None = None, attachment_urls: list[str] | None = None,
                       max_acu_limit: int | None = None, repos: list[str] | None = None,
                       session_secrets: list[dict] | None = None) -> dict:
        """POST /sessions. v3 takes attachment_urls, repos and structured_output_schema as fields; v1 has no
        attachment field, so files go in the prompt as ATTACHMENT:"<url>" lines (v1 upload doc). session_secrets
        [{key, value, sensitive}] exist only in this session; dry-run shows their keys, never their values."""
        body: dict = {"prompt": prompt, "title": title, "tags": tags or None, "max_acu_limit": max_acu_limit,
                      "structured_output_schema": schema, "session_secrets": session_secrets or None}
        if self.version == "v3":
            body.update(attachment_urls=attachment_urls or None, repos=repos or None)
        elif attachment_urls:
            body["prompt"] = prompt + "\n\n" + "\n".join(f'ATTACHMENT:"{u}"' for u in attachment_urls)
        body = {k: v for k, v in body.items() if v is not None}
        r = self._call("POST", "/sessions", body=body)
        return r or {"session_id": "devin-dryrun-" + uuid.uuid4().hex[:8], "url": "https://app.devin.ai/sessions/dry-run",
                     "status": "dry_run"}

    def session(self, sid: str) -> dict:
        return self._call("GET", f"/sessions/{sid}") or {"session_id": sid, "status": "dry_run"}

    def send(self, sid: str, message: str) -> dict | None:
        """v3: POST /sessions/{id}/messages (resumes a suspended session). v1: POST /sessions/{id}/message."""
        return self._call("POST", f"/sessions/{sid}/{'message' if self.version == 'v1' else 'messages'}",
                          body={"message": message})

    def messages(self, sid: str) -> list[dict]:
        if self.version == "v1":
            return (self.session(sid) or {}).get("messages") or []
        items, after = [], None
        while True:
            r = self._call("GET", f"/sessions/{sid}/messages", query={"first": 200, "after": after}) or {}
            items += r.get("items", [])
            after = r.get("end_cursor")
            if not r.get("has_next_page") or not after:
                return items

    def attachments(self, sid: str) -> list[dict]:
        """Files of the session (v3 only): [{attachment_id, content_type, name, source, url}]."""
        if self.version == "v1":
            return []
        r = self._call("GET", f"/sessions/{sid}/attachments")
        return r if isinstance(r, list) else (r or {}).get("items", [])

    def download(self, url: str, dest: str | os.PathLike) -> pathlib.Path:
        """Fetch an attachment. The v3 download path answers 307 to a presigned URL, which must be fetched WITHOUT the
        bearer header, so redirects are followed by hand."""
        dest = pathlib.Path(dest)
        if self.dry_run:
            print(json.dumps({"dry_run": True, "method": "GET", "url": url, "dest": str(dest)}), file=self.out)
            return dest

        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None

        opener = urllib.request.build_opener(NoRedirect)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self._key}"})
        try:
            with opener.open(req, timeout=120) as r:
                data = r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (301, 302, 303, 307, 308) or not e.headers.get("Location"):
                raise DevinError(f"GET attachment -> HTTP {e.code}") from None
            with urllib.request.urlopen(e.headers["Location"], timeout=120) as r:
                data = r.read()
        dest.write_bytes(data)
        return dest

    def terminate(self, sid: str) -> None:
        self._call("DELETE", f"/sessions/{sid}")

    def summary(self, sid: str, s: dict | None = None) -> dict:
        s = s or self.session(sid)
        return {"session_id": s.get("session_id", sid), "url": s.get("url"), "state": state_of(s, self.version),
                "status": s.get("status_enum") or s.get("status"), "status_detail": s.get("status_detail"),
                "acus_consumed": s.get("acus_consumed"), "pull_requests": pr_urls(s),
                "structured_output": s.get("structured_output"), "updated_at": s.get("updated_at")}

    def wait(self, sid: str, poll_s: float = 30, timeout_s: float = 4 * 3600, on_update=None) -> dict:
        """Poll until a TERMINAL state or timeout. on_update(summary) is called whenever the summary changes."""
        last, t0 = None, time.time()
        while True:
            cur = self.summary(sid)
            if cur != last and on_update:
                on_update(cur)
            last = cur
            if self.dry_run or cur["state"] in TERMINAL or time.time() - t0 > timeout_s:
                return cur
            time.sleep(poll_s)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--org-id")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self")
    sub.add_parser("check-auth", help="read-only: verify the key, create nothing")
    c = sub.add_parser("create")
    c.add_argument("--prompt-file", required=True)
    c.add_argument("--schema", help="JSON schema file for structured output")
    c.add_argument("--attach", action="append", default=[], help="local file to upload and attach (repeatable)")
    c.add_argument("--repo", action="append", default=[])
    c.add_argument("--title")
    c.add_argument("--tag", action="append", default=[])
    c.add_argument("--max-acu", type=int)
    c.add_argument("--wait", action="store_true")
    for name in ("status", "wait", "messages", "attachments", "terminate"):
        sub.add_parser(name).add_argument("session_id")
    dl = sub.add_parser("download")
    dl.add_argument("url")
    dl.add_argument("dest")
    m = sub.add_parser("message")
    m.add_argument("session_id")
    m.add_argument("text")
    a = p.parse_args(argv)
    d = Devin(org_id=a.org_id, dry_run=a.dry_run)
    show = lambda x: print(json.dumps(x, indent=2, ensure_ascii=False))  # noqa: E731
    if a.cmd == "check-auth":
        show(d.check_auth())
    elif a.cmd == "self":
        show(d.whoami())
    elif a.cmd == "create":
        urls = [d.upload(f) for f in a.attach]
        schema = json.loads(pathlib.Path(a.schema).read_text()) if a.schema else None
        s = d.create_session(pathlib.Path(a.prompt_file).read_text(), title=a.title, tags=a.tag, schema=schema,
                             attachment_urls=urls, max_acu_limit=a.max_acu, repos=a.repo)
        show({k: s.get(k) for k in ("session_id", "url", "status")})
        if a.wait:
            show(d.wait(s["session_id"], on_update=lambda u: print(f"[{time.strftime('%H:%M:%S')}] {u['state']} "
                                                                     f"{u['status_detail'] or ''}", flush=True)))
    elif a.cmd in ("status", "wait"):
        show(d.summary(a.session_id) if a.cmd == "status" else d.wait(a.session_id))
    elif a.cmd == "messages":
        show(d.messages(a.session_id))
    elif a.cmd == "attachments":
        show(d.attachments(a.session_id))
    elif a.cmd == "terminate":
        d.terminate(a.session_id)
    elif a.cmd == "download":
        print(d.download(a.url, a.dest))
    elif a.cmd == "message":
        show(d.send(a.session_id, a.text))


if __name__ == "__main__":
    try:
        main()
    except DevinError as e:
        sys.exit(f"devin: {e}")
