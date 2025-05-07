import json
import csv
import os
from typing import List, Optional, Tuple, Dict, Any
import pandas as pd
import torch as t
import human_id
import subprocess
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path

VANDC_DIR = ".vandc"


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
        os.makedirs(VANDC_DIR, exist_ok=True)
        self.csv_path = Path(VANDC_DIR) / f"{self.run}.csv"

        self.metadata = {
            "run": self.run,
            "time": datetime.now().isoformat(),
            "command": _get_command(),
            "git_commit": _get_git_commit(),
            "config": json.dumps(vars(config))
            if hasattr(config, "__dict__")
            else str(config),
        }

        self.step = 0
        self.csv_file = None
        self.writer = None

        logger.opt(raw=True, colors=True).info(
            f"Starting run: <green>{self.run}</green> in {self.csv_path}\n"
        )

        with open(self.csv_path, "w", newline="") as f:
            for key, value in self.metadata.items():
                f.write(f"# {key}: {value}\n")

        self.csv_file = open(self.csv_path, "a")

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

    def __del__(self):
        self.close()


def _fetch(name: str) -> pd.DataFrame:
    csv_path = os.path.join(VANDC_DIR, f"{name}.csv")
    df = pd.read_csv(csv_path, comment="#")
    if "step" in df.columns:
        df = df.set_index("step")

    return df


def _meta(name: str) -> dict:
    csv_path = os.path.join(VANDC_DIR, f"{name}.csv")

    metadata = {}
    with open(csv_path, "r") as f:
        for line in f:
            if not line.startswith("#"):
                break

            parts = line[1:].strip().split(":", 1)
            if len(parts) == 2:
                key, value = parts
                metadata[key.strip()] = value.strip()

    return metadata
