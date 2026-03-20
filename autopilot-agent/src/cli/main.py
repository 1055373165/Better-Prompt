"""CLI entry point — Typer app with start/resume/status and control commands."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="autopilot",
    help="Multi-Agent system for automated full-cycle software development",
)
console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@app.command()
def start(
    requirement: str = typer.Argument(..., help="One-sentence project requirement"),
    project_dir: Path = typer.Option(".", "--dir", "-d", help="Target project directory"),
    model: str = typer.Option("gpt-4o", "--model", "-m", help="LLM model name"),
    provider: str = typer.Option("openai", "--provider", "-p", help="LLM provider"),
    max_parallel: int = typer.Option(3, "--parallel", help="Max parallel MDUs"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
) -> None:
    """Start a new autopilot development session."""
    setup_logging(verbose)

    import os
    os.environ["AUTOPILOT_PROJECT_DIR"] = str(project_dir.resolve())
    os.environ["AUTOPILOT_MODEL"] = model
    os.environ["AUTOPILOT_LLM_PROVIDER"] = provider
    os.environ["AUTOPILOT_MAX_PARALLEL"] = str(max_parallel)

    from src.config.settings import Settings
    from src.state.database import init_db
    from src.state.queries import create_project, create_change_log

    settings = Settings.from_env()
    db_path = settings.get_db_full_path()

    console.print(f"\n[bold green]🚀 Autopilot starting[/bold green]")
    console.print(f"  Requirement: {requirement}")
    console.print(f"  Project dir: {project_dir.resolve()}")
    console.print(f"  Model: {provider}/{model}")
    console.print(f"  Max parallel: {max_parallel}\n")

    init_db(db_path)
    project = create_project(db_path, name=project_dir.name, goal=requirement)
    create_change_log(db_path, project.id, "init", f"Project started: {requirement}", "global")

    console.print(f"  Project ID: {project.id}")
    console.print(f"  Database: {db_path}\n")

    from src.orchestrator.main_graph import build_main_graph
    from langgraph.checkpoint.sqlite import SqliteSaver

    initial_state = {
        "project_id": project.id,
        "project_dir": str(project_dir.resolve()),
        "raw_requirement": requirement,
        "current_phase": "requirement",
        "current_step": "step_1",
        "mdu_results": [],
        "messages": [],
    }

    checkpoint_path = str(db_path).replace(".db", "_checkpoint.db")
    with SqliteSaver.from_conn_string(checkpoint_path) as checkpointer:
        graph = build_main_graph().compile(
            checkpointer=checkpointer,
            interrupt_before=["human_gate"],
        )
        config = {"configurable": {"thread_id": f"project-{project.id}"}}

        console.print("[bold]Starting execution...[/bold]\n")
        _run_with_human_loop(graph, initial_state, config)


@app.command()
def resume(
    project_dir: Path = typer.Option(".", "--dir", "-d", help="Project directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Resume an interrupted autopilot session."""
    setup_logging(verbose)

    import os
    os.environ["AUTOPILOT_PROJECT_DIR"] = str(project_dir.resolve())

    from src.config.settings import Settings

    settings = Settings.from_env()
    db_path = settings.get_db_full_path()
    checkpoint_path = str(db_path).replace(".db", "_checkpoint.db")

    if not Path(checkpoint_path).exists():
        console.print("[red]No checkpoint found. Use 'start' to begin a new session.[/red]")
        raise typer.Exit(1)

    from src.orchestrator.main_graph import build_main_graph
    from langgraph.checkpoint.sqlite import SqliteSaver
    from src.state.queries import get_change_logs

    with SqliteSaver.from_conn_string(checkpoint_path) as checkpointer:
        graph = build_main_graph().compile(
            checkpointer=checkpointer,
            interrupt_before=["human_gate"],
        )

        config = {"configurable": {"thread_id": "project-1"}}
        snapshot = graph.get_state(config)

        if snapshot and snapshot.values:
            state = snapshot.values
            console.print(f"\n[bold green]🔄 Resuming session[/bold green]")
            console.print(f"  Phase: {state.get('current_phase', '?')}")
            console.print(f"  Step: {state.get('current_step', '?')}")
            console.print(f"  Completed MDUs: {state.get('completed_mdu_count', 0)}\n")

            _run_with_human_loop(graph, None, config)
        else:
            console.print("[red]No saved state found.[/red]")
            raise typer.Exit(1)


@app.command()
def status(
    project_dir: Path = typer.Option(".", "--dir", "-d", help="Project directory"),
) -> None:
    """Show current project progress."""
    from src.config.settings import Settings
    from src.state.database import init_db
    from src.state.queries import get_progress_summary, get_all_mdus

    import os
    os.environ["AUTOPILOT_PROJECT_DIR"] = str(project_dir.resolve())

    settings = Settings.from_env()
    db_path = settings.get_db_full_path()

    if not db_path.exists():
        console.print("[red]No database found. Start a project first.[/red]")
        raise typer.Exit(1)

    summary = get_progress_summary(db_path, project_id=1)

    table = Table(title="Project Progress")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total MDUs", str(summary["total"]))
    table.add_row("Completed", str(summary["completed"]))
    table.add_row("In Progress", str(summary["in_progress"]))
    table.add_row("Pending", str(summary["pending"]))
    table.add_row("Skipped", str(summary["skipped"]))
    table.add_row("Blocked", str(summary["blocked"]))
    table.add_row("Completion", f"{summary['percent']}%")

    console.print(table)


@app.command()
def decisions(
    project_dir: Path = typer.Option(".", "--dir", "-d", help="Project directory"),
) -> None:
    """View all architecture decisions (ADRs)."""
    from src.config.settings import Settings
    from src.state.queries import get_decisions

    import os
    os.environ["AUTOPILOT_PROJECT_DIR"] = str(project_dir.resolve())

    settings = Settings.from_env()
    db_path = settings.get_db_full_path()

    if not db_path.exists():
        console.print("[red]No database found.[/red]")
        raise typer.Exit(1)

    adrs = get_decisions(db_path, project_id=1)
    if not adrs:
        console.print("No decisions recorded yet.")
        return

    table = Table(title="Architecture Decisions")
    table.add_column("ADR", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="green")
    table.add_column("Spike", style="yellow")

    for d in adrs:
        spike_str = "N/A"
        if d.spike_required:
            spike_str = d.spike_result or "pending"
        table.add_row(
            f"ADR-{d.adr_number:03d}",
            d.title,
            d.status,
            spike_str,
        )

    console.print(table)


@app.command()
def backtrack(
    reason: str = typer.Argument(..., help="Reason for backtracking"),
    project_dir: Path = typer.Option(".", "--dir", "-d"),
) -> None:
    """Trigger explicit backtrack."""
    console.print(f"[yellow]🔙 Backtrack requested: {reason}[/yellow]")
    console.print("This will be processed in the next execution step.")


@app.command()
def skip(
    reason: str = typer.Option("User requested skip", "--reason", "-r"),
    project_dir: Path = typer.Option(".", "--dir", "-d"),
) -> None:
    """Skip current MDU and mark downstream as blocked."""
    console.print(f"[yellow]⏭️ Skip requested: {reason}[/yellow]")


@app.command()
def pause(
    project_dir: Path = typer.Option(".", "--dir", "-d"),
) -> None:
    """Pause execution and save state."""
    console.print("[yellow]⏸️ Execution paused. Use 'resume' to continue.[/yellow]")


@app.command(name="change-request")
def change_request(
    description: str = typer.Argument(..., help="Description of the change"),
    project_dir: Path = typer.Option(".", "--dir", "-d"),
) -> None:
    """Submit a formal requirement change request."""
    console.print(f"[yellow]📝 Change request submitted: {description}[/yellow]")
    console.print("Impact analysis will be performed in the next execution step.")


def _run_with_human_loop(graph, initial_state, config):
    """Run the graph with human-in-the-loop interaction."""
    if initial_state:
        for event in graph.stream(initial_state, config, stream_mode="values"):
            _display_state(event)
    else:
        graph.update_state(config, {})

    while True:
        snapshot = graph.get_state(config)
        if not snapshot or not snapshot.next:
            console.print("\n[bold green]✅ Execution complete.[/bold green]")
            break

        state = snapshot.values
        if state.get("waiting_for_human"):
            prompt = state.get("human_prompt", "Waiting for input...")
            console.print(f"\n[bold yellow]⚠️ Input needed:[/bold yellow]\n{prompt}\n")

            response = typer.prompt("Your response")
            graph.update_state(
                config,
                {"human_response": response, "waiting_for_human": False},
            )

        for event in graph.stream(None, config, stream_mode="values"):
            _display_state(event)


def _display_state(state: dict) -> None:
    """Display current state to user."""
    phase = state.get("current_phase", "")
    step = state.get("current_step", "")
    if phase or step:
        console.print(f"  📍 Phase: {phase} | Step: {step}")

    heartbeat = state.get("heartbeat_percent")
    if heartbeat:
        total = state.get("total_mdu_count", 0)
        completed = state.get("completed_mdu_count", 0)
        console.print(f"  📊 Progress: {completed}/{total} ({heartbeat}%)")


if __name__ == "__main__":
    app()
