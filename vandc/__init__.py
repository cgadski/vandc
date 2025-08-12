from typing import Optional
import json
from typing import Iterable
from .writer import CsvWriter, fetch, meta, describe
import qqdm as og_tqdm

_writer: Optional[CsvWriter] = None
_qqdm: Optional[og_tqdm.qqdm] = None


def init(*config, cmd=None):
    global _writer
    if _writer is not None:
        close()
    _writer = CsvWriter(*config, cmd=cmd)


def progress(it: Iterable) -> og_tqdm.qqdm:
    global _qqdm
    print()
    _qqdm = og_tqdm.qqdm(it)
    return _qqdm


def log(data: dict, step: Optional[int] = None, commit: bool = True):
    if _writer is not None:
        if _qqdm is not None:
            _qqdm.set_infos(data)
        _writer.log(data, step, commit)


def commit():
    if _writer is not None:
        _writer.commit()


def close():
    global _writer, _qqdm
    if _writer is not None:
        _writer.close()
        _writer = None

    if _qqdm is not None:
        _qqdm.close()
        _qqdm = None


def run_name() -> str:
    if _writer is not None:
        return _writer.run
    raise RuntimeError("Run not initialized")
