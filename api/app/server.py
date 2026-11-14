"""Entry point: python -m app.server (reads .env if present)."""
import logging
import os

import uvicorn


def _load_dotenv(path: str = ".env") -> None:
    # Like node --env-file: real environment variables win over the file.
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


if __name__ == "__main__":
    _load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    from .main import create_app

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), log_level="warning", reload=False)
