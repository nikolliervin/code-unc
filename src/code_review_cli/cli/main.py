"""Main CLI entry point using Typer."""

import typer
from rich import print
from rich.console import Console
from rich.traceback import install

# Handle both direct execution and package import
try:
    from .. import __version__
    from .commands import review, config, history
except ImportError:
    # If running directly, add parent directory to path
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from code_review_cli import __version__
    from code_review_cli.cli.commands import review, config, history

# Install rich traceback handler
install(show_locals=True)

# Create console for rich output
console = Console()

# Create main Typer app
app = typer.Typer(
    name="code-review",
    help="AI-powered code review tool using git diff and OpenAI/Anthropic",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Add subcommands
app.add_typer(review.app, name="review", help="Run code review on git diff")
app.add_typer(config.app, name="config", help="Manage configuration settings")
app.add_typer(history.app, name="history", help="View review history")


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-V", help="Enable verbose output"
    ),
    config_file: str = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
) -> None:
    """AI-powered code review tool."""
    if version:
        print(f"[bold blue]Code Review CLI[/bold blue] version [green]{__version__}[/green]")
        raise typer.Exit()
    
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")


if __name__ == "__main__":
    app() 