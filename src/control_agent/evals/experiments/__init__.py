from . import *

import importlib
import pkgutil

# Dynamically discover and import all submodules in this package
datasets = {}

__all__ = []
for module_info in pkgutil.iter_modules(__path__):
    module_name = module_info.name
    # Import the submodule
    module = importlib.import_module(f"{__name__}.{module_name}")
    if hasattr(module, "dataset") and hasattr(module, "OutputDataT"):
        dataset = module.dataset
        OutputDataT = module.OutputDataT
        name = dataset.name or module_name
        datasets[name] = (dataset, OutputDataT)

    elif not module_name == "demo":
        raise ValueError(f"Module {module_name} does not have a dataset or agent_runner")
    __all__.append(module_name)

__all__.append('datasets')