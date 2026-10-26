import logging
import sys

from app.config import settings


def setup_logging() -> None:
    """Configura o logging da aplicação (stdout, formato único para app e uvicorn)."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = True

    # SQL só aparece se pedirem DEBUG explicitamente
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
