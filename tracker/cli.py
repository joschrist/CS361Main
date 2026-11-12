import os
from pathlib import Path
import typer

from typing import Optional

from tracker import core, storage

app = typer.Typer(
    rich_markup_mode=None,
    help=(
        "Media Tracker keeps every book, movie, game, and album you enjoy in one "
        "library, so everything you track is in one place.\n\n"
        "\b\n"
        "Getting started in 3 steps:\n"
        '  1. Add an item:       tracker add "Dune" --type book\n'
        "  2. See your library:  tracker list\n"
        '  3. Fix a mistake:     tracker edit 1 --title "New title"\n'
        "                        tracker delete 1"
    ),
    epilog=(
        "\b\n"
        "Cost: each command takes a few seconds. Your library is stored\n"
        "in a file on this computer only; nothing is sent anywhere.\n\n"
        "\b\n"
        "More detail:  tracker <command> --help\n"
        "Less text:    add --quiet to list, add, or edit to hide tips\n"
        "Mistakes:     every change can be reversed; see the Undo line\n"
        "              in each command's help."
    ),
)

def _db_path():
    return Path(os.environ.get("TRACKER_DB", storage.DEFAULT_DB_PATH))

@app.callback()
def main() -> None:
    pass

def _format_table(items):
    id_w = max([len("ID")] + [len(str(i["id"])) for i in items]) + 3
    title_w = max([len("TITLE")] + [len(i["title"]) for i in items]) + 3
    lines = [f'{"ID":<{id_w}}{"TITLE":<{title_w}}TYPE']
    for i in items:
        lines.append(f'{i["id"]:<{id_w}}{i["title"]:<{title_w}}{i["type"]}')
    return "\n".join(lines)

STUCK_HINT = (
    'Stuck? Run "tracker add" with no options and we\'ll guide you\n'
    "step by step."
)


def _fail_add(code, title, type_):
    valid = ", ".join(core.VALID_TYPES)
    if code == "blank_title":
        typer.echo("Error: a title is required. Nothing was saved.")
    elif type_ is None or not type_.strip():
        typer.echo("Error: a type is required. Nothing was saved.")
        typer.echo(f"Valid types: {valid}")
    else:
        typer.echo(f'Error: "{type_}" is not a valid type. Nothing was saved.')
        typer.echo(f"Valid types: {valid}")
    typer.echo(STUCK_HINT)
    raise typer.Exit(code=1)

def _fail_edit(code, item_id, type_):
    if code == "not_found":
        typer.echo(f"Error: no item with ID {item_id} was found. Nothing was changed.")
        typer.echo('Run "tracker list" to see valid IDs, or run "tracker edit"')
        typer.echo("to pick from a list.")
    elif code == "nothing_to_change":
        typer.echo("Error: nothing to change. Nothing was changed.")
        typer.echo('Use --title and/or --type, or run "tracker edit" with no')
        typer.echo("options to pick from a list.")
    elif code == "blank_title":
        typer.echo("Error: the title can't be blank. Nothing was changed.")
    elif code == "invalid_type":
        typer.echo(f'Error: "{type_}" is not a valid type. Nothing was changed.')
        typer.echo(f"Valid types: {', '.join(core.VALID_TYPES)}")
    raise typer.Exit(code=1)

def _fail_delete(code, item_id):
    if code == "not_found":
            typer.echo(f"Error: no item with ID {item_id} was found. Nothing was changed.")
            typer.echo('Run "tracker list" to see valid IDs, or run "tracker delete"')
            typer.echo("to pick from a list.")
    raise typer.Exit(code=1)


def _pick_item(path, verb):
    items = core.list_items(path=path)
    if not items:
        typer.echo("Your library is empty.")
        typer.echo('Add your first item: tracker add "Dune" --type book')
        raise typer.Exit()

    typer.echo(f"Which item do you want to {verb}?")
    typer.echo(_format_table(items))
    answer = typer.prompt(
        "Enter an ID (or press Enter to cancel)", default="", show_default=False
    ).strip()
    if not answer:
        typer.echo("Cancelled. Nothing was changed.")
        raise typer.Exit()
    return answer

def _guided_add_prompts():
    typer.echo("Let's add an item. Press Ctrl+C at any time to cancel;")
    typer.echo("nothing will be saved.")
    title = typer.prompt("Step 1 of 2. Title")
    type_ = typer.prompt("Step 2 of 2. Type (book, movie, game, album)")
    return title, type_

@app.command("list")
def list_cmd(quiet: bool = typer.Option(False, "--quiet", help="Hide tips.")):
    """Show all items in your library.

    Undo: list only reads your library; it changes nothing.
    """
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

@app.command("add")
def add_cmd(
    title: Optional[str] = typer.Argument(None, help="Name of the item (use quotes for spaces)."),
    type: Optional[str] = typer.Option(None, help="One of: book, movie, game, album."),
    quiet: bool = typer.Option(False, help="Hide tips."),
):
    """Add a new item to your library.

    \b
    Two ways to add an item:
      Quick:   tracker add "Abbey Road" --type album
      Guided:  tracker add   (we ask you step by step)

    \b
    Undo: to remove an item you just added, run
          tracker delete ID
    """
    path = _db_path()

    if title is None and type is None:
        title, type = _guided_add_prompts()

    try:
        item = core.add_item(title, type, path=path)
    except core.TrackerError as err:
        if err.code != "duplicate":
            _fail_add(err.code, title, type)
        existing = err.existing
        typer.echo(
            f'"{existing["title"]}" ({existing["type"]}) is already in your library '
            f'as ID {existing["id"]}.'
        )
        if not typer.confirm("Add it again anyway?", default=False):
            typer.echo("Cancelled. Nothing was saved.")
            return
        item = core.add_item(title, type, allow_duplicate=True, path=path)

    typer.echo(f'Added: {item["title"]} ({item["type"]}), ID {item["id"]}')
    if not quiet:
        typer.echo('Tip: see everything with "tracker list".')
        typer.echo(f'     To undo: tracker delete {item["id"]}')

@app.command("edit")
def edit_cmd(
    item_id: Optional[int] = typer.Argument(None, metavar="ID", help="The item's number (see \"tracker list\")."),
    title: Optional[str] = typer.Option(None, help="New title."),
    type: Optional[str] = typer.Option(None, help="New type: book, movie, game, or album."),
    quiet: bool = typer.Option(False, help="Hide tips."),
):
    """Change an item's title or type.

    \b
    Two ways to edit an item:
      With an ID:     tracker edit 3 --title "Dune Messiah"
      Pick from list: tracker edit   (you choose)

    \b
    Undo: edit it again with the old value. The confirmation
          always shows the old value.
    """
    path = _db_path()
    picked = item_id is None

    if picked:
        answer = _pick_item(path, "edit")
        if not answer.isdigit():
            _fail_edit("not_found", answer, None)
        item_id = int(answer)

        if title is None and type is None:
            try:
                current = core.get_item(item_id, path=path)
            except core.TrackerError as err:
                _fail_edit(err.code, item_id, None)
            title = typer.prompt(
                f'New title (press Enter to keep "{current["title"]}")',
                default="", show_default=False,
            ).strip() or None
            type = typer.prompt(
                f'New type (press Enter to keep "{current["type"]}")',
                default="", show_default=False,
            ).strip() or None

    try:
        old, new = core.edit_item(item_id, title=title, type_=type, path=path)
    except core.TrackerError as err:
        _fail_edit(err.code, item_id, type)

    typer.echo(f"Updated item {item_id}:")
    undo = []
    if title is not None:
        typer.echo(f'  title: {old["title"]} → {new["title"]}')
        undo.append(f'--title "{old["title"]}"')
    if type is not None:
        typer.echo(f'  type: {old["type"]} → {new["type"]}')
        undo.append(f'--type {old["type"]}')
    if not quiet:
        typer.echo(f'Tip: To undo: tracker edit {item_id} {" ".join(undo)}')    

@app.command("delete")
def delete_cmd(
    item_id: Optional[int] = typer.Argument(None, metavar="ID", help="The item's number (see \"tracker list\")."),
    yes: bool = typer.Option(False, help="Skip the \"Delete it?\" question."),
):
    """Remove an item from your library.

    \b
    Two ways to delete an item:
      With an ID:     tracker delete 3
      Pick from list: tracker delete   (you choose)

    \b
    Undo: the confirmation shows the command that restores it.
    """
    path = _db_path()

    if item_id is None:
        answer = _pick_item(path, "delete")
        if not answer.isdigit():
            _fail_delete("not_found", answer)
        item_id = int(answer)

    try:
        item = core.get_item(item_id, path=path)     
    except core.TrackerError as err:
        _fail_delete(err.code, item_id)
        

    typer.echo(f'You are about to delete: "{item["title"]}" ({item["type"]}, ID {item["id"]}).')
    typer.echo("It will be removed from your library right away.")
    typer.echo("To restore it later, run:")
    typer.echo(f'  tracker add "{item["title"]}" --type {item["type"]}')

    if not yes:
        if not typer.confirm("Delete it?", default=False):
                typer.echo("Cancelled. Nothing was deleted.")
                return

    core.delete_item(item_id, path=path)

    typer.echo(f"Deleted item {item_id}.")