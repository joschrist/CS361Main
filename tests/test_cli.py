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
    result = runner.invoke(app, ["add"], input="Dune\n")  # input ends before step 2
    assert result.exit_code != 0
    assert core.list_items(path=cli_db) == []