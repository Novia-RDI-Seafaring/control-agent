"""CLI interface for the mcp_fmi_ecc26 package using Typer."""

import typer
from .zn import ZieglerNicholsMethod, FOPDT


def main(
    K: float = typer.Option(2.0, "--K", help="Static process gain"),
    T: float = typer.Option(1.0, "--T", help="Process time constant [s]"),
    L: float = typer.Option(0.5, "--L", help="Effective time delay [s]"),
):
    """
    Ziegler-Nichols Method CLI for FOPDT system analysis.
    
    Calculates ultimate point and PI controller parameters for a First-Order
    Plus Dead Time (FOPDT) system using the Ziegler-Nichols closed-loop method.
    """
    try:
        # Create FOPDT system
        sys_pars = FOPDT(K=K, T=T, L=L)
        
        # Create Ziegler-Nichols method instance
        zn_method = ZieglerNicholsMethod(sys_pars)
        
        # Display results
        typer.echo("Ziegler-Nichols Method Results")
        typer.echo("=" * 40)
        typer.echo(f"System Parameters: K={K}, T={T}, L={L}")
        typer.echo(f"Ultimate Point: {zn_method.ultimate_point}")
        typer.echo(f"PI Controller: {zn_method.pi_controller}")
        typer.echo("=" * 40)
        
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    typer.run(main)
