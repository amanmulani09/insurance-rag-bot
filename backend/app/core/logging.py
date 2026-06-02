import logging

from app.core.config import LOG_LEVEL


def configure_logging() -> None:
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    for logger_name in ("httpx", "httpcore", "huggingface_hub", "sentence_transformers"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
