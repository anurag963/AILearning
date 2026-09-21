"""Starts pytest for the dashboard and for run_all.py, and tracks the one running job.

Only one job runs at a time: two at once would share Groq's tokens-per-minute
limit and fight over it. Jobs are launched as an argument list, never through a
shell, and the server only ever passes node ids that pytest itself reported.
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAMEWORK = HERE.parent
DATA = HERE / "data"

# Matched against the failure text: deepeval wraps a Groq 429 in a tenacity RetryError.
RATE_LIMIT = "RetryError|RateLimitError|Error code: 429|rate_limit_exceeded"


def pytest_command(ids=(), retries: int = 5, delay: int = 30, extra=()) -> list[str]:
    """Rate-limited tests are retried after a pause; real metric failures are not."""
    return [
        sys.executable, "-m", "pytest",
        "--reruns", str(retries), "--reruns-delay", str(delay),
        "--only-rerun", RATE_LIMIT,
        *extra, *ids,
    ]


# ---------------------------------------------------------------------------
# Catalog: every scenario pytest can run, so the dashboard can show (and run)
# ones that have never produced a result.
# ---------------------------------------------------------------------------
_catalog_lock = threading.Lock()
_catalog: dict = {"sig": None, "items": []}


def _source_signature():
    files = [*FRAMEWORK.glob("tests/**/*.py"), *FRAMEWORK.glob("dataset/*.py"), FRAMEWORK / "metrics_catalog.py"]
    return tuple(sorted((str(p), p.stat().st_mtime) for p in files if p.exists()))


def catalog() -> list[dict]:
    """[{id, file, test, param, markers}], in pytest's run order. Re-collected when a test or dataset file changes."""
    with _catalog_lock:
        sig = _source_signature()
        if sig != _catalog["sig"]:
            DATA.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=DATA, suffix=".json", delete=False) as tmp:
                out = Path(tmp.name)
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
                    cwd=FRAMEWORK, env={**os.environ, "DASHBOARD_CATALOG_OUT": str(out)},
                    capture_output=True, text=True, timeout=180,
                )
                if not out.read_text():
                    raise RuntimeError("pytest could not collect the tests:\n" + (proc.stdout + proc.stderr)[-1500:])
                _catalog.update(sig=sig, items=json.loads(out.read_text()))
            finally:
                out.unlink(missing_ok=True)
        return _catalog["items"]


# ---------------------------------------------------------------------------
# The one running job
# ---------------------------------------------------------------------------
class Busy(Exception):
    pass


ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


class Runner:
    def __init__(self):
        self._lock = threading.Lock()
        self._proc = None
        self._log = None
        self._job: dict = {}

    def _alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start(self, ids: list[str] | None) -> None:
        """ids=None runs everything."""
        with self._lock:
            if self._alive():
                raise Busy()
            if self._log:
                self._log.close()
            DATA.mkdir(parents=True, exist_ok=True)
            self._log = open(DATA / "job.log", "wb")
            # A server started in the background can hand its children an "ignore SIGINT" setting, which would make
            # Stop do nothing, so restore the default handler first. After an interrupt, pytest has already saved its
            # results, but in-flight network threads can keep the interpreter alive for a minute at exit: leave now.
            boot = (
                "import os,signal,sys;signal.signal(signal.SIGINT,signal.default_int_handler);"
                "import pytest;code=int(pytest.main());"
                "sys.stdout.flush();sys.stderr.flush();"
                "os._exit(code) if code==2 else sys.exit(code)"
            )
            cmd = pytest_command(ids or ())
            self._proc = subprocess.Popen(
                [cmd[0], "-c", boot, *cmd[3:]],
                cwd=FRAMEWORK, stdout=self._log, stderr=subprocess.STDOUT,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
                start_new_session=True,  # own process group, so Stop can signal pytest and its children
            )
            self._job = {"started": time.time(), "ids": list(ids) if ids else None, "stops": 0}

    def stop(self) -> bool:
        """First call asks pytest to finish gracefully (it saves what it has); a second kills it."""
        with self._lock:
            if not self._alive():
                return False
            self._job["stops"] += 1
            sig = signal.SIGINT if self._job["stops"] == 1 else signal.SIGKILL
            os.killpg(self._proc.pid, sig)
            return True

    def _pending(self, planned, recorded_since):
        done = recorded_since(self._job["started"])
        return [i for i in planned if i not in done]

    def status(self, all_ids: list[str], recorded_since) -> dict:
        """`recorded_since(started)` returns the ids this job has already saved; the rest are pending."""
        with self._lock:
            if self._proc is None:
                return {"running": False}
            running = self._alive()
            planned = self._job["ids"] if self._job["ids"] is not None else all_ids
            tail = ""
            try:
                raw = (DATA / "job.log").read_bytes()[-6000:].decode("utf-8", "replace")
                tail = "\n".join(ANSI.sub("", raw).replace("\r", "\n").splitlines()[-40:])
            except OSError:
                pass
            return {
                "running": running,
                "stopping": running and self._job["stops"] > 0,
                "started": self._job["started"],
                "all": self._job["ids"] is None,
                "count": len(planned),
                "pending": self._pending(planned, recorded_since) if running else [],
                "exit_code": None if running else self._proc.returncode,
                "log": tail,
            }


runner = Runner()
