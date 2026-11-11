import pytest
from typer.testing import CliRunner

from tracker import core
from tracker.cli import app

runner = CliRunner()


@pytest.fixture
def cli_db(tmp_path, monkeypatch):
    path = tmp_path / "cli.db"
    monkeypatch.setenv("TRACKER_DB", str(path))
    return path


def test_list_empty(cli_db):
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Your library is empty." in result.output
    assert 'tracker add "Dune" --type book' in result.output


def test_list_shows_table(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    core.add_item("Hades", "game", path=cli_db)
    result = runner.invoke(app, ["list"])
    assert "Your library (2 items)" in result.output
    assert "Dune" in result.output and "game" in result.output
    assert "Tip:" in result.output


def test_list_quiet_hides_tips(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    result = runner.invoke(app, ["list", "--quiet"])
    assert "Dune" in result.output
    assert "Tip:" not in result.output
    assert "Your library (" not in result.output

def test_add_quick(cli_db):
    result = runner.invoke(app, ["add", "Dune", "--type", "book"])
    assert result.exit_code == 0
    assert "Added: Dune (book), ID 1" in result.output
    assert "To undo: tracker delete 1" in result.output
    assert [i["title"] for i in core.list_items(path=cli_db)] == ["Dune"]


def test_add_quiet_hides_tips(cli_db):
    result = runner.invoke(app, ["add", "Dune", "--type", "book", "--quiet"])
    assert "Added: Dune (book), ID 1" in result.output
    assert "Tip:" not in result.output


def test_add_cleans_type_case(cli_db):
    result = runner.invoke(app, ["add", "Dune", "--type", "Book"])
    assert "Added: Dune (book)" in result.output


def test_add_missing_title(cli_db):
    result = runner.invoke(app, ["add", "--type", "book"])
    assert result.exit_code == 1
    assert "a title is required. Nothing was saved." in result.output
    assert "Stuck?" in result.output
    assert core.list_items(path=cli_db) == []


def test_add_missing_type(cli_db):
    result = runner.invoke(app, ["add", "Dune"])
    assert result.exit_code == 1
    assert "a type is required" in result.output
    assert core.list_items(path=cli_db) == []


def test_add_invalid_type(cli_db):
    result = runner.invoke(app, ["add", "Dune", "--type", "podcast"])
    assert result.exit_code == 1
    assert '"podcast" is not a valid type' in result.output
    assert "Valid types: book, movie, game, album" in result.output
    assert "Stuck?" in result.output
    assert core.list_items(path=cli_db) == []


def test_add_duplicate_declined(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    result = runner.invoke(app, ["add", "Dune", "--type", "book"], input="n\n")
    assert "already in your library as ID 1" in result.output
    assert "Cancelled. Nothing was saved." in result.output
    assert len(core.list_items(path=cli_db)) == 1


def test_add_duplicate_accepted(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    runner.invoke(app, ["add", "Dune", "--type", "book"], input="y\n")
    assert len(core.list_items(path=cli_db)) == 2


def test_add_guided(cli_db):
    result = runner.invoke(app, ["add"], input="Dune\nbook\n")
    assert "Step 1 of 2" in result.output
    assert "Step 2 of 2" in result.output
    assert "Added: Dune (book), ID 1" in result.output


def test_add_guided_cancel_saves_nothing(cli_db):
    result = runner.invoke(app, ["add"], input="Dune\n")
    assert result.exit_code != 0
    assert core.list_items(path=cli_db) == []

def test_edit_title(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    result = runner.invoke(app, ["edit", "1", "--title", "Dune Messiah"])
    assert result.exit_code == 0
    assert "Updated item 1:" in result.output
    assert "title: Dune → Dune Messiah" in result.output
    assert 'To undo: tracker edit 1 --title "Dune"' in result.output
    assert core.get_item(1, path=cli_db)["title"] == "Dune Messiah"


def test_edit_type_quiet(cli_db):
    core.add_item("Hades", "movie", path=cli_db)
    result = runner.invoke(app, ["edit", "1", "--type", "game", "--quiet"])
    assert "type: movie → game" in result.output
    assert "Tip:" not in result.output


def test_edit_nothing_to_change(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    result = runner.invoke(app, ["edit", "1"])
    assert result.exit_code == 1
    assert "nothing to change. Nothing was changed." in result.output
    assert 'run "tracker edit" with no' in result.output


def test_edit_not_found(cli_db):
    result = runner.invoke(app, ["edit", "9", "--title", "X"])
    assert result.exit_code == 1
    assert "no item with ID 9 was found. Nothing was changed." in result.output


def test_edit_invalid_type_changes_nothing(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    result = runner.invoke(app, ["edit", "1", "--type", "podcast"])
    assert result.exit_code == 1
    assert '"podcast" is not a valid type' in result.output
    assert core.get_item(1, path=cli_db)["type"] == "book"


def test_edit_blank_title_changes_nothing(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    result = runner.invoke(app, ["edit", "1", "--title", "  "])
    assert result.exit_code == 1
    assert core.get_item(1, path=cli_db)["title"] == "Dune"


def test_edit_pick_mode(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    core.add_item("Hades", "game", path=cli_db)
    result = runner.invoke(app, ["edit"], input="2\nHades II\n\n")
    assert "Which item do you want to edit?" in result.output
    assert "title: Hades → Hades II" in result.output
    assert core.get_item(2, path=cli_db)["title"] == "Hades II"
    assert core.get_item(2, path=cli_db)["type"] == "game"


def test_edit_pick_cancel(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    result = runner.invoke(app, ["edit"], input="\n")
    assert "Cancelled. Nothing was changed." in result.output
    assert core.get_item(1, path=cli_db)["title"] == "Dune"


def test_edit_pick_all_blank_is_nothing_to_change(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    result = runner.invoke(app, ["edit"], input="1\n\n\n")
    assert result.exit_code == 1
    assert "nothing to change" in result.output


def test_edit_pick_bad_id(cli_db):
    core.add_item("Dune", "book", path=cli_db)
    result = runner.invoke(app, ["edit"], input="abc\n")
    assert result.exit_code == 1
    assert "no item with ID abc was found" in result.output


def test_edit_pick_empty_library(cli_db):
    result = runner.invoke(app, ["edit"])
    assert "Your library is empty." in result.output