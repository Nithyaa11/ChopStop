"""Start the API for local development on http://127.0.0.1:8010 (auto-reload).

Run from backend/:  uv run python -m scripts.dev
Port 8010 is the project's standard dev port (8000/8001 are used by other apps on
this machine). Override with API_PORT in .env if ever needed.
Binds to 127.0.0.1 only, so the dev API is not reachable from the network.
"""

import uvicorn

from app.core.config import get_settings


def main() -> None:
    port = get_settings().api_port  # 8010 unless API_PORT is set in .env
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)


if __name__ == "__main__":
    main()
