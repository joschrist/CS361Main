import pytest

from tracker import core

@pytest.fixture
def db(tmp_path):
    return tmp_path / "test.db"

def test_add_returns_item(db):
    item = core.add_item("Dune", "book", path=db)
    assert item["title"] == "Dune"
    assert item["type"] == "book"

def test_add_blank_title_fails(db):
    with pytest.raises(core.TrackerError) as err:
        core.add_item("   ", "book", path=db)
    assert err.value.code == "blank_title"

def test_add_bad_type_fails(db):
    with pytest.raises(core.TrackerError) as err:
        core.add_item("Dune", "podcast", path=db)
    assert err.value.code == "invalid_type"

def test_add_cleans_type(db):
    assert core.add_item("Dune", "Book", path=db)["type"] == "book"

def test_add_duplicate_fails_then_allowed(db):
    core.add_item("Dune", "book", path=db)
    with pytest.raises(core.TrackerError) as err:
        core.add_item("dune", "book", path=db)
    assert err.value.code == "duplicate"
    assert err.value.existing["title"] == "Dune"

def test_clean_fields_skips_none():
    assert core._clean_fields(None, None) == (None, None)

def test_edit_item(db):
    item = core.add_item("Dune", "book", path=db)
    old, new = core.edit_item(item["id"], "Dune: Messiah", "movie", path=db)

    assert old["title"] == "Dune"
    assert old["type"] == "book"
    assert new["title"] == "Dune: Messiah"
    assert new["type"] == "movie"

def test_list_items(db):
    core.add_item("Dune", "book", path=db)
    core.add_item("Hades", "game", path=db)

    items = core.list_items(path=db)

    assert [i["title"] for i in items] == ["Dune", "Hades"]
    assert [i["type"] for i in items] == ["book", "game"]

def test_list_items_empty(db):
    assert core.list_items(path=db) == []