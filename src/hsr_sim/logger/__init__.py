import logging

from rich.console import Console
from rich.logging import RichHandler

_console = Console(stderr=True)

_handler = RichHandler(
    console=_console,
    rich_tracebacks=True,
    show_time=True,
    show_path=True,
    markup=True,
)

_handler.setFormatter(logging.Formatter("%(name)s | %(message)s"))

logging.basicConfig(level=logging.WARNING, handlers=[_handler])


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


def set_level(level: int) -> None:
    logging.getLogger().setLevel(level)
