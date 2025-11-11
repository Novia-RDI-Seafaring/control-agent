from dataclasses import dataclass
from control_agent.experiment_definitions.response_schema import LambdaTuningResponse
from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from control_agent import FOPDT
#from control_agent.lam import LambdaTuningMethod
from logging import getLogger

from control_toolbox.tools.pid_tuning import lambda_tuning as _lambda_tuning
from control_toolbox.tools.pid_tuning import LambdaTuningProps
from control_toolbox.tools.pid_tuning import PIDParameters
logger = getLogger(__name__)


@dataclass
class LambdaTuningEvaluator(Evaluator[object, object, object]):
    """Evaluate lambda tuning results against ground truth"""
    tolerance: float = 0.10  # 10% tolerance
    
    def evaluate(self, ctx: EvaluatorContext[object, LambdaTuningResponse, object]) -> EvaluationReason:
        """Compare lambda tuning results with ground truth"""
        # Calculate ground truth using the same library
        output: LambdaTuningResponse = ctx.output
        lam_method = _lambda_tuning(
            FOPDT(K=1.0, T=2.0, L=1.0),
            props=LambdaTuningProps(
                controller = "pi",
                response = "balanced"
            )
        )
        ground_truth_Kp = lam_method.Kp
        ground_truth_Ti = lam_method.Ti
        ground_truth_Td = lam_method.Td
        Kp = output.controller_parameters.Kp
        Ti = output.controller_parameters.Ti
        Td = output.controller_parameters.Td
        
        # Calculate relative errors
        kp_error = abs(Kp - ground_truth_Kp) / ground_truth_Kp if ground_truth_Kp != 0 else abs(Kp - ground_truth_Kp)
        ti_error = abs(Ti - ground_truth_Ti) / ground_truth_Ti if ground_truth_Ti != 0 else abs(Ti - ground_truth_Ti)
        td_error = abs(Td - ground_truth_Td) / ground_truth_Td if ground_truth_Td != 0 else abs(Td - ground_truth_Td)

        # Check if parameters are within tolerance
        if kp_error <= self.tolerance and ti_error <= self.tolerance and td_error <= self.tolerance:
            return EvaluationReason(
                value=True,
                reason=f"Controller parameters match ground truth (Kp={Kp:.3f}, Ti={Ti:.3f}, Td={Td:.3f})"  
            )
        else:
            return EvaluationReason(
                value=False,
                reason=f"Parameter errors exceed tolerance: Kp={kp_error:.2%}, Ti={ti_error:.2%}, Td={td_error:.2%} "
                       f"(expected Kp={ground_truth_Kp:.3f}, Ti={ground_truth_Ti:.3f}, Td={ground_truth_Td:.3f})"
            )