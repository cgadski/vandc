from typing import Optional
from typing import Iterable
from .writer import CsvWriter
from .fetch import fetch, fetch_path, fetch_dir, fetch_all, collate_runs
from qqdm import qqdm

_writer: Optional[CsvWriter] = None
_qqdm: Optional[qqdm] = None


def init(*config, cmd=None):
    global _writer
    if _writer is not None:
        close()
    _writer = CsvWriter(*config, cmd=cmd)


def progress(it: Iterable) -> qqdm:
    global _qqdm
    print()
    _qqdm = qqdm(it)
    return _qqdm


def log(data: dict, step: Optional[int] = None, commit: bool = True):
    if not _logs_enabled:
        return

    data = writer.flatten_arrays(data)

    if _qqdm is not None:
        formatted_data = {}
        for k, v in data.items():
            if isinstance(v, float):
                formatted_data[k] = f"{v:.2e}"
            else:
                formatted_data[k] = v
        _qqdm.set_infos(formatted_data)

    if _writer is not None:
        _writer.log(data, step, commit)


_logs_enabled = True


def enable_logs(enable=True):
    global _logs_enabled
    _logs_enabled = enable


class no_logs:
    def __init__(self):
        self.prev_state = _logs_enabled

    def __enter__(self):
        global _logs_enabled
        _logs_enabled = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _logs_enabled
        _logs_enabled = self.prev_state


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
