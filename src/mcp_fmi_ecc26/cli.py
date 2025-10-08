import typer
from mcp_fmi_ecc26 import ZieglerNicholsMethod, FOPDT

app = typer.Typer()


@app.command()
def main(
    K: float = typer.Option(..., "--K", help="Static process gain K"),
    T: float = typer.Option(..., "--T", help="Process time constant T"),
    L: float = typer.Option(..., "--L", help="Effective time delay L"),
    method: str = typer.Option("zn", "--method", help="Tuning method (zn)"),
):
    """FOPDT system analysis CLI.
    
    System parameters: K (gain), T (time constant), L (time delay)
    Methods: zn (Ziegler-Nichols)
    """
    
    if method.lower() != "zn":
        typer.echo(f"Error: Unknown method '{method}'. Available: zn", err=True)
        raise typer.Exit(1)
    
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
