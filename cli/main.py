"""ProspectMap - CLI entry point for local business prospecting."""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

import config
import web_audit
from cache import Cache
from exporter import export
from places import PlacesAPIError, PlacesClient
from scorer import enrich

PRIORITY_STYLE = {
    "HIGH": "bold red",
    "MEDIUM": "yellow",
    "LOW": "dim white",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="prospectmap",
        description="ProspectMap - local business prospecting without a website.",
    )
    parser.add_argument(
        "--city",
        "--ville",
        required=True,
        help="City or address (e.g. 'Cugnaux 31270')",
    )
    parser.add_argument(
        "--type",
        dest="type_filter",
        default="all",
        choices=list(config.TYPE_MAPPING.keys()) + list(config.TYPE_ALIASES.keys()),
        help="Business category to target",
    )
    parser.add_argument(
        "--radius",
        "--rayon",
        type=int,
        default=config.DEFAULT_RADIUS,
        help=f"Search radius in meters (default: {config.DEFAULT_RADIUS})",
    )
    parser.add_argument(
        "--export",
        dest="export_path",
        help="Output file path (.csv or .json)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of displayed/exported prospects",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Filter out prospects below this score (0-100)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Bypass the local cache and force a fresh API call",
    )
    parser.add_argument(
        "--ttl-days",
        type=int,
        default=config.DEFAULT_TTL_DAYS,
        help=f"Cache freshness window in days (default: {config.DEFAULT_TTL_DAYS})",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Skip the prospect table (useful when only exporting)",
    )
    parser.add_argument(
        "--no-web-check",
        action="store_true",
        help="Skip the website quality audit (faster, but no weak-site detection)",
    )
    return parser.parse_args()


def display(prospects: list[dict], console: Console) -> None:
    if not prospects:
        console.print("[yellow]No prospects found.[/yellow]")
        return

    table = Table(
        title=f"Prospects - {len(prospects)} result(s)",
        title_style="bold cyan",
        header_style="bold",
        show_lines=False,
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Name", style="cyan")
    table.add_column("Phone", style="green")
    table.add_column("Website", style="magenta")
    table.add_column("Rating", justify="right")
    table.add_column("Reviews", justify="right")
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Priority")

    for i, p in enumerate(prospects, 1):
        site = p.get("website") or "—"
        if len(site) > 35:
            site = site[:32] + "..."
        priority = p.get("priority", "")
        style = PRIORITY_STYLE.get(priority, "white")
        rating = p.get("rating")
        table.add_row(
            str(i),
            p.get("name") or "",
            p.get("phone") or "—",
            site,
            f"{rating}" if rating is not None else "—",
            str(p.get("review_count") or 0),
            str(p.get("score") or 0),
            f"[{style}]{priority}[/{style}]",
        )
    console.print(table)

    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for p in prospects:
        counts[p.get("priority", "LOW")] = counts.get(p.get("priority", "LOW"), 0) + 1
    console.print(
        f"  [bold red]HIGH[/bold red]: {counts['HIGH']}   "
        f"[yellow]MEDIUM[/yellow]: {counts['MEDIUM']}   "
        f"[dim]LOW[/dim]: {counts['LOW']}"
    )


def main() -> int:
    args = parse_args()
    console = Console()

    args.type_filter = config.TYPE_ALIASES.get(args.type_filter, args.type_filter)

    console.print(
        f"[cyan]Search[/cyan]: type=[bold]{args.type_filter}[/bold] "
        f"city=[bold]{args.city}[/bold] radius=[bold]{args.radius}m[/bold]"
    )

    with Cache(Path(config.DB_PATH)) as cache:
        cached = None
        if not args.refresh:
            cached = cache.get_search(
                args.city, args.type_filter, args.radius, args.ttl_days
            )

        if cached is not None:
            raw, fetched_at = cached
            age_days = (datetime.now(timezone.utc) - fetched_at).days
            console.print(
                f"[dim]Cache hit: {len(raw)} prospect(s), {age_days}d old "
                f"— pass --refresh to re-query the API.[/dim]"
            )
        else:
            if not config.GOOGLE_API_KEY:
                console.print(
                    "[red]Error:[/red] GOOGLE_API_KEY is missing. "
                    "Copy .env.example to .env and set your key."
                )
                return 1

            try:
                client = PlacesClient()
            except PlacesAPIError as e:
                console.print(f"[red]Error:[/red] {e}")
                return 1

            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("{task.completed}/{task.total}"),
                    TimeElapsedColumn(),
                    console=console,
                    transient=True,
                ) as progress:
                    task = progress.add_task("Searching...", total=None)

                    def on_progress(label: str, current: int, total: int) -> None:
                        if total > 0:
                            progress.update(
                                task, description=label, completed=current, total=total
                            )
                        else:
                            progress.update(task, description=label)

                    raw = client.search_prospects(
                        args.city,
                        args.type_filter,
                        args.radius,
                        on_progress=on_progress,
                    )
            except PlacesAPIError as e:
                console.print(f"[red]API error:[/red] {e}")
                return 2
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user.[/yellow]")
                return 130

            cache.save_search(args.city, args.type_filter, args.radius, raw)

        audits = None
        if not args.no_web_check:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
                TimeElapsedColumn(),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("Auditing websites...", total=None)

                def on_audit(label: str, current: int, total: int) -> None:
                    if total > 0:
                        progress.update(
                            task, description=label, completed=current, total=total
                        )
                    else:
                        progress.update(task, description=label)

                audits = web_audit.audit_places(
                    cache.conn, raw, on_progress=on_audit
                )

    prospects = enrich(raw, audits=audits)
    if args.min_score:
        prospects = [p for p in prospects if p["score"] >= args.min_score]
    if args.limit:
        prospects = prospects[: args.limit]

    if not args.no_display:
        display(prospects, console)

    if args.export_path and prospects:
        try:
            path = export(prospects, args.export_path)
            console.print(f"\n[green]Export:[/green] {path}")
        except ValueError as e:
            console.print(f"[red]Export error:[/red] {e}")
            return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
