"""Configuration command implementation."""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from ...core.config.manager import ConfigManager
from ...models.config import Config, AIConfig, OutputConfig, GitConfig, CacheConfig, ReviewConfig

console = Console()
app = typer.Typer()


@app.command("init")
def init_config() -> None:
    """Initialize configuration with interactive setup."""
    console.print("[bold blue]Initializing Code Review CLI Configuration[/bold blue]\n")
    
    # AI Provider setup
    console.print("[bold]AI Provider Configuration[/bold]")
    provider = Prompt.ask(
        "Choose AI provider",
        choices=["openai", "anthropic", "gemini", "ollama"],
        default="openai"
    )
    
    # Get API key and model based on provider
    api_key = None
    if provider == "openai":
        api_key = Prompt.ask("Enter OpenAI API key", password=True)
        model = Prompt.ask(
            "Choose model",
            choices=["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            default="gpt-4-turbo"
        )
    elif provider == "anthropic":
        api_key = Prompt.ask("Enter Anthropic API key", password=True)
        model = Prompt.ask(
            "Choose model",
            choices=["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
            default="claude-3-sonnet-20240229"
        )
    elif provider == "gemini":
        api_key = Prompt.ask("Enter Google Gemini API key", password=True)
        model = Prompt.ask(
            "Choose model",
            choices=[
                "gemini-2.5-flash",      # Latest, fastest, most cost-effective
                "gemini-2.5-pro", 
                "gemini-2.0-flash",
                "gemini-1.5-flash", 
                "gemini-1.5-pro", 
                "gemini-1.0-pro"
            ],
            default="gemini-2.5-flash"
        )
    else:  # ollama
        api_key = None
        model = Prompt.ask(
            "Enter Ollama model name",
            default="codellama:7b"
        )
    
    # Create AI configuration
    ai_config = AIConfig(
        provider=provider,
        model=model,
        temperature=0.1,
        max_tokens=4000
    )
    
    # Set provider-specific API keys
    if provider == "openai":
        ai_config.openai_api_key = api_key
    elif provider == "anthropic":
        ai_config.anthropic_api_key = api_key
    elif provider == "gemini":
        ai_config.gemini_api_key = api_key
    elif provider == "ollama":
        ai_config.ollama_model = model
    
    # Create full configuration
    config = Config(
        ai=ai_config,
        output=OutputConfig(
            format="rich",
            show_progress=True,
            show_metrics=True,
            show_suggestions=True,
            max_issues_display=50,
            console_width=None,
            color_enabled=True
        ),
        git=GitConfig(
            default_source="HEAD",
            default_target="main",
            max_diff_size=1000000,
            include_patterns=[],
            exclude_patterns=["*.log", "*.tmp", "node_modules/*", ".git/*"],
            binary_files=False
        ),
        cache=CacheConfig(
            enabled=True,
            ttl_hours=24,
            max_size_mb=100,
            cleanup_interval_hours=168
        ),
        review=ReviewConfig(
            default_focus=[],
            severity_threshold="LOW",
            max_files_per_review=100,
            timeout_seconds=300
        )
    )
    
    # Save configuration
    try:
        config_manager = ConfigManager()
        config_path = config_manager.save_config(config)
        
        console.print(f"\n[green]✓[/green] Configuration saved successfully!")
        console.print(f"Config file: [blue]{config_path}[/blue]")
        console.print(f"Provider: [blue]{provider}[/blue]")
        console.print(f"Model: [blue]{model}[/blue]")
        
        if api_key:
            console.print(f"API Key: [green]••••••••[/green] (hidden)")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to save configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command("show")
def show_config() -> None:
    """Show current configuration."""
    console.print("[bold blue]Current Configuration[/bold blue]\n")
    
    table = Table(title="Code Review CLI Settings")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")
    
    # TODO: Load actual config
    table.add_row("AI Provider", "openai")
    table.add_row("Model", "gpt-4-turbo")
    table.add_row("Output Format", "rich")
    table.add_row("Max Files", "50")
    table.add_row("Cache Enabled", "true")
    
    console.print(table)
    console.print("\n[yellow]⚠️ Showing placeholder values - actual config loading not yet implemented[/yellow]")


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key (e.g., ai.provider)"),
    value: str = typer.Argument(..., help="Configuration value"),
) -> None:
    """Set configuration value."""
    console.print(f"Setting [cyan]{key}[/cyan] to [magenta]{value}[/magenta]")
    console.print("[yellow]⚠️ Configuration setting not yet implemented[/yellow]")


@app.command("validate")
def validate_config() -> None:
    """Validate current configuration."""
    console.print("[bold blue]Validating Configuration[/bold blue]\n")
    
    with console.status("[bold green]Checking configuration..."):
        import time
        time.sleep(2)  # Simulate validation
    
    console.print("[green]✓[/green] Configuration is valid")
    console.print("[yellow]⚠️ Validation logic not yet implemented[/yellow]")


if __name__ == "__main__":
    app() 