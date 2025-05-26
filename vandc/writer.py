import json
import csv
import os
import sqlite3
from typing import List, Optional, Tuple, Dict, Any
import pandas as pd
import human_id
import subprocess
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path
import functools


@functools.lru_cache(maxsize=1)
def vandc_dir():
    git_root = _get_git_root()
    if git_root:
        return git_root / ".vandc"
    else:
        return Path(".vandc")


def db_path():
    return vandc_dir() / "db.sqlite"


def _get_git_commit():
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


def _get_git_root():
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


def _to_relative_path(root: Path, s: str) -> str:
    try:
        path = Path(s)
        if path.is_absolute() and str(path).startswith(str(root)):
            return str(path.relative_to(root))
        return s
    except:
        return s


def _get_command():
    root = _get_git_root()
    if root:
        return " ".join(_to_relative_path(root, s) for s in sys.argv)
    else:
        return " ".join(sys.argv)


class Writer:
    run: str

    def log(self, d: dict, step: Optional[int], commit: bool):
        pass

    def commit(self):
        pass


class CsvWriter(Writer):
    def __init__(
        self,
        config,
        filename: Optional[str] = None,
    ):
        self.run = human_id.generate_id()
        os.makedirs(vandc_dir(), exist_ok=True)
        self.csv_path = vandc_dir() / f"{self.run}.csv"

        self.config = config

        self.step = 0
        self.csv_file = None
        self.writer = None

        self.conn = sqlite3.connect(db_path())
        self.conn.autocommit = True
        self._ensure_tables()

        logger.opt(raw=True, colors=True).info(
            f"Starting run: <green>{self.run}</green>\n"
        )

        self._insert_run()
        self.csv_file = open(self.csv_path, "a")

    def _ensure_tables(self):
        assert self.conn
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run TEXT PRIMARY KEY,
            command, timestamp, git_commit, config
        )
        """)

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS config (
            run REFERENCES runs(run),
            key, value,
            PRIMARY KEY (run, key)
        )
        """)

    def _insert_run(self):
        metadata = {
            "run": self.run,
            "time": datetime.now().isoformat(),
            "command": _get_command(),
            "git_commit": _get_git_commit(),
            "config": json.dumps(vars(self.config)),
        }

        assert self.conn

        self.conn.execute(
            "INSERT INTO runs (run, command, timestamp, git_commit, config) VALUES (?, ?, ?, ?, ?)",
            (
                self.run,
                metadata["command"],
                metadata["time"],
                metadata["git_commit"],
                metadata["config"],
            ),
        )
        config_items = vars(self.config).items()
        self.conn.executemany(
            "INSERT INTO config (run, key, value) VALUES (?, ?, ?)",
            ((self.run, key, str(value)) for key, value in config_items),
        )

        with open(self.csv_path, "w") as f:
            for key, value in metadata.items():
                f.write(f"# {key}: {value}\n")

    def log(self, d: dict, step: Optional[int], commit: bool):
        if step is not None:
            self.step = step

        d["step"] = self.step

        if self.writer is None:
            self.writer = csv.DictWriter(self.csv_file, fieldnames=d.keys())  # pyright: ignore
            self.writer.writeheader()

        self.writer.writerow(d)

        if commit:
            self.step += 1

    def commit(self):
        if self.csv_file:
            self.csv_file.flush()

    def __enter__(self):
        return self

    def close(self):
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None

        if self.conn:
            self.conn.close()
            self.conn = None

    def __del__(self):
        self.close()


def _query(q, args=None):
    """Execute a SQL query and return the first column of results as a list of strings"""
    conn = sqlite3.connect(db_path())
    try:
        cursor = conn.execute(q, args or ())
        results = [str(row[0]) for row in cursor.fetchall()]
        return results
    finally:
        conn.close()


def _fetch(run: str) -> pd.DataFrame:
    df = pd.read_csv(vandc_dir() / f"{run}.csv", comment="#")
    if "step" in df.columns:
        df = df.set_index("step")
    return df


def _meta(name: str) -> dict:
    metadata = {}
    with open(vandc_dir() / f"{name}.csv", "r") as f:
        for line in f:
            if not line.startswith("#"):
                break

            parts = line[1:].strip().split(":", 1)
            if len(parts) == 2:
                key, value = parts
                metadata[key.strip()] = value.strip()

    return metadata


def _describe(name: str):
    meta = _meta(name)
    print(f"{name}: {meta['time']} on commit {meta['git_commit']}")
    print(f"$ {meta['command']}")


def _get_run(run) -> str:
    if run is None:
        runs = _query("SELECT run FROM runs ORDER BY timestamp DESC LIMIT 1")
        if not runs:
            raise ValueError("No runs found in database")
        return runs[0]
    return run


def describe(run=None):
    _describe(_get_run(run))


def fetch(run=None):
    return _fetch(_get_run(run))


def meta(run=None):
    return _meta(_get_run(run))
