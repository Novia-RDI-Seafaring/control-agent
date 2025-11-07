from .tool_info import dataset as info_ds
from .sys import dataset as sys_ds
from .lam import dataset as lam_ds
from .zn import dataset as zn_ds

from pydantic_evals import Case, Dataset
from typing import Dict, Any

all = {
    'info': info_ds,
    'sys': sys_ds,
    'lam': lam_ds,
    'zn': zn_ds,
}