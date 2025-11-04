from pathlib import Path
from typing import Optional

# Default FMU directory path (fallback if not set via set_fmu_dir)
DEFAULT_FMU_DIR = (Path(__file__).parents[2] / "models" / "fmus").resolve()

# Global FMU directory configuration
_fmu_dir: Optional[Path] = None

def set_fmu_dir(path: Path) -> None:
    """Set the FMU directory path."""
    global _fmu_dir
    if not path.exists():
        raise ValueError(f"FMU directory does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    _fmu_dir = path.resolve()

def get_fmu_dir() -> Path:
    """Get the FMU directory path. Returns DEFAULT_FMU_DIR if not set."""
    global _fmu_dir
    if _fmu_dir is None:
        return DEFAULT_FMU_DIR
    return _fmu_dir

def reset_fmu_dir() -> None:
    """Reset the FMU directory to None."""
    global _fmu_dir
    _fmu_dir = None

