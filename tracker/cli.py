import typer

app = typer.Typer(help="A command-line library for the books, movies, games, and albums you consume.")


@app.callback()
def main() -> None:
    """A command-line library for the books, movies, games, and albums you consume."""
    