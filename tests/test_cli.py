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