import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import questionary
from datetime import datetime, timezone
from vandc.util import db_path, vandc_dir

import pyperclip


def get_runs_by_script(script_name: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path())
    try:
        if script_name:
            cursor = conn.execute(
                """
                SELECT run, command, timestamp, git_commit, config
                FROM runs
                WHERE command LIKE ?
                ORDER BY timestamp DESC
                LIMIT 20
                """,
                (f"{script_name}%",),
            )
        else:
            cursor = conn.execute(
                """
                SELECT run, command, timestamp, git_commit, config
                FROM runs
                ORDER BY timestamp DESC
                LIMIT 20
                """,
            )
        results = []
        for row in cursor.fetchall():
            run_id, command, timestamp, git_commit, config_json = row
            try:
                config = json.loads(config_json) if config_json else {}
            except json.JSONDecodeError:
                config = {}

            results.append(
                {
                    "run": run_id,
                    "command": command,
                    "timestamp": timestamp,
                    "git_commit": git_commit,
                    "config": config,
                }
            )
        return results
    finally:
        conn.close()


def format_time_ago(s: str) -> str:
    try:
        timestamp = datetime.fromisoformat(s)
        now = datetime.now(timezone.utc)

        diff = now - timestamp
        seconds = diff.total_seconds()

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 2592000:  # 30 days
            days = int(seconds // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds < 31536000:  # 365 days
            months = int(seconds // 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = int(seconds // 31536000)
            return f"{years} year{'s' if years != 1 else ''} ago"
    except:
        return "unknown time"


def format_run_choice(run: Dict[str, Any]) -> str:
    time_ago = format_time_ago(run["timestamp"]) if run["timestamp"] else "unknown time"

    if run["config"]:
        config_parts = [f"{k}={v}" for k, v in run["config"].items()]
        config_str = ", ".join(config_parts)
    else:
        config_str = "no config"

    return f"{run['command']} ({time_ago}) | {config_str}"


def select_run(runs: List[Dict[str, Any]]) -> None:
    if not runs:
        print("No runs found for the specified script.")
        return

    choices = []
    for run in runs:
        choice_display = format_run_choice(run)
        choices.append(questionary.Choice(title=choice_display, value=run))

    try:
        selected_run = questionary.select(
            "Select a run to copy to clipboard:",
            choices=choices,
            use_jk_keys=False,
            use_search_filter=True,
        ).ask()

        if selected_run:
            pyperclip.copy(selected_run["run"])

    except KeyboardInterrupt:
        print("\nExiting...")
        return


def show_run_data(n: int, run_name: str) -> None:
    import pandas as pd

    csv_path = vandc_dir() / f"{run_name}.csv"

    if not csv_path.exists():
        print(f"No data file found for run: {run_name}")
        return

    try:
        df = pd.read_csv(csv_path, comment="#")

        if df.empty:
            print(f"(No data)")
        else:
            print(df.tail(n).to_string())

    except Exception as e:
        print(f"Error reading data for run {run_name}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("script", nargs="?")
    parser.add_argument("--tail")
    parser.add_argument("-n", type=int, default=20)

    args = parser.parse_args()

    if not db_path().exists():
        print(f"No vandc database found at {db_path()}")
        sys.exit(1)

    if args.tail:
        show_run_data(args.n, args.tail)
        return

    runs = get_runs_by_script(args.script)

    if not runs:
        if args.script:
            print(f"No runs found for script: {args.script}")
        else:
            print("No runs found")
        sys.exit(1)

    select_run(runs)


if __name__ == "__main__":
    main()
