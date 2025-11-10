from dataclasses import dataclass

from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from control_agent import FOPDT
from control_agent import ZieglerNicholsMethod
from logging import getLogger

logger = getLogger(__name__)


@dataclass
class ZieglerNicholsEvaluator(Evaluator[object, object, object]):
    """Evaluate Ziegler-Nichols tuning results against ground truth"""
    ground_truth_K: float
    ground_truth_T: float
    ground_truth_L: float
    tolerance: float = 0.05  # 5% tolerance
    
    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> EvaluationReason:
        """Compare Ziegler-Nichols tuning results with ground truth"""
        # Calculate ground truth using the same library
        system = FOPDT(
            K=self.ground_truth_K,
            T=self.ground_truth_T,
            L=self.ground_truth_L
        )
        zn_method = ZieglerNicholsMethod(system)
        ground_truth_Kp = zn_method.pi_controller.K_p
        ground_truth_Ti = zn_method.pi_controller.T_i
        
        # Parse agent output
        output = ctx.output
        if isinstance(output, dict):
            # Try different possible structures
            controller = output.get('controller_parameters', {})
            if not controller:
                controller = output.get('pid_parameters', {})
            if not controller:
                controller = output  # Maybe output is the controller directly
            
            Kp = controller.get('Kp') or controller.get('K_p')
            Ti = controller.get('Ti') or controller.get('T_i')
        else:
            logger.error(f"Could not parse output: {type(output)}")
            return EvaluationReason(value=False, reason=f"Could not parse output: expected dict, got {type(output)}")
        
        if Kp is None or Ti is None:
            return EvaluationReason(value=False, reason="Missing controller parameters: Kp or Ti not found in output")
        
        # Calculate relative errors
        kp_error = abs(Kp - ground_truth_Kp) / ground_truth_Kp if ground_truth_Kp != 0 else abs(Kp - ground_truth_Kp)
        ti_error = abs(Ti - ground_truth_Ti) / ground_truth_Ti if ground_truth_Ti != 0 else abs(Ti - ground_truth_Ti)
        
        # Check if parameters are within tolerance
        if kp_error <= self.tolerance and ti_error <= self.tolerance:
            return EvaluationReason(
                value=True,
                reason=f"Controller parameters match ground truth (Kp={Kp:.3f}, Ti={Ti:.3f})"
            )
        else:
            return EvaluationReason(
                value=False,
                reason=f"Parameter errors exceed tolerance: Kp={kp_error:.2%}, Ti={ti_error:.2%} "
                       f"(expected Kp={ground_truth_Kp:.3f}, Ti={ground_truth_Ti:.3f})"
            )