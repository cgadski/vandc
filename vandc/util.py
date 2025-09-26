import functools
import subprocess
from pathlib import Path
import sys
from typing import Optional


@functools.lru_cache(maxsize=1)
def git_root() -> Optional[Path]:
    try:
        root = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
            )
            .decode("ascii")
            .strip()
        )
        return Path(root)
    except:
        return None


def vandc_dir():
    if root := git_root():
        return root / ".vandc"
    else:
        return Path(".vandc")


def run_path(run: str):
    return vandc_dir() / f"{run}.csv"


def db_path():
    return vandc_dir() / "db.sqlite"


def git_commit():
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode("ascii")
            .strip()
        )
    except:
        return None


def _to_relative_path(root: Path, s: str) -> str:
    try:
        path = Path(s)
        if path.is_absolute() and str(path).startswith(str(root)):
            return str(path.relative_to(root))
        return s
    except:
        return s


def command_relative():
    root = git_root()
    if root:
        return " ".join(_to_relative_path(root, s) for s in sys.argv)
    else:
        return " ".join(sys.argv)
