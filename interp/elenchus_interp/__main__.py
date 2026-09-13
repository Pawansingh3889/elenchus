"""Start the service: ``uv run python -m elenchus_interp`` from ``interp/``.

INTERP_TOKEN is required, because the backend container can only reach this process when it
listens beyond localhost, and there it would otherwise read any prompt anyone sends it.
"""

import os

import uvicorn

from elenchus_interp.analysis import load
from elenchus_interp.server import create_app

MODEL = "Qwen/Qwen3-0.6B"
# Pinned, so an analysis names exactly the weights that produced it.
REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
MIN_TOKEN_LENGTH = 16


def main() -> None:
    token = os.environ.get("INTERP_TOKEN", "")
    if len(token) < MIN_TOKEN_LENGTH:
        raise SystemExit(
            f"INTERP_TOKEN must be set to at least {MIN_TOKEN_LENGTH} characters, the same "
            "value the backend is given. Generate one with: openssl rand -hex 24"
        )
    model = os.environ.get("INTERP_MODEL", MODEL)
    revision = os.environ.get("INTERP_REVISION", REVISION)
    max_prompt_tokens = int(os.environ.get("INTERP_MAX_PROMPT_TOKENS", "8192"))
    app = create_app(
        lambda: load(model, revision, max_prompt_tokens), token, model=model, revision=revision
    )
    uvicorn.run(
        app,
        host=os.environ.get("INTERP_HOST", "127.0.0.1"),
        port=int(os.environ.get("INTERP_PORT", "8765")),
    )


if __name__ == "__main__":
    main()
