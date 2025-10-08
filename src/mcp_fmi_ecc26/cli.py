import typer
from mcp_fmi_ecc26 import ZieglerNicholsMethod, FOPDT

app = typer.Typer()


@app.command()
def main(
    K: float = typer.Option(1.0, "--K", help="Static process gain, K>0"),
    T: float = typer.Option(1.0, "--T", help="Process time constant, T>0"),
    L: float = typer.Option(1.0, "--L", help="Effective time delay, L>0"),
):
    """Ziegler-Nichols Method CLI for FOPDT system analysis."""
    try:
        sys_pars = FOPDT(K=K, T=T, L=L)
        zn_method = ZieglerNicholsMethod(sys_pars)
        
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
    app()
