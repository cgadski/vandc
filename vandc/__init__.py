from typing import Optional
import json
from .writer import Writer, CsvWriter, fetch, meta, describe
from .list_runs import list_runs

_writer: Optional[Writer] = None


def init(config=None):
    global _writer
    if _writer is None:
        _writer = CsvWriter(config)


def log(data: dict, step: Optional[int] = None, commit: bool = True):
    if _writer is not None:
        _writer.log(data, step, commit)
        _writer.commit()


def log_fast(data: dict, step: Optional[int] = None, commit: bool = True):
    if _writer is not None:
        _writer.log(data, step, commit)


def commit():
    if _writer is not None:
        _writer.commit()


def close():
    global _writer
    _writer = None


def run_name() -> str:
    if _writer is not None:
        return _writer.run
    raise RuntimeError("Run not initialized")
