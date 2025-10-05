import json
import csv
import os
import sqlite3
from typing import Optional
import human_id
from datetime import datetime, timezone
from loguru import logger
import numpy as np
import torch
from .util import *


def flatten_arrays(d):
    result = {}
    for k, v in d.items():
        if isinstance(v, np.ndarray):
            result[k] = v.item()
        elif isinstance(v, torch.Tensor):
            result[k] = v.item()
        else:
            result[k] = v
    return result


class CsvWriter:
    config: dict
    conn: Optional[sqlite3.Connection]
    cmd: str

    def __init__(
        self,
        *config,
        cmd: Optional[str] = None,
    ):
        self.run = human_id.generate_id()
        os.makedirs(vandc_dir(), exist_ok=True)
        self.csv_path = vandc_dir() / f"{self.run}.csv"

        self.config = {}
        for cfg in config:
            if cfg is not None:
                if isinstance(cfg, dict):
                    self.config.update(cfg)
                else:
                    self.config.update(vars(cfg))

        if cmd is not None:
            self.cmd = cmd
        else:
            self.cmd = command_relative()

        self.step = 0
        self.writer = None

        self.conn = sqlite3.connect(db_path())
        self._ensure_tables()

        logger.opt(raw=True, colors=True).info(
            f"Starting run: <green>{self.run}</green>\n"
        )

        if self.config:
            config_lines = [f"  {key}: {value}" for key, value in self.config.items()]
            config_str = "\n".join(config_lines)
            logger.opt(raw=True, colors=True).info(
                f"Config:\n<blue>{config_str}</blue>\n"
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

        self.conn.commit()

    def _insert_run(self):
        metadata = {
            "run": self.run,
            "time": datetime.now(timezone.utc).isoformat(),
            "command": self.cmd,
            "git_commit": git_commit(),
            "config": json.dumps(self.config),
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
        self.conn.executemany(
            "INSERT INTO config (run, key, value) VALUES (?, ?, ?)",
            ((self.run, key, str(value)) for key, value in self.config.items()),
        )

        self.conn.commit()

        with open(self.csv_path, "w") as f:
            for key, value in metadata.items():
                f.write(f"# {key}: {value}\n")

    def log(self, d: dict, step: Optional[int], commit: bool):
        if step is not None:
            self.step = step

        if d.get("step") is None:
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
