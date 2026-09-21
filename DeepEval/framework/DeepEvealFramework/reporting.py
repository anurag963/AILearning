"""Records every test result, with full metric detail, for the dashboard.

deepeval's own `.latest_test_run.json` drops the reason and message for any
case that errors (a Groq 429, for instance), and is overwritten on every run.
This keeps one JSON file per run in dashboard/data/runs/.

How it works:
  - `install()` wraps `deepeval.assert_test` to note the test case, and wraps
    the executors it calls internally to capture the per-metric results
    (score, reason, error). Reading the metric objects instead does not work:
    deepeval evaluates copies of them.
  - `pytest_runtest_makereport` attaches that note to the pytest report as a
    user property, which pytest-xdist forwards to the controller process.
  - `pytest_runtest_logreport` collects reports and rewrites the run file after
    every test (status "running"), so the dashboard is live during a long run
    and a Ctrl+C loses nothing. `pytest_sessionfinish` marks it finished.
  - Attempts that pytest-rerunfailures is about to retry are not recorded; only
    the final attempt of each test is.
conftest.py registers this module as a plugin and calls `install()`.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

import pytest

RUNS_DIR = Path(__file__).resolve().parent / "dashboard" / "data" / "runs"
PROP = "deepeval_calls"

_calls: list[dict] = []  # assert_test calls made by the test currently running
_RECORDS: list[dict] = []  # one entry per finished test; the run file is rewritten from this
_STARTED = time.time()
_last_results: list = []  # MetricData from the most recent deepeval executor call


def _jsonable(value):
    """Best-effort conversion so an odd metric attribute never breaks a run."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)


def _describe_case(tc) -> dict:
    turns = getattr(tc, "turns", None)
    if turns is not None:  # ConversationalTestCase
        return {
            "kind": "conversation",
            "turns": [{"role": t.role, "content": t.content} for t in turns],
        }
    return {
        "kind": "single",
        "input": tc.input,
        "actual_output": tc.actual_output,
        "expected_output": tc.expected_output,
        "context": tc.context,
        "retrieval_context": tc.retrieval_context,
    }


def _describe_metric(md) -> dict:
    """md is a deepeval MetricData."""
    return {
        "name": md.name,
        "score": _jsonable(md.score),
        "threshold": _jsonable(md.threshold),
        "success": _jsonable(md.success),
        "reason": md.reason,
        "error": md.error,
        "logs": md.verbose_logs,
        "judge": md.evaluation_model,
    }


def install() -> None:
    """Wrap deepeval.assert_test. Must run before test modules import it."""
    import sys

    import deepeval

    if getattr(deepeval.assert_test, "_recording", False):
        return
    original = deepeval.assert_test
    module = sys.modules[original.__module__]  # assert_test looks the executors up here

    def remember(results):
        if results:
            _last_results[:] = list(results[0].metrics_data or [])
        return results

    sync_executor = module.execute_test_cases
    async_executor = module.a_execute_test_cases

    def execute_test_cases(*args, **kwargs):
        return remember(sync_executor(*args, **kwargs))

    async def a_execute_test_cases(*args, **kwargs):
        return remember(await async_executor(*args, **kwargs))

    module.execute_test_cases = execute_test_cases
    module.a_execute_test_cases = a_execute_test_cases

    def recording_assert_test(*args, **kwargs):
        test_case = args[0] if args else kwargs.get("test_case")
        _last_results.clear()
        try:
            return original(*args, **kwargs)
        finally:
            try:
                _calls.append(
                    {
                        "case": _describe_case(test_case),
                        "metrics": [_describe_metric(md) for md in _last_results],
                    }
                )
            except Exception as e:  # recording must never change a test's outcome
                _calls.append({"case": {}, "metrics": [], "record_error": repr(e)})

    recording_assert_test._recording = True
    deepeval.assert_test = recording_assert_test


# ---------------------------------------------------------------------------
# pytest hooks (registered as a plugin by conftest.py)
# ---------------------------------------------------------------------------
def _markers(item) -> list[str]:
    return sorted({m.name for m in item.iter_markers()} - {"parametrize", "usefixtures", "filterwarnings"})


def pytest_runtest_setup(item):
    _calls.clear()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if call.when != "call":
        return
    markers = _markers(item)
    report.user_properties.append(
        (
            PROP,
            {
                "calls": list(_calls),
                "exc_type": call.excinfo.typename if call.excinfo else None,
                "markers": markers,
            },
        )
    )


def pytest_runtest_logreport(report):
    if report.outcome == "rerun":  # pytest-rerunfailures: this attempt will be retried
        return
    # Fixtures that skip or raise never reach the "call" phase.
    if report.when == "setup" and (report.failed or report.skipped):
        outcome = "error" if report.failed else "skipped"
        extra = {}
    elif report.when == "call":
        extra = dict(report.user_properties).get(PROP, {})
        if report.passed:
            outcome = "passed"
        elif report.skipped:
            outcome = "skipped"
        else:  # deepeval raises AssertionError for a failed metric; anything else is infra
            outcome = "failed" if extra.get("exc_type") == "AssertionError" else "error"
    else:
        return

    file, _, rest = report.nodeid.partition("::")
    name, _, param = rest.partition("[")
    _RECORDS.append(
        {
            "id": report.nodeid,
            "file": Path(file).name,
            "test": name,
            "param": param[:-1] if param.endswith("]") else "",
            "outcome": outcome,
            "duration": round(report.duration, 2),
            "markers": extra.get("markers", []),
            "calls": extra.get("calls", []),
            "message": report.longreprtext if outcome in ("failed", "error", "skipped") else "",
        }
    )
    _write("running")


_config = {}  # set by pytest_sessionstart; read when writing


def pytest_sessionstart(session):
    _config["args"] = list(session.config.invocation_params.args)
    _config["worker"] = hasattr(session.config, "workerinput")


def pytest_collection_finish(session):
    _config["expected"] = len(session.items)  # lets the dashboard show "42 of 190"
    out = os.getenv("DASHBOARD_CATALOG_OUT")  # the dashboard asks for the full scenario list this way
    if out:
        catalog = []
        for item in session.items:
            file, _, rest = item.nodeid.partition("::")
            name, _, param = rest.partition("[")
            catalog.append({
                "id": item.nodeid, "file": Path(file).name, "test": name,
                "param": param[:-1] if param.endswith("]") else "", "markers": _markers(item),
            })
        Path(out).write_text(json.dumps(catalog))


def _write(status: str) -> None:
    if _config.get("worker") or not _RECORDS:
        return  # xdist workers report to the controller, which writes the file
    from llm_provider.groq_judge import JUDGE_MODEL

    try:
        from chatbot import DEFAULT_MODEL  # Chatbot/chatbot.py, on sys.path via targets/
    except ImportError:
        DEFAULT_MODEL = ""
    started = datetime.fromtimestamp(_STARTED)
    counts = {k: sum(1 for r in _RECORDS if r["outcome"] == k) for k in ("passed", "failed", "error", "skipped")}
    run = {
        "id": started.strftime("%Y%m%d-%H%M%S"),
        "status": status,  # "running" until the session ends
        "updated": time.time(),
        "started": started.isoformat(timespec="seconds"),
        "duration": round(time.time() - _STARTED, 1),
        "judge_model": JUDGE_MODEL,
        "bot_model": os.getenv("GROQ_MODEL", DEFAULT_MODEL),
        "args": _config.get("args", []),
        "expected": _config.get("expected", len(_RECORDS)),
        "counts": counts,
        "total": len(_RECORDS),
        "tests": _RECORDS,
    }
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    target = RUNS_DIR / f"{run['id']}.json"
    tmp = target.with_suffix(".tmp")  # write-then-rename so the dashboard never reads half a file
    tmp.write_text(json.dumps(run, indent=1, ensure_ascii=False))
    tmp.replace(target)


def pytest_sessionfinish(session, exitstatus):
    _write("finished")
