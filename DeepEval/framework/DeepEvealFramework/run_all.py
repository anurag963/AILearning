"""Run the whole suite in one pytest session and watch the report live.

    python run_all.py                  # every test, dashboard opens in your browser
    python run_all.py -m safety        # anything unrecognised goes straight to pytest
    python run_all.py --no-dashboard   # tests only

Groq's free tier caps tokens per minute, so a full run hits rate limits. Tests
that fail with one are retried after a pause; real metric failures are not.
"""
import argparse
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "dashboard"))
import app  # noqa: E402  (dashboard/app.py)
from runner import pytest_command  # noqa: E402  (dashboard/runner.py)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-dashboard", action="store_true", help="run the tests without serving the report")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--retries", type=int, default=5, help="retries per rate-limited test (default 5)")
    ap.add_argument("--retry-delay", type=int, default=30, help="seconds between retries (default 30)")
    args, pytest_args = ap.parse_known_args()

    url = f"http://127.0.0.1:{args.port}/"
    serving = False
    if not args.no_dashboard:
        try:
            server = app.make_server(args.port)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            serving = True
        except OSError:
            print(f"Port {args.port} is busy; assuming the dashboard is already running there.")
        webbrowser.open(url)
        print(f"Live report: {url}\n")

    cmd = pytest_command(retries=args.retries, delay=args.retry_delay, extra=pytest_args)
    proc = subprocess.Popen(cmd, cwd=HERE)
    try:
        code = proc.wait()
    except KeyboardInterrupt:  # the child got the same Ctrl+C and is saving its results
        code = proc.wait()

    newest = sorted(app.RUNS_DIR.glob("*.json"))[-1:] or None
    if newest:
        print(f"\nRun saved: {newest[0].name}")
        # Shareable single-file reports: this run, and every run merged (latest real verdict per test).
        app.report.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        for which, name in (("latest", newest[0].stem), ("combined", "combined")):
            path = app.report.REPORTS_DIR / f"report-{name}.html"
            path.write_text(app.report.render(which), encoding="utf-8")
            print(f"Report: {path}")
    if serving:
        print(f"Report stays up at {url}  (Ctrl+C to stop)")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
    return code


if __name__ == "__main__":
    sys.exit(main())
