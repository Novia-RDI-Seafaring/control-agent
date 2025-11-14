from . import *

import importlib
import pkgutil

# Dynamically discover and import all submodules in this package
datasets = {}

__all__ = []
for module_info in pkgutil.iter_modules(__path__):
    module_name = module_info.name
    # Skip old/backup files
    #if module_name.endswith('_old'):
    #    continue
    # Import the submodule
    module = importlib.import_module(f"{__name__}.{module_name}")
    if hasattr(module, "dataset") and hasattr(module, "OutputDataT"):
        dataset = module.dataset
        OutputDataT = module.OutputDataT
        name = dataset.name or module_name
        # Debug: Print evaluators before storing
    #    if dataset.cases:
    #        import sys
    #        evaluator_names = [type(e).__name__ for e in dataset.cases[0].evaluators]
    #        print(f"[DEBUG] {name}: Evaluators before storing: {evaluator_names}", file=sys.stderr, flush=True)
        datasets[name] = (dataset, OutputDataT)
        # Debug: Print evaluators after storing
    #    if dataset.cases:
    #        import sys
    #        evaluator_names = [type(e).__name__ for e in dataset.cases[0].evaluators]
    #        print(f"[DEBUG] {name}: Evaluators after storing: {evaluator_names}", file=sys.stderr, flush=True)

    elif not module_name == "demo":
        raise ValueError(f"Module {module_name} does not have a dataset or agent_runner")
    __all__.append(module_name)

__all__.append('datasets')