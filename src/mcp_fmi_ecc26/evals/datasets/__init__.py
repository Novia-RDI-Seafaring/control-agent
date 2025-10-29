from .sys import dataset as sys_ds
from .lam import dataset as lam_ds
from .zn import dataset as zn_ds

from pydantic_evals import Case, Dataset
from typing import Dict, Any

all: Dict[str, Dataset["str", "str", Any]] = {
    "sys": sys_ds,
    "lam": lam_ds,
    "zn": zn_ds,
}

__all__ = ["all", "sys_ds", "lam_ds", "zn_ds"]