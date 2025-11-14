"""Tuning methods for control systems."""
from control_agent.domain.tuning.ziegler_nichols import ZieglerNicholsMethod, UltimatePoint
from control_agent.domain.tuning.lambda_tuning import LambdaTuningMethod

__all__ = [
    "ZieglerNicholsMethod",
    "UltimatePoint",
    "LambdaTuningMethod",
]

