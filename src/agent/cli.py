"""Interactive CLI for the FMI Agent."""

import sys
from typing import Optional
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from agent.api import FMIAgent

app = typer.Typer(help="FMI Agent CLI for PI Controller Tuning")
console = Console()


@app.command()
def chat(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Azure OpenAI deployment name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    max_iterations: int = typer.Option(20, "--max-iterations", help="Maximum agent iterations"),
):
    """Start interactive chat session with FMI Agent."""
    console.print(Panel.fit(
        "[bold cyan]FMI Agent - PI Controller Tuning Assistant[/bold cyan]\n"
        "Type your queries or commands:\n"
        "  • [yellow]'exit'[/yellow] or [yellow]'quit'[/yellow] to end session\n"
        "  • [yellow]'help'[/yellow] for example queries\n"
        "  • [yellow]'clear'[/yellow] to clear screen",
        border_style="cyan"
    ))
    
    # Initialize agent
    try:
        console.print("\n[cyan]Initializing agent...[/cyan]")
        agent = FMIAgent(
            model_name=model,
            verbose=verbose,
            max_iterations=max_iterations,
        )
        console.print("[green]✓ Agent ready![/green]\n")
    except Exception as e:
        console.print(f"[red]✗ Error initializing agent: {e}[/red]")
        console.print("[yellow]Make sure your Azure OpenAI credentials are set in .env file[/yellow]")
        sys.exit(1)
    
    # Main loop
    while True:
        try:
            # Get user input
            query = Prompt.ask("\n[bold green]You[/bold green]")
            
            if not query.strip():
                continue
            
            # Handle commands
            if query.lower() in ["exit", "quit", "q"]:
                console.print("\n[cyan]Goodbye![/cyan]")
                break
            
            if query.lower() == "clear":
                console.clear()
                continue
            
            if query.lower() == "help":
                show_help()
                continue
            
            # Run agent
            console.print("\n[cyan]Agent:[/cyan] Thinking...\n")
            result = agent.run(query)
            
            if result.get("success"):
                # Display output
                console.print(Panel(
                    Markdown(result["output"]),
                    title="[bold cyan]Agent Response[/bold cyan]",
                    border_style="cyan"
                ))
                
                # Show tool usage if verbose
                if verbose and result.get("intermediate_steps"):
                    show_tool_usage(result["intermediate_steps"])
            else:
                console.print(f"[red]✗ Error: {result.get('error', 'Unknown error')}[/red]")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            continue
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")


@app.command()
def query(
    text: str = typer.Argument(..., help="Query to run"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Azure OpenAI deployment name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    evaluate: bool = typer.Option(False, "--eval", help="Enable evaluation mode"),
    ground_truth_method: Optional[str] = typer.Option(None, "--gt-method", help="Ground truth method (zn/lambda)"),
    K: Optional[float] = typer.Option(None, help="FOPDT parameter K for ground truth"),
    T: Optional[float] = typer.Option(None, help="FOPDT parameter T for ground truth"),
    L: Optional[float] = typer.Option(None, help="FOPDT parameter L for ground truth"),
    lam: Optional[float] = typer.Option(None, help="Lambda parameter for lambda tuning"),
):
    """Run a single query and exit."""
    # Initialize agent
    agent = FMIAgent(
        model_name=model,
        verbose=verbose,
        evaluate=evaluate,
    )
    
    # Prepare ground truth params
    ground_truth_params = None
    if ground_truth_method and K is not None and T is not None and L is not None:
        ground_truth_params = {"K": K, "T": T, "L": L}
        if lam is not None:
            ground_truth_params["lambda"] = lam
    
    # Run query
    console.print(f"\n[bold cyan]Query:[/bold cyan] {text}\n")
    result = agent.run(
        query=text,
        ground_truth_method=ground_truth_method,
        ground_truth_params=ground_truth_params,
    )
    
    if result.get("success"):
        console.print(Panel(
            Markdown(result["output"]),
            title="[bold cyan]Agent Response[/bold cyan]",
            border_style="cyan"
        ))
        
        # Show evaluation if available
        if "evaluation" in result:
            show_evaluation(result["evaluation"])
    else:
        console.print(f"[red]✗ Error: {result.get('error')}[/red]")
        sys.exit(1)


def show_help():
    """Display example queries."""
    console.print(Panel(
        "[bold]Example Queries:[/bold]\n\n"
        "• What simulation models do you have available?\n"
        "• Simulate an open-loop step response with input change from 0 to 1\n"
        "• Simulate a closed-loop step response with setpoint change from 0 to 1\n"
        "• Make a step response and identify a FOPDT model\n"
        "• Tune the PI controller with Lambda tuning lambda = 1.0\n"
        "• Tune the PI controller with Lambda tuning for fast response\n"
        "• Tune the PI controller using Ziegler-Nichols closed-loop method\n"
        "• Change the control parameters to K_p = 1.0 and T_i = 2.0",
        title="[bold cyan]Help[/bold cyan]",
        border_style="cyan"
    ))


def show_tool_usage(intermediate_steps):
    """Display tool usage table."""
    table = Table(title="Tool Usage", show_header=True, header_style="bold cyan")
    table.add_column("Step", style="cyan")
    table.add_column("Tool", style="yellow")
    table.add_column("Status", style="green")
    
    for i, step in enumerate(intermediate_steps, 1):
        if len(step) >= 2:
            action = step[0]
            observation = step[1]
            tool_name = getattr(action, "tool", "unknown")
            status = "✓" if observation else "✗"
            table.add_row(str(i), tool_name, status)
    
    console.print("\n")
    console.print(table)


def show_evaluation(evaluation):
    """Display evaluation results."""
    table = Table(title="Evaluation Results", show_header=True, header_style="bold cyan")
    table.add_column("Parameter", style="cyan")
    table.add_column("Agent", style="yellow")
    table.add_column("Ground Truth", style="green")
    table.add_column("Error %", style="red")
    
    if evaluation.agent_Kp is not None:
        table.add_row(
            "Kp",
            f"{evaluation.agent_Kp:.4f}",
            f"{evaluation.ground_truth_Kp:.4f}" if evaluation.ground_truth_Kp else "N/A",
            f"{evaluation.Kp_error_percent:.2f}%" if evaluation.Kp_error_percent else "N/A"
        )
    
    if evaluation.agent_Ti is not None:
        table.add_row(
            "Ti",
            f"{evaluation.agent_Ti:.4f}",
            f"{evaluation.ground_truth_Ti:.4f}" if evaluation.ground_truth_Ti else "N/A",
            f"{evaluation.Ti_error_percent:.2f}%" if evaluation.Ti_error_percent else "N/A"
        )
    
    console.print("\n")
    console.print(table)
    
    status = "[green]PASSED ✓[/green]" if evaluation.passed else "[red]FAILED ✗[/red]"
    console.print(f"\nStatus: {status}")


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()

