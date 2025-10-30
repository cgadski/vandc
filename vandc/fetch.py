import pathlib
import sqlite3
import pandas as pd
from dataclasses import dataclass
from typing import List, Iterator
from .util import *


def _query(q, args=None):
    conn = sqlite3.connect(db_path())
    try:
        cursor = conn.execute(q, args or ())
        results = [str(row[0]) for row in cursor.fetchall()]
        return results
    finally:
        conn.close()


def _read_data(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, comment="#")
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    if "step" in df.columns:
        df = df.set_index("step")
    return df


def _read_meta(path: Path) -> dict:
    import json

    metadata = {}
    with open(path, "r") as f:
        for line in f:
            if not line.startswith("#"):
                break

            parts = line[1:].strip().split(":", 1)
            if len(parts) == 2:
                key, value = parts
                metadata[key.strip()] = value.strip()

    if "config" in metadata:
        try:
            metadata["config"] = json.loads(metadata["config"])
        except json.JSONDecodeError:
            pass

    if "run" not in metadata:
        metadata["run"] = "?"

    if "command" not in metadata:
        metadata["command"] = "?"

    return metadata


@dataclass
class Run:
    meta: dict
    config: dict
    logs: pd.DataFrame

    def __repr__(self):
        m = self.meta
        n_logs = self.logs.shape[0]
        return f"<{m['run']} ({n_logs} logs): {m['command']}>"


def fetch_path(path: Path) -> Run:
    meta = _read_meta(path)
    return Run(
        meta=meta,
        config=meta.get("config", {}),
        logs=_read_data(path),
    )


def fetch(run: Optional[str] = None) -> Run:
    if run is None:
        runs = _query("SELECT run FROM runs ORDER BY timestamp DESC LIMIT 1")
        if not runs:
            raise ValueError("No runs found in database")
        return fetch_path(run_path(runs[0]))
    return fetch_path(run_path(run))


def fetch_dir(dir: Path) -> Iterator[Run]:
    for p in dir.iterdir():
        if p.is_file() and p.suffix == ".csv":
            yield fetch_path(p)


def fetch_all(
    command_glob: Optional[str] = None, this_commit: bool = False
) -> List[Run]:
    query = ["SELECT run FROM runs WHERE 1"]
    args = []

    if command_glob:
        query += ["AND command LIKE ?"]
        args += [command_glob]

    if this_commit:
        query += ["AND git_commit = ?"]
        args += [git_commit()]

    runs = _query(" ".join(query), args)
    return [fetch_path(run_path(run)) for run in runs]


def collate_runs(runs: List[Run]) -> pd.DataFrame:
    return pd.concat(run.logs.assign(**run.meta["config"]) for run in runs)
