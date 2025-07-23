"""Configuration command implementation."""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from ...core.config.manager import ConfigManager
from ...models.config import Config, AIConfig, OutputConfig, GitConfig, CacheConfig, ReviewConfig
from pydantic import ValidationError

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
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Main configuration table
        table = Table(title="Code Review CLI Settings", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        # AI Configuration
        table.add_row("AI Provider", config.ai.provider)
        table.add_row("Model", config.ai.model)
        table.add_row("Temperature", str(config.ai.temperature))
        table.add_row("Max Tokens", str(config.ai.max_tokens))
        table.add_row("Max Retries", str(config.ai.max_retries))
        table.add_row("Retry Delay", f"{config.ai.retry_delay}s")
        table.add_row("Timeout", f"{config.ai.timeout}s")
        
        # Show API key status (hidden for security)
        if config.ai.provider == "openai" and config.ai.openai_api_key:
            table.add_row("OpenAI API Key", "••••••••" + config.ai.openai_api_key[-4:] if len(config.ai.openai_api_key) > 4 else "••••••••")
        elif config.ai.provider == "anthropic" and config.ai.anthropic_api_key:
            table.add_row("Anthropic API Key", "••••••••" + config.ai.anthropic_api_key[-4:] if len(config.ai.anthropic_api_key) > 4 else "••••••••")
        elif config.ai.provider == "gemini" and config.ai.gemini_api_key:
            table.add_row("Gemini API Key", "••••••••" + config.ai.gemini_api_key[-4:] if len(config.ai.gemini_api_key) > 4 else "••••••••")
        
        # Show Ollama settings regardless of provider (since they're in your config)
        if config.ai.ollama_base_url:
            table.add_row("Ollama URL", config.ai.ollama_base_url)
        if config.ai.ollama_model:
            table.add_row("Ollama Model", config.ai.ollama_model)
        
        # Git Configuration
        table.add_row("Default Source", config.git.default_source)
        table.add_row("Default Target", config.git.default_target)
        table.add_row("Max Diff Size", f"{config.git.max_diff_size:,} bytes")
        table.add_row("Binary Files", "Yes" if config.git.binary_files else "No")
        
        # Output Configuration
        table.add_row("Output Format", config.output.format)
        table.add_row("Show Progress", "Yes" if config.output.show_progress else "No")
        table.add_row("Show Metrics", "Yes" if config.output.show_metrics else "No")
        table.add_row("Show Suggestions", "Yes" if config.output.show_suggestions else "No")
        table.add_row("Max Issues Display", str(config.output.max_issues_display))
        table.add_row("Color Enabled", "Yes" if config.output.color_enabled else "No")
        
        # Cache Configuration
        table.add_row("Cache Enabled", "Yes" if config.cache.enabled else "No")
        table.add_row("Cache TTL", f"{config.cache.ttl_hours} hours")
        table.add_row("Cache Max Size", f"{config.cache.max_size_mb} MB")
        table.add_row("Cache Cleanup Interval", f"{config.cache.cleanup_interval_hours} hours")
        
        # Review Configuration
        if hasattr(config, 'review') and config.review:
            table.add_row("Severity Threshold", config.review.severity_threshold)
            table.add_row("Max Files per Review", str(config.review.max_files_per_review))
            table.add_row("Timeout", f"{config.review.timeout_seconds} seconds")
        
        console.print(table)
        
        # Show config file location
        config_path = config_manager.config_path
        console.print(f"\n[dim]Config file: {config_path}[/dim]")
        
        # Show file patterns
        console.print(f"\n[bold]Include Patterns:[/bold]")
        if config.git.include_patterns:
            for pattern in config.git.include_patterns:
                console.print(f"  • {pattern}")
        else:
            console.print("  • (none)")
        
        console.print(f"\n[bold]Exclude Patterns:[/bold]")
        if config.git.exclude_patterns:
            for pattern in config.git.exclude_patterns:
                console.print(f"  • {pattern}")
        else:
            console.print("  • (none)")
        
        # Show focus areas
        if hasattr(config, 'review') and config.review:
            console.print(f"\n[bold]Default Focus Areas:[/bold]")
            if config.review.default_focus:
                for focus in config.review.default_focus:
                    console.print(f"  • {focus}")
            else:
                console.print("  • (none)")
        
    except FileNotFoundError:
        console.print("[yellow]⚠️  No configuration file found.[/yellow]")
        console.print("Run [bold]unc config init[/bold] to create a configuration.")
    except Exception as e:
        console.print(f"[red]❌ Error loading configuration: {e}[/red]")
        console.print("Run [bold]unc config validate[/bold] to check your configuration.")


@app.command("raw")
def show_raw_config() -> None:
    """Show raw YAML configuration."""
    console.print("[bold blue]Raw Configuration (YAML)[/bold blue]\n")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Convert config to dict and display as YAML
        import yaml
        config_dict = config.dict()
        
        # Remove sensitive data
        if 'ai' in config_dict:
            if 'openai_api_key' in config_dict['ai'] and config_dict['ai']['openai_api_key']:
                config_dict['ai']['openai_api_key'] = '••••••••' + config_dict['ai']['openai_api_key'][-4:]
            if 'anthropic_api_key' in config_dict['ai'] and config_dict['ai']['anthropic_api_key']:
                config_dict['ai']['anthropic_api_key'] = '••••••••' + config_dict['ai']['anthropic_api_key'][-4:]
            if 'gemini_api_key' in config_dict['ai'] and config_dict['ai']['gemini_api_key']:
                config_dict['ai']['gemini_api_key'] = '••••••••' + config_dict['ai']['gemini_api_key'][-4:]
        
        yaml_str = yaml.dump(config_dict, default_flow_style=False, sort_keys=False, indent=2)
        console.print(f"[code]{yaml_str}[/code]")
        
        # Show config file location
        config_path = config_manager.config_path
        console.print(f"\n[dim]Config file: {config_path}[/dim]")
        
    except FileNotFoundError:
        console.print("[yellow]⚠️  No configuration file found.[/yellow]")
        console.print("Run [bold]unc config init[/bold] to create a configuration.")
    except Exception as e:
        console.print(f"[red]❌ Error loading configuration: {e}[/red]")
        console.print("Run [bold]unc config validate[/bold] to check your configuration.")


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
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        errors = []
        warnings = []
        
        # Validate AI configuration
        if not config.ai.provider:
            errors.append("AI provider is not set")
        elif config.ai.provider not in ['openai', 'anthropic', 'gemini', 'ollama']:
            errors.append(f"Invalid AI provider: {config.ai.provider}")
        
        if not config.ai.model:
            errors.append("AI model is not set")
        
        # Check API keys based on provider
        if config.ai.provider == "openai" and not config.ai.openai_api_key:
            errors.append("OpenAI API key is required for OpenAI provider")
        elif config.ai.provider == "anthropic" and not config.ai.anthropic_api_key:
            errors.append("Anthropic API key is required for Anthropic provider")
        elif config.ai.provider == "gemini" and not config.ai.gemini_api_key:
            errors.append("Gemini API key is required for Gemini provider")
        
        # Validate temperature range
        if not (0.0 <= config.ai.temperature <= 2.0):
            errors.append(f"Temperature must be between 0.0 and 2.0, got {config.ai.temperature}")
        
        # Validate max tokens
        if config.ai.max_tokens <= 0:
            errors.append(f"Max tokens must be positive, got {config.ai.max_tokens}")
        elif config.ai.max_tokens > 32000:
            warnings.append(f"Max tokens is very high ({config.ai.max_tokens}), may cause issues")
        
        # Validate output format
        if config.output.format not in ['rich', 'json', 'markdown', 'html']:
            errors.append(f"Invalid output format: {config.output.format}")
        
        # Validate severity threshold
        if hasattr(config, 'review') and config.review:
            if config.review.severity_threshold not in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                errors.append(f"Invalid severity threshold: {config.review.severity_threshold}")
        
        # Display results
        if errors:
            console.print("[red]❌ Configuration validation failed![/red]\n")
            console.print("[bold red]Errors:[/bold red]")
            for error in errors:
                console.print(f"  • {error}")
        else:
            console.print("[green]✓ Configuration is valid![/green]")
        
        if warnings:
            console.print(f"\n[bold yellow]Warnings:[/bold yellow]")
            for warning in warnings:
                console.print(f"  • {warning}")
        
        # Configuration summary
        console.print(f"\n[bold]Configuration Summary:[/bold]")
        console.print(f"Provider: [blue]{config.ai.provider}[/blue]")
        console.print(f"Model: [blue]{config.ai.model}[/blue]")
        console.print(f"Config file: [dim]{config_manager.config_path}[/dim]")
        
        if errors:
            raise typer.Exit(1)
            
    except FileNotFoundError:
        console.print("[red]❌ Configuration file not found![/red]")
        console.print("Run [bold]unc config init[/bold] to create a configuration.")
    except ValidationError as e:
        console.print("[red]❌ Configuration validation failed![/red]")
        console.print(f"Validation errors: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error validating configuration: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app() 
