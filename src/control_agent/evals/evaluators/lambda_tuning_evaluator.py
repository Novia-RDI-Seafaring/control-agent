from dataclasses import dataclass
from control_agent.experiment_definitions.response_schema import LambdaTuningResponse
from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from control_agent import FOPDT
from control_agent.lam import LambdaTuningMethod
from logging import getLogger

logger = getLogger(__name__)


@dataclass
class LambdaTuningEvaluator(Evaluator[object, object, object]):
    """Evaluate lambda tuning results against ground truth"""
    tolerance: float = 0.05  # 5% tolerance
    
    def evaluate(self, ctx: EvaluatorContext[object, LambdaTuningResponse, object]) -> EvaluationReason:
        """Compare lambda tuning results with ground truth"""
        # Calculate ground truth using the same library
        output: LambdaTuningResponse = ctx.output
        system = output.system_parameters
        lam_method = LambdaTuningMethod(FOPDT(K=system.K, T=system.T, L=system.L), lam=output.lambda_parameter)
        ground_truth_Kp = lam_method.pi_controller.K_p
        ground_truth_Ti = lam_method.pi_controller.T_i
        Kp = output.controller_parameters.Kp
        Ti = output.controller_parameters.Ti
        
        # Calculate relative errors
        kp_error = abs(Kp - ground_truth_Kp) / ground_truth_Kp if ground_truth_Kp != 0 else abs(Kp - ground_truth_Kp)
        ti_error = abs(Ti - ground_truth_Ti) / ground_truth_Ti if ground_truth_Ti != 0 else abs(Ti - ground_truth_Ti)
        
        # Check if parameters are within tolerance
        if kp_error <= self.tolerance and ti_error <= self.tolerance:
            return EvaluationReason(
                value=True,
                reason=f"Controller parameters match ground truth (Kp={Kp:.3f}, Ti={Ti:.3f}, λ={output.lambda_parameter:.3f})"
            )
        else:
            return EvaluationReason(
                value=False,
                reason=f"Parameter errors exceed tolerance: Kp={kp_error:.2%}, Ti={ti_error:.2%} "
                       f"(expected Kp={ground_truth_Kp:.3f}, Ti={ground_truth_Ti:.3f})"
            )