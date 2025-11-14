from dataclasses import dataclass
from typing import Dict, Any
from control_agent.evals.schemas.responses import CaseResponse, SystemIdentificationResponse, SystemParameters
from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from control_agent import FOPDT
from logging import getLogger

logger = getLogger(__name__)


@dataclass
class SystemIdentificationEvaluator(Evaluator[object, CaseResponse[SystemIdentificationResponse], object]):
    """Evaluate system identification results against ground truth FOPDT parameters"""
    ground_truth_K: float
    ground_truth_T: float
    ground_truth_L: float
    tolerance: float = 0.05  # 5% tolerance
    
    def evaluate(self, ctx: EvaluatorContext[object, CaseResponse[SystemIdentificationResponse], object]) -> EvaluationReason:
        """Compare identified parameters with ground truth"""
        output: SystemIdentificationResponse = ctx.output.output
        system_parameters: SystemParameters = output.parameters

        K = system_parameters.K
        T = system_parameters.T
        L = system_parameters.L
        
        # Calculate relative errors
        k_error = abs(K - self.ground_truth_K) / self.ground_truth_K if self.ground_truth_K != 0 else abs(K - self.ground_truth_K)
        t_error = abs(T - self.ground_truth_T) / self.ground_truth_T if self.ground_truth_T != 0 else abs(T - self.ground_truth_T)
        l_error = abs(L - self.ground_truth_L) / self.ground_truth_L if self.ground_truth_L != 0 else abs(L - self.ground_truth_L)
        
        # Check if all parameters are within tolerance
        if k_error <= self.tolerance and t_error <= self.tolerance and l_error <= self.tolerance:
            return EvaluationReason(
                value=True,
                reason=f"System parameters match ground truth (K={K:.3f}, T={T:.3f}, L={L:.3f})"
            )
        else:
            return EvaluationReason(
                value=False,
                reason=f"Parameter errors exceed tolerance: K={k_error:.2%}, T={t_error:.2%}, L={l_error:.2%} "
                       f"(expected K={self.ground_truth_K:.3f}, T={self.ground_truth_T:.3f}, L={self.ground_truth_L:.3f})"
            )
