"""Local web UI for exploring a RAG pipeline over the files in data/.

Run:  python app.py      then open http://127.0.0.1:8001
"""
import os
import sys
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

from rag import DATA_DIR, EMBEDDING_MODEL, MODES, STRATEGIES, Explorer

HERE = Path(__file__).parent
MAX_QUERY_CHARS = 1000

DEFAULTS = {"strategy": "section", "chunk_size": 500, "overlap": 50, "mode": "hybrid", "top_k": 4}
INT_BOUNDS = {"chunk_size": (100, 3000), "overlap": (0, 1000), "top_k": (1, 20)}

print("Loading embedding model (first run downloads ~80 MB)...")
try:
    explorer = Explorer()
    explorer.index_for(DEFAULTS["strategy"], DEFAULTS["chunk_size"], DEFAULTS["overlap"])  # fail fast
except (FileNotFoundError, OSError) as e:
    sys.exit(f"Error: {e}")


def error(message, status):
    return JSONResponse({"error": message}, status_code=status)


def parse_settings(source):
    """Validate chunking/retrieval settings from a query string or JSON body. Raises ValueError."""
    settings = {}
    for key, default in DEFAULTS.items():
        value = source.get(key, default)
        if key in INT_BOUNDS:
            low, high = INT_BOUNDS[key]
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise ValueError(f"{key} must be an integer.") from None
            if not low <= value <= high:
                raise ValueError(f"{key} must be between {low} and {high}.")
        elif value not in (STRATEGIES if key == "strategy" else MODES):
            raise ValueError(f"Unknown {key}: {value!r}.")
        settings[key] = value
    if settings["overlap"] >= settings["chunk_size"]:
        raise ValueError("overlap must be smaller than chunk_size.")
    return settings


async def read_json(request):
    """Return the JSON body as a dict, or None if the request isn't a valid JSON object."""
    # Requiring this header forces browsers to CORS-preflight cross-site requests (which
    # we don't allow), so other websites can't make your browser call this API.
    if not request.headers.get("content-type", "").startswith("application/json"):
        return None
    try:
        data = await request.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


async def index(request):
    return FileResponse(HERE / "static" / "index.html")


async def corpus(request):
    try:
        settings = parse_settings(request.query_params)
    except ValueError as e:
        return error(str(e), 400)

    idx = await run_in_threadpool(
        explorer.index_for, settings["strategy"], settings["chunk_size"], settings["overlap"]
    )
    counts = {}
    for c in idx.chunks:
        counts[c.doc] = counts.get(c.doc, 0) + 1
    return JSONResponse(
        {
            "settings": settings,
            "docs": [{"path": d, "chunks": n} for d, n in counts.items()],
            "chunks": [
                {
                    "id": c.id,
                    "doc": c.doc,
                    "heading": c.heading,
                    "text": c.text,
                    "x": float(xy[0]),
                    "y": float(xy[1]),
                }
                for c, xy in zip(idx.chunks, idx.coords)
            ],
            "embedding": {"model": EMBEDDING_MODEL, "dim": int(idx.vectors.shape[1])},
            "llm": {"model": explorer.model, "configured": explorer.client is not None},
            "data_dir": str(DATA_DIR),
        }
    )


async def query(request):
    data = await read_json(request)
    if data is None:
        return error("Invalid request.", 400)

    text = data.get("query")
    if not isinstance(text, str) or not text.strip():
        return error("Query is empty.", 400)
    if len(text) > MAX_QUERY_CHARS:
        return error(f"Query is too long (max {MAX_QUERY_CHARS} characters).", 400)
    try:
        settings = parse_settings(data)
    except ValueError as e:
        return error(str(e), 400)

    # embedding + the LLM call are blocking, so keep them off the event loop
    result = await run_in_threadpool(
        explorer.query, text.strip(), settings, data.get("generate") is True
    )
    return JSONResponse(result)


app = Starlette(
    routes=[
        Route("/", index),
        Route("/api/corpus", corpus),
        Route("/api/query", query, methods=["POST"]),
    ]
)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    print(f"Open http://127.0.0.1:{port}  (Ctrl+C to stop)")
    # 127.0.0.1 = this machine only; the explorer isn't exposed to your network
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
