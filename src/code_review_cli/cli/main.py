"""Main CLI entry point using Typer."""

import typer
from rich.console import Console

from .. import __version__
from .commands import review, config, history

console = Console()

# Create main Typer application
app = typer.Typer(
    name="code-review",
    help="AI-powered code review tool using git diff and OpenAI/Anthropic",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Add subcommands
app.add_typer(review.app, name="review", help="Run code review on git diff")
app.add_typer(config.app, name="config", help="Manage configuration settings")
app.add_typer(history.app, name="history", help="View review history")


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Enable verbose output"),
    config_path: str = typer.Option(None, "--config", "-c", help="Path to configuration file"),
):
    """AI-powered code review tool using git diff and OpenAI/Anthropic."""
    if version:
        console.print(f"code-review version {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app() 