from dataclasses import dataclass
from control_agent.experiment_definitions.response_schema import CaseResponse
from control_agent.experiment_definitions.response_schema import LambdaTuningResponse
from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from control_agent import FOPDT
#from control_agent.lam import LambdaTuningMethod
from logging import getLogger
import numpy as np

from control_toolbox.tools.pid_tuning import lambda_tuning as _lambda_tuning
from control_toolbox.tools.pid_tuning import LambdaTuningProps
from control_toolbox.tools.pid_tuning import PIDParameters
logger = getLogger(__name__)

def _relative_error(x: float, y: float) -> float:
    return abs(x - y) / y if y != 0 else abs(x - y)

@dataclass
class LambdaTuningEvaluator(Evaluator[object, CaseResponse[LambdaTuningResponse], object]):
    """Evaluate lambda tuning results against ground truth"""
    tolerance: float = 0.10  # 10% tolerance
    gt_Kp: float = 1.0
    gt_Ti: float = 2.0
    gt_Td: float = 0.0
    gt_response: str = "balanced"
    
    def evaluate(self, ctx: EvaluatorContext[object, LambdaTuningResponse, object]) -> EvaluationReason:
        """Compare lambda tuning results with ground truth"""
        # Calculate ground truth using the same library
        output = ctx.output
        if hasattr(output, 'output'):
            output = output.output
        if hasattr(output, 'output'):
            output = output.output

        if not isinstance(output, LambdaTuningResponse):
                    return EvaluationReason(
                        value=False,
                        reason=f"Output is not of type LambdaTuningResponse. Got {type(output).__name__!r}."
                    )

        gt_pid_parameters = _lambda_tuning(
            FOPDT(K=1.0, T=2.0, L=1.0),
            props=LambdaTuningProps(
                controller = "pi",
                response = self.gt_response,
            )
        )
        
        # Calculate relative errors
        Kp = output.controller_parameters.Kp
        Ti = output.controller_parameters.Ti
        Td = output.controller_parameters.Td

        kp_error = _relative_error(Kp, gt_pid_parameters.Kp)
        ti_error = _relative_error(Ti, gt_pid_parameters.Ti)
        td_error = _relative_error(Td, gt_pid_parameters.Td)

        # Check if parameters are within tolerance
        if kp_error <= self.tolerance and ti_error <= self.tolerance and td_error <= self.tolerance:
            return EvaluationReason(
                value=True,
                reason=f"Parameter errors match the ground truth: Kp_error={kp_error:.2%}, Ti_error={ti_error:.2%}, Td_error={td_error:.2%} "
                       f"(expected Kp={self.gt_Kp:.3f}, Ti={self.gt_Ti:.3f}, Td={self.gt_Td:.3f})"
            )
        else:
            return EvaluationReason(
                value=False,
                reason=f"Parameter errors exceed tolerance: Kp_error={kp_error:.2%}, Ti_error={ti_error:.2%}, Td_error={td_error:.2%} "
                       f"(expected Kp={self.gt_Kp:.3f}, Ti={self.gt_Ti:.3f}, Td={self.gt_Td:.3f})"
            )