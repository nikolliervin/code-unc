"""Main CLI entry point using Typer."""

import typer
from rich.console import Console

from .. import __version__
from .commands import review, config, history

console = Console()

# Create main Typer application
app = typer.Typer(
    name="unc",
    help="AI-powered code review tool using git diff and various AI providers (OpenAI, Anthropic, Gemini, Ollama)",
    no_args_is_help=True,
    rich_markup_mode="rich",
    epilog="Run 'unc help' for comprehensive command reference and examples",
)

# Add subcommands
app.add_typer(review.app, name="review", help="Run code review on git diff")
app.add_typer(config.app, name="config", help="Manage configuration settings")
app.add_typer(history.app, name="history", help="View review history")


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Enable verbose output"),
    config_path: str = typer.Option(None, "--config", "-c", help="Path to configuration file"),
):
    """AI-powered code review tool using git diff and various AI providers."""
    pass


@app.command("version")
def version():
    """Show version and exit."""
    # ASCII Art
    art = """
                             =@@@+............=@@@*                           
                        .@@*........................=@@:                      
                      @#................................=@:                   
        *@.  -@@   @@......................................%@   %@=   @@      
       @         @#.................--------:................=@         @     
      @          *.....................:::....:...:::.........-          @    
      @         ................:--..........:--.....:.........+         +-   
     *:         *....:%@@@@@@@@@@@@..........%@@@@@@@@@@@@- ...*          @   
     @:       .%@@@@@@@@@@@=.   :@@@@=+**+=@@@@-   .-%@@@@@@@@@@@:        @   
     @:....@@@@@@@@@@*.............@@@@@@@@@@.............+@@@@@@@@@@:....@   
     #=...:@@@@@@@@*........@*.*@...@@@@@@@@ ..@-.@%........-@@@@@@@@=...:@   
     =@...%.@@@@@@@ .......@....:#..#@....@@..@.....+....... @@@@@@@-*...@%   
    =@...-#.... @@@+.......+.....-.+@@+==+%@*.+.....+.......:@@@-....--...=@  
    @ ..-=-.....*@@@............:%------------*=............@@@@......=-.. @  
    #*..-=-......@@@*..........%----------------@..........-@@@.......+-..-@  
     *@...+.......@@@..........@----------------@..........@@@.......:...#@   
        -*@........%@@#....:%@@@+--------------=@@@@:....*@@@........*#=      
          @.........*@@@@@@@@    @+----------=@    @@@@@@@@%.........@        
          :@...........:..=         :+#@@%*-         *..:...........%*        
           %*............*                            @............=@         
            @=...........@                            %...........:@          
             %%............%-                      -@............+@           
               @...............:#%.           #%:...............@:            
                #@............................................%@              
                  @@........................................@@                
                    -@*..................................=@+                   
                       +@@............................#%**@                   
                      @#****#%%:................:%@%*******@@                 
                    %@**********@     .*@-      %*******%****@                
                   @*************@  @#*****%@ .#********#@***#@               
              %@@@@*****#@*******************************@%***@.              
           @@:......@*#@-@*******************************@****@.              
         .@%%%@@%+..@@. +%*******************************@***@%               
         @%%@@@@%%@*    @#*******************************@%@@                 
         @%%@   @%@@    @********************************@                    
         +@@-  .@%@@    @********************************@.                   
               :@%@@    @********************************@.                   
               -@%@@    @********************************@.                   
               =@%@@    @#*******************************@                    
               +@%@@    =@%%@@@##******************#%@@%%@                    
               *@%@@    .@%%%%%%%%%%%@@@@@@@@@@%%%%%%%%%%@                    
               %@%@@     @%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%                    
               @@%@@     @%%%%%%%%%%%%%%@@%%%%%%%%%%%%%%@-                    
               @@%@@     @@%%%%%%%%%%%@+   @@%%%%%%%%%%%@                     
               @@%@@      @%%%%%%%%%@@      :@%%%%%%%%%%@                     
               @%%@@      @%%%%%%%%%@        @@%%%%%%%%@*                     
               @%%@@      #@%%%%%%%%@         @%%%%%%%%@                      
               @%%@@      +@@%%%%%%@:         @@%%%%%@@@                      
               @%%@@    -@#######@@@          @@@%#######@                    
               @@@@:    @@@@@@@@@@@@          @@@@@@@@@@@@                    
"""
    
    console.print(art, style="cyan")
    console.print(f"unc version {__version__}", style="bold green")
    raise typer.Exit()


@app.command("help")
def show_help():
    """Show comprehensive help with examples."""
    from rich.panel import Panel
    
    # Title
    console.print("\n[bold blue]UNC - AI-Powered Code Review Tool[/bold blue]")
    console.print("Comprehensive command reference and examples\n", style="dim")
    
    # Quick Start
    quick_start = """
[bold green]Quick Start:[/bold green]
1. [bold]unc config init[/bold] - Initialize configuration
2. [bold]unc review run-review[/bold] - Run your first review
3. [bold]unc config show[/bold] - View current settings
"""
    console.print(Panel(quick_start, title="🚀 Quick Start", border_style="green"))
    
    # Main Commands
    main_commands = """
[bold green]Main Commands:[/bold green]
[cyan]review[/cyan]  - Run AI code reviews on git diffs
[cyan]config[/cyan]  - Manage configuration settings
[cyan]history[/cyan] - View review history
[cyan]version[/cyan] - Show version information
[cyan]help[/cyan]    - Show this help message
"""
    console.print(Panel(main_commands, title="📋 Main Commands", border_style="magenta"))
    
    # Review Commands
    review_commands = """
[bold green]Review Commands:[/bold green]
[cyan]run-review[/cyan] - Run AI code review on git diff
[cyan]list[/cyan]       - List recent reviews
[cyan]show[/cyan]       - Show detailed review by ID

[bold yellow]Examples:[/bold yellow]
  unc review run-review --source feature --target main
  unc review list --format json
  unc review show abc12345-def6-7890-ghij-klmnopqrstuv
"""
    console.print(Panel(review_commands, title="🔍 Review Commands", border_style="blue"))
    
    # Config Commands
    config_commands = """
[bold green]Configuration Commands:[/bold green]
[cyan]init[/cyan]     - Interactive configuration setup
[cyan]show[/cyan]     - Show current configuration
[cyan]raw[/cyan]      - Show raw YAML configuration
[cyan]set[/cyan]      - Set configuration value
[cyan]validate[/cyan] - Validate configuration

[bold yellow]Examples:[/bold yellow]
  unc config init
  unc config show
  unc config set ai.provider openai
"""
    console.print(Panel(config_commands, title="⚙️ Configuration Commands", border_style="green"))
    
    # History Commands
    history_commands = """
[bold green]History Commands:[/bold green]
[cyan]list[/cyan]  - List review history
[cyan]show[/cyan]  - Show detailed review by ID
[cyan]clear[/cyan] - Clear review history

[bold yellow]Examples:[/bold yellow]
  unc history list --limit 10
  unc history show abc12345-def6-7890-ghij-klmnopqrstuv
  unc history clear --yes
"""
    console.print(Panel(history_commands, title="📚 History Commands", border_style="yellow"))
    
    # Common Examples
    examples = """
[bold green]Common Examples:[/bold green]

[bold]Basic Review:[/bold]
  unc review run-review

[bold]Review Specific Branches:[/bold]
  unc review run-review --source feature-branch --target main

[bold]Review with Focus Areas:[/bold]
  unc review run-review --focus security --focus performance

[bold]Review Specific Files:[/bold]
  unc review run-review --include "*.py" --exclude "tests/*"

[bold]Change AI Provider:[/bold]
  unc config set ai.provider anthropic
  unc config set ai.anthropic_api_key "your-key"

[bold]View Configuration:[/bold]
  unc config show
  unc config raw

[bold]View History:[/bold]
  unc history list --format json
  unc history show <review-id>
"""
    console.print(Panel(examples, title="💡 Common Examples", border_style="blue"))
    
    # Tips
    tips = """
[bold green]Tips:[/bold green]
• Use [bold]--verbose[/bold] for detailed output
• Use [bold]--config[/bold] to specify custom config file
• API keys can be set via environment variables
• Use [bold]unc help[/bold] anytime for this reference
"""
    console.print(Panel(tips, title="💭 Tips", border_style="yellow"))
    
    raise typer.Exit()


if __name__ == "__main__":
    app() 