import pytest
import sqlite3

from tracker import storage

@pytest.fixture
def db(tmp_path):
    return tmp_path / "test.db"

def test_insesrt_and_get(db):
    item_id = storage.insert_item("Dune", "book", db)
    assert storage.get_item(item_id, db) == {"id": item_id, "title": "Dune", "type": "book"}

def test_get_missing_returns_none(db):
    assert storage.get_item(999, db) is None

def test_list_is_empty_at_first(db):
    assert storage.list_items(db) == []

def test_data_is_saved_between_connection(db):
    storage.insert_item("Hades", "game", db)
    assert [i["title"] for i in storage.list_items(db)] == ["Hades"]

def test_update_changes_title(db):
    item_id = storage.insert_item("Dune", "book", db)
    assert storage.update_item(item_id, title="Dune Messiah", path=db) is True
    assert storage.get_item(item_id, db)["title"] == "Dune Messiah"


def test_update_missing_returns_false(db):
    assert storage.update_item(999, title="Nope", path=db) is False


def test_delete_removes_item(db):
    item_id = storage.insert_item("Dune", "book", db)
    assert storage.delete_item(item_id, db) is True
    assert storage.get_item(item_id, db) is None


def test_delete_missing_returns_false(db):
    assert storage.delete_item(999, db) is False


def test_find_duplicate_ignores_case(db):
    storage.insert_item("Dune", "book", db)
    assert storage.find_duplicate("dune", "book", db) is not None
    assert storage.find_duplicate("Dune", "movie", db) is None

def test_failed_write_leaves_no_partial_data(db):
    storage.insert_item("Dune", "book", db)
    with pytest.raises(sqlite3.IntegrityError):
        storage.insert_item(None, "book", db)
    assert [i["title"] for i in storage.list_items(db)] == ["Dune"]