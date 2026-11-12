import os
import sqlite3
import subprocess
import sys
import time

import pytest

from tracker import core, storage

RUNS = 20


def _run_and_kill(args, db, delay):
    """Start a real tracker command, wait `delay` seconds, then kill it abruptly."""
    env = {**os.environ, "TRACKER_DB": str(db)}
    proc = subprocess.Popen(
        [sys.executable, "-c", "from tracker.cli import app; app()", *args],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(delay)
    proc.kill()
    proc.wait()


def _integrity_ok(db):
    """Ask SQLite to check its own file for corruption."""
    conn = sqlite3.connect(db)
    try:
        return conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        conn.close()


@pytest.fixture
def seeded_db(tmp_path):
    db = tmp_path / "reliability.db"
    core.add_item("Dune", "book", path=db)
    core.add_item("Hades", "game", path=db)
    return db


@pytest.mark.parametrize("run", range(RUNS))
def test_edit_interrupted_never_corrupts(seeded_db, run):
    _run_and_kill(["edit", "1", "--title", "Dune Messiah"], seeded_db, run * 0.03)

    assert _integrity_ok(seeded_db)
    assert storage.get_item(1, seeded_db)["title"] in ("Dune", "Dune Messiah")
    assert storage.get_item(2, seeded_db) == {"id": 2, "title": "Hades", "type": "game"}


@pytest.mark.parametrize("run", range(RUNS))
def test_delete_interrupted_never_corrupts(seeded_db, run):
    _run_and_kill(["delete", "1", "--yes"], seeded_db, run * 0.03)

    assert _integrity_ok(seeded_db)
    item = storage.get_item(1, seeded_db)
    assert item is None or item == {"id": 1, "title": "Dune", "type": "book"}
    assert storage.get_item(2, seeded_db) == {"id": 2, "title": "Hades", "type": "game"}