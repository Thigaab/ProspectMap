"""LeadLocal — point d'entrée CLI pour la prospection de commerces locaux."""
import argparse
import sys

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
from exporter import export
from places import PlacesAPIError, PlacesClient
from scorer import enrich

PRIORITY_STYLE = {
    "HAUTE": "bold red",
    "MOYENNE": "yellow",
    "BASSE": "dim white",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="leadlocal",
        description="LeadLocal — prospection de commerces locaux sans site web.",
    )
    parser.add_argument(
        "--ville",
        required=True,
        help="Ville ou adresse (ex: 'Cugnaux 31270')",
    )
    parser.add_argument(
        "--type",
        dest="type_filter",
        default="all",
        choices=list(config.TYPE_MAPPING.keys()),
        help="Catégorie de commerce à cibler",
    )
    parser.add_argument(
        "--rayon",
        type=int,
        default=config.DEFAULT_RADIUS,
        help=f"Rayon de recherche en mètres (défaut: {config.DEFAULT_RADIUS})",
    )
    parser.add_argument(
        "--export",
        dest="export_path",
        help="Chemin du fichier d'export (.csv ou .json)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limiter le nombre de prospects affichés/exportés",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Filtrer les prospects sous ce score (0-100)",
    )
    return parser.parse_args()


def display(prospects: list[dict], console: Console) -> None:
    if not prospects:
        console.print("[yellow]Aucun prospect trouvé.[/yellow]")
        return

    table = Table(
        title=f"Prospects — {len(prospects)} résultat(s)",
        title_style="bold cyan",
        header_style="bold",
        show_lines=False,
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Nom", style="cyan")
    table.add_column("Téléphone", style="green")
    table.add_column("Site", style="magenta")
    table.add_column("Note", justify="right")
    table.add_column("Avis", justify="right")
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Priorité")

    for i, p in enumerate(prospects, 1):
        site = p.get("site_web") or "—"
        if len(site) > 35:
            site = site[:32] + "..."
        priority = p.get("priorite", "")
        style = PRIORITY_STYLE.get(priority, "white")
        note = p.get("note")
        table.add_row(
            str(i),
            p.get("nom") or "",
            p.get("telephone") or "—",
            site,
            f"{note}" if note is not None else "—",
            str(p.get("nb_avis") or 0),
            str(p.get("score") or 0),
            f"[{style}]{priority}[/{style}]",
        )
    console.print(table)

    counts = {"HAUTE": 0, "MOYENNE": 0, "BASSE": 0}
    for p in prospects:
        counts[p.get("priorite", "BASSE")] = counts.get(p.get("priorite", "BASSE"), 0) + 1
    console.print(
        f"  [bold red]HAUTE[/bold red]: {counts['HAUTE']}   "
        f"[yellow]MOYENNE[/yellow]: {counts['MOYENNE']}   "
        f"[dim]BASSE[/dim]: {counts['BASSE']}"
    )


def main() -> int:
    args = parse_args()
    console = Console()

    if not config.GOOGLE_API_KEY:
        console.print(
            "[red]Erreur:[/red] GOOGLE_API_KEY absente. "
            "Copiez .env.example en .env et renseignez votre clé."
        )
        return 1

    try:
        client = PlacesClient()
    except PlacesAPIError as e:
        console.print(f"[red]Erreur:[/red] {e}")
        return 1

    console.print(
        f"[cyan]Recherche[/cyan] : type=[bold]{args.type_filter}[/bold] "
        f"ville=[bold]{args.ville}[/bold] rayon=[bold]{args.rayon}m[/bold]"
    )

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
            task = progress.add_task("Recherche...", total=None)

            def on_progress(label: str, current: int, total: int) -> None:
                if total > 0:
                    progress.update(task, description=label, completed=current, total=total)
                else:
                    progress.update(task, description=label)

            raw = client.search_prospects(
                args.ville, args.type_filter, args.rayon, on_progress=on_progress
            )
    except PlacesAPIError as e:
        console.print(f"[red]Erreur API:[/red] {e}")
        return 2
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrompu par l'utilisateur.[/yellow]")
        return 130

    prospects = enrich(raw)
    if args.min_score:
        prospects = [p for p in prospects if p["score"] >= args.min_score]
    if args.limit:
        prospects = prospects[: args.limit]

    display(prospects, console)

    if args.export_path and prospects:
        try:
            path = export(prospects, args.export_path)
            console.print(f"\n[green]Export :[/green] {path}")
        except ValueError as e:
            console.print(f"[red]Erreur export :[/red] {e}")
            return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
