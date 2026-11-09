import sqlite3
from contextlib import closing
from pathlib import Path

DEFAULT_DB_PATH = Path.home()

def _connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type  TEXT NOT NULL
        )
        """
    )
    return conn

def _to_dict(row):
    return {"id": row["id"], "title": row["title"], "type": row["type"]}

def insert_item(title, type_, path=DEFAULT_DB_PATH):
    with closing(_connect(path)) as conn, conn:
        cur = conn.execute(
            "INSERT INTO items (title, type) VALUES (?, ?)", (title, type_)
        )
    return cur.lastrowid

def get_item(item_id, path=DEFAULT_DB_PATH):
    with closing(_connect(path)) as conn:
        row = conn.execute(
            "SELECT id, title, type FROM items WHERE id = ?", (item_id,)
        ).fetchone()
        return _to_dict(row) if row else None

def list_items(path=DEFAULT_DB_PATH):
    with closing(_connect(path)) as conn:
        rows = conn.execute("SELECT id, title, type FROM items ORDER BY id").fetchall()
    return [_to_dict(r) for r in rows]

def find_duplicate(title, type_, path=DEFAULT_DB_PATH):
    with closing(_connect(path)) as conn:
        row = conn.execute(
            "SELECT id, title, type FROM items WHERE LOWER(title) = LOWER(?) AND type = ?",
            (title, type_),
        ).fetchone()
    return _to_dict(row) if row else None


def update_item(item_id, title=None, type_=None, path=DEFAULT_DB_PATH):
    fields, values = [], []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if type_ is not None:
        fields.append("type = ?")
        values.append(type_)
    if not fields:
        return False
    values.append(item_id)
    with closing(_connect(path)) as conn, conn:
        cur = conn.execute(f"UPDATE items SET {', '.join(fields)} WHERE id = ?", values)
        return cur.rowcount > 0


def delete_item(item_id, path=DEFAULT_DB_PATH):
    with closing(_connect(path)) as conn, conn:
        cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        return cur.rowcount > 0