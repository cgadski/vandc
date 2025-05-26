import sqlite3
import argparse
from pathlib import Path
import os
from datetime import datetime
import pandas as pd
from .writer import vandc_dir, db_path

def get_runs(limit=10):
    """Fetch the most recent runs from the database"""
    conn = sqlite3.connect(db_path())
    try:
        cursor = conn.execute("""
            SELECT run, timestamp, command, config
            FROM runs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()
    finally:
        conn.close()

def count_logs(run_name):
    """Count the number of log entries for a run"""
    try:
        csv_path = vandc_dir() / f"{run_name}.csv"
        if not csv_path.exists():
            return 0

        df = pd.read_csv(csv_path, comment="#")
        return len(df)
    except Exception:
        return 0

def format_timestamp(ts_string):
    """Format ISO timestamp to a more readable format"""
    try:
        dt = datetime.fromisoformat(ts_string)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ts_string

def list_runs():
    parser = argparse.ArgumentParser(description="List recent runs")
    parser.add_argument("-n", "--limit", type=int, default=10,
                        help="Number of runs to display (default: 10)")
    args = parser.parse_args()

    if not vandc_dir().exists():
        print(f"No .vandc directory found at {vandc_dir()}")
        return

    if not db_path().exists():
        print(f"No database found at {db_path()}")
        return

    runs = get_runs(args.limit)

    if not runs:
        print("No runs found in the database.")
        return

    print(f"Last {len(runs)} runs:")
    print("=" * 80)
    for run, timestamp, command, config in runs:
        num_logs = count_logs(run)
        print(f"Run: {run}")
        print(f"Time: {format_timestamp(timestamp)}")
        print(f"Command: {command}")
        print(f"Logs: {num_logs}")
        print("-" * 80)

if __name__ == "__main__":
    list_runs()
