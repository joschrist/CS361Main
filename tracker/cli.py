import os
from pathlib import Path
import typer

from tracker import core, storage

app = typer.Typer(
    help="A command-line library for the books, movies, games, and albums you consume."
)

def _db_path():
    return Path(os.environ.get("TRACKER_DB", storage.DEFAULT_DB_PATH))

@app.callback()
def main() -> None:
    """A command-line library for the books, movies, games, and albums you consume."""

def _format_table(items):
    id_w = max([len("ID")] + [len(str(i["id"])) for i in items]) + 3
    title_w = max([len("TITLE")] + [len(i["title"]) for i in items]) + 3
    lines = [f'{"ID":<{id_w}}{"TITLE":<{title_w}}TYPE']
    for i in items:
        lines.append(f'{i["id"]:<{id_w}}{i["title"]:<{title_w}}{i["type"]}')
    return "\n".join(lines)

@app.command("list")
def list_cmd(quiet: bool = typer.Option(False, "--quiet", help="Hide tips.")):
    items = core.list_items(path=_db_path())

    if not items:
        typer.echo("Your library is empty.")
        typer.echo('Add your first item: tracker add "Dune" --type book')
        return

    if not quiet:
        n = len(items)
        typer.echo(f"Your library ({n} item{'s' if n != 1 else ''}) \n")
    typer.echo(_format_table(items))
    if not quiet:
        typer.echo('\nTip: change an item with "tracker edit ID --title ..."')
        typer.echo('    remove one with "tracker delete ID"')
    