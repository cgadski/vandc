from typing import Optional
import json
import pandas as pd
from .writer import Writer, CsvWriter, _fetch, _meta

_writer: Optional[Writer] = None


def init(config=None):
    global _writer
    if _writer is None:
        _writer = CsvWriter(config)


def log(data: dict, step: Optional[int] = None, commit: bool = True):
    if _writer is not None:
        _writer.log(data, step, commit)


def fetch(name: str) -> pd.DataFrame:
    return _fetch(name)


def meta(name: str):
    return _meta(name)
