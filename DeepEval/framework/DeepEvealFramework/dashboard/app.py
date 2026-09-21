"""Local dashboard for the DeepEval results in data/runs/.

Run:  python dashboard/app.py      then open http://127.0.0.1:8765
Standard library only, so it runs in the same venv as the tests.

The page can also start test runs (POST /api/run). That endpoint is guarded so
only this page can call it: a JSON content type (which browsers will not send
cross-site without a preflight we never answer), an Origin and Host check
(against DNS rebinding), and only node ids that pytest itself reported.
"""
import json
import os
import re
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import report  # noqa: E402  (dashboard/report.py)
from runner import Busy, catalog, runner as job_runner  # noqa: E402  (dashboard/runner.py)

RUNS_DIR = HERE / "data" / "runs"
RUN_ID = re.compile(r"^\d{8}-\d{6}$")  # also stops path traversal
MAX_BODY = 200_000


_summaries = {}  # path -> (mtime, summary): the UI polls during a run, so don't re-parse every file each time


def list_runs():
    runs = []
    for path in sorted(RUNS_DIR.glob("*.json"), reverse=True):  # newest first
        try:
            mtime = path.stat().st_mtime
            cached = _summaries.get(path)
            if not cached or cached[0] != mtime:
                run = json.loads(path.read_text(encoding="utf-8"))
                cached = _summaries[path] = (mtime, {k: v for k, v in run.items() if k != "tests"})
        except (OSError, ValueError):
            continue  # a corrupt file must not break the list
        runs.append(cached[1])
    return runs


def scenarios():
    """Every scenario pytest can run, with its most recent result (or None if it never ran).

    If the most recent attempt errored (the judge never answered), `last_real`
    carries the last actual verdict so the card can still show it.
    """
    latest, last_real = {}, {}
    for run in report.load_runs():  # oldest first, so later runs overwrite
        for t in run["tests"]:
            entry = {**t, "run": run["id"], "when": run["started"]}
            latest[t["id"]] = entry
            if t["outcome"] != "error":
                last_real[t["id"]] = entry
    out = []
    for item in catalog():
        cur = latest.get(item["id"])
        real = None
        if cur and cur["outcome"] == "error" and item["id"] in last_real:
            r = last_real[item["id"]]
            ms = report.metrics_of(r)
            real = {"outcome": r["outcome"], "score": ms[0].get("score") if ms else None, "when": r["when"], "run": r["run"]}
        out.append({**item, "latest": cur, "last_real": real})
    return out


def recorded_since(started):
    """Ids the running job has already saved, from the newest run file that began after it."""
    for run in reversed(report.load_runs()):
        try:
            if datetime.fromisoformat(run["started"]).timestamp() >= started - 5:
                return {t["id"] for t in run["tests"]}
        except (KeyError, ValueError):
            continue
        break
    return set()


def job_state():
    from runner import _catalog  # already collected whenever a job exists, so this never blocks
    return job_runner.status([c["id"] for c in _catalog["items"]], recorded_since)


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, payload):
        self._send(status, json.dumps(payload).encode(), "application/json")

    # ---- GET ----
    def do_GET(self):
        url = urlsplit(self.path)
        path = url.path
        if path == "/report":
            which = parse_qs(url.query).get("run", ["latest"])[0]
            if which not in ("latest", "combined") and not RUN_ID.match(which):
                return self._json(400, {"error": "Invalid run id."})
            page = report.render(which)
            if page is None:
                return self._send(404, b"No matching run yet. Run the tests first.", "text/plain; charset=utf-8")
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            if parse_qs(url.query).get("download"):
                self.send_header("Content-Disposition", f'attachment; filename="report-{which}.html"')
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/":
            return self._send(
                200, (HERE / "static" / "index.html").read_bytes(), "text/html; charset=utf-8"
            )
        if path == "/api/runs":
            return self._json(200, list_runs())
        if path == "/api/scenarios":
            try:
                return self._json(200, scenarios())
            except (RuntimeError, OSError) as e:
                return self._json(500, {"error": str(e)})
        if path == "/api/job":
            return self._json(200, job_state())
        match = re.fullmatch(r"/api/runs/([^/]+)", path)
        if match:
            if not RUN_ID.match(match.group(1)):
                return self._json(400, {"error": "Invalid run id."})
            file = RUNS_DIR / f"{match.group(1)}.json"
            if not file.is_file():
                return self._json(404, {"error": "Run not found."})
            return self._send(200, file.read_bytes(), "application/json")
        self._json(404, {"error": "Not found."})

    # ---- POST ----
    def _guard(self):
        """Returns the parsed JSON body, or None after having sent an error."""
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host") not in hosts:
            self._json(403, {"error": "Forbidden host."})
        elif self.headers.get("Origin") not in (None, *(f"http://{h}" for h in hosts)):
            self._json(403, {"error": "Forbidden origin."})
        elif not self.headers.get("Content-Type", "").startswith("application/json"):
            self._json(415, {"error": "Send application/json."})
        else:
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 <= length <= MAX_BODY:
                    return self._json(413, {"error": "Body too large."})
                data = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                return self._json(400, {"error": "Invalid JSON."})
            if isinstance(data, dict):
                return data
            self._json(400, {"error": "Expected a JSON object."})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in ("/api/run", "/api/stop"):
            return self._json(404, {"error": "Not found."})
        body = self._guard()
        if body is None:
            return
        if path == "/api/stop":
            return self._json(200, {"stopped": job_runner.stop()})

        try:
            order = {c["id"]: i for i, c in enumerate(catalog())}
        except RuntimeError as e:
            return self._json(500, {"error": str(e)})
        if body.get("all") is True:
            ids = None
        else:
            ids = body.get("ids")
            if not (isinstance(ids, list) and ids and all(isinstance(i, str) and i in order for i in ids)):
                return self._json(400, {"error": "ids must be a non-empty list of known scenario ids."})
            ids = sorted(set(ids), key=order.get)  # catalog order, so progress reads top to bottom
        try:
            job_runner.start(ids)
        except Busy:
            return self._json(409, {"error": "A run is already in progress."})
        self._json(202, job_state())

    def log_message(self, *args):
        pass  # keep the terminal quiet


def make_server(port):
    # 127.0.0.1 = this machine only; results contain bot replies and are not exposed to the network
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8765))
    print(f"Open http://127.0.0.1:{port}  (Ctrl+C to stop)")
    make_server(port).serve_forever()
