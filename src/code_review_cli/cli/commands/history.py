"""History command implementation."""

import typer
from rich.console import Console
from rich.table import Table
from datetime import datetime
from typing import Optional

from ...core.config.manager import ConfigManager
from ...core.history.storage import HistoryStorage

console = Console()
app = typer.Typer()


@app.command("list")
def list_history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of reviews to show"),
    format: str = typer.Option("table", "--format", "-f", help="Output format (table, json)"),
) -> None:
    """List review history."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Check if history is enabled
        if not config.history.enabled:
            console.print("[yellow]⚠️ History tracking is disabled. Enable it with:[/yellow]")
            console.print("[yellow]  unc config set history.enabled true[/yellow]")
            return
        
        # Load history data
        history_storage = HistoryStorage(config.history)
        reviews = history_storage.get_reviews(limit=limit)
        
        if not reviews:
            console.print("[yellow]No review history found.[/yellow]")
            console.print("Run some code reviews to build up history!")
            return
        
        console.print(f"[bold blue]Review History (last {len(reviews)})[/bold blue]\n")
        
        if format == "table":
            table = Table(title="Recent Code Reviews")
            table.add_column("Date", style="cyan")
            table.add_column("ID", style="dim")
            table.add_column("Status", style="green") 
            table.add_column("AI Provider", style="blue")
            table.add_column("Files", justify="right", style="magenta")
            table.add_column("Issues", justify="right", style="red")
            
            for review in reviews:
                # Format date
                created_at = review.get('created_at')
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        pass
                
                date_str = created_at.strftime("%Y-%m-%d %H:%M") if isinstance(created_at, datetime) else str(created_at)
                
                # Truncate ID for display
                short_id = review['id'][:8] + "..." if len(review['id']) > 8 else review['id']
                
                # Status with emoji
                status = review['status']
                if status == "COMPLETED":
                    status_display = "✅ COMPLETED"
                elif status == "FAILED":
                    status_display = "❌ FAILED"
                else:
                    status_display = f"⏳ {status}"
                
                table.add_row(
                    date_str,
                    short_id,
                    status_display,
                    review.get('ai_provider', 'Unknown'),
                    str(review.get('file_count', 0)),
                    str(review.get('issue_count', 0))
                )
            
            console.print(table)
            
        elif format == "json":
            import json
            console.print(json.dumps(reviews, indent=2, default=str))
        
    except Exception as e:
        console.print(f"[red]❌ Failed to load history: {e}[/red]")


@app.command("show")
def show_review(
    review_id: str = typer.Argument(..., help="Review ID to display"),
) -> None:
    """Show detailed review by ID."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Check if history is enabled
        if not config.history.enabled:
            console.print("[yellow]⚠️ History tracking is disabled. Enable it with:[/yellow]")
            console.print("[yellow]  unc config set history.enabled true[/yellow]")
            return
        
        # Load history data
        history_storage = HistoryStorage(config.history)
        review_data = history_storage.get_review_by_id(review_id)
        
        if not review_data:
            console.print(f"[red]❌ Review not found: {review_id}[/red]")
            console.print("Use 'unc history list' to see available reviews.")
            return
        
        console.print(f"[bold blue]Review Details: {review_id}[/bold blue]\n")
        
        # Basic info
        console.print(f"[bold]Status:[/bold] {review_data['status']}")
        console.print(f"[bold]Created:[/bold] {review_data['created_at']}")
        if review_data.get('ai_provider'):
            console.print(f"[bold]AI Provider:[/bold] {review_data['ai_provider']}")
        if review_data.get('ai_model'):
            console.print(f"[bold]AI Model:[/bold] {review_data['ai_model']}")
        
        # Summary
        if review_data.get('summary'):
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(review_data['summary'])
        
        # Issues count
        if review_data.get('issues_data'):
            import json
            try:
                issues = json.loads(review_data['issues_data'])
                console.print(f"\n[bold]Issues Found:[/bold] {len(issues)}")
                
                # Group by severity
                severity_counts = {}
                for issue in issues:
                    severity = issue.get('severity', 'UNKNOWN')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                for severity, count in severity_counts.items():
                    console.print(f"  {severity}: {count}")
                    
            except json.JSONDecodeError:
                console.print("\n[yellow]Could not parse issues data[/yellow]")
        
        # File count
        if review_data.get('file_count'):
            console.print(f"\n[bold]Files Reviewed:[/bold] {review_data['file_count']}")
        
        # Error message if any
        if review_data.get('error_message'):
            console.print(f"\n[bold red]Error:[/bold red] {review_data['error_message']}")
            
    except Exception as e:
        console.print(f"[red]❌ Failed to load review details: {e}[/red]")


@app.command("clear")
def clear_history(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Clear review history."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Check if history is enabled
        if not config.history.enabled:
            console.print("[yellow]⚠️ History tracking is disabled. Enable it with:[/yellow]")
            console.print("[yellow]  unc config set history.enabled true[/yellow]")
            return
        
        # Get current count
        history_storage = HistoryStorage(config.history)
        current_reviews = history_storage.get_reviews(limit=1000)  # Get a high limit to count
        current_count = len(current_reviews)
        
        if current_count == 0:
            console.print("[yellow]No history to clear.[/yellow]")
            return
        
        # Confirm deletion
        if not confirm:
            confirm = typer.confirm(f"Are you sure you want to clear all {current_count} review history entries?")
        
        if confirm:
            console.print(f"[red]Clearing {current_count} review history entries...[/red]")
            deleted_count = history_storage.clear_history()
            if deleted_count > 0:
                console.print(f"[green]✓ Cleared {deleted_count} history entries.[/green]")
            else:
                console.print("[yellow]No entries were cleared.[/yellow]")
        else:
            console.print("Operation cancelled.")
            
    except Exception as e:
        console.print(f"[red]❌ Failed to clear history: {e}[/red]")


@app.command("stats")
def show_statistics() -> None:
    """Show history statistics."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Check if history is enabled
        if not config.history.enabled:
            console.print("[yellow]⚠️ History tracking is disabled. Enable it with:[/yellow]")
            console.print("[yellow]  unc config set history.enabled true[/yellow]")
            return
        
        # Get statistics
        history_storage = HistoryStorage(config.history)
        stats = history_storage.get_statistics()
        
        console.print("[bold blue]History Statistics[/bold blue]\n")
        
        if stats.get("total_entries", 0) == 0:
            console.print("[yellow]No history entries found.[/yellow]")
            return
        
        console.print(f"[bold]Total Reviews:[/bold] {stats.get('total_entries', 0)}")
        
        # Show by status
        by_status = stats.get('by_status', {})
        if by_status:
            console.print(f"\n[bold]By Status:[/bold]")
            for status, count in by_status.items():
                console.print(f"  {status}: {count}")
        
        # Show by provider
        by_provider = stats.get('by_provider', {})
        if by_provider:
            console.print(f"\n[bold]By AI Provider:[/bold]")
            for provider, count in by_provider.items():
                console.print(f"  {provider}: {count}")
        
        # Show date range
        date_range = stats.get('date_range', {})
        if date_range.get('earliest') and date_range.get('latest'):
            console.print(f"\n[bold]Date Range:[/bold]")
            console.print(f"  Earliest: {date_range['earliest']}")
            console.print(f"  Latest: {date_range['latest']}")
        
        # Show storage info
        if stats.get('storage_path'):
            console.print(f"\n[bold]Storage Location:[/bold] {stats['storage_path']}")
        
        # Show configuration
        console.print(f"\n[bold]Configuration:[/bold]")
        console.print(f"  Max Entries: {config.history.max_entries}")
        console.print(f"  Retention Days: {config.history.retention_days}")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to load statistics: {e}[/red]")


if __name__ == "__main__":
    app() 