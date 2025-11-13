from dataclasses import dataclass
from typing import List

from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from logging import getLogger

logger = getLogger(__name__)


@dataclass
class StepResponseEvaluator(Evaluator[object, object, object]):
    """Evaluate step response structure (DataModel format)"""
    
    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> EvaluationReason:
        """Check that output is a valid step response (DataModel)"""
        # Extract the actual output from AgentRunResult -> CaseResponse -> StepResponse
        output = ctx.output
        
        # If ctx.output is an AgentRunResult, extract the nested output
        if hasattr(output, 'output'):
            output = output.output
        
        # If it's a CaseResponse, extract the nested output
        if hasattr(output, 'output'):
            output = output.output
        
        # Check if output has the expected structure
        if isinstance(output, dict):
            # Check for timestamps
            if 'timestamps' not in output and 'timestamps' not in str(output).lower():
                return EvaluationReason(value=False, reason="Missing timestamps in step response")
            
            # Check for signals/outputs
            has_signals = 'signals' in output or 'outputs' in output or 'inputs' in output
            if not has_signals:
                return EvaluationReason(value=False, reason="Missing signals/outputs in step response")
            
            return EvaluationReason(value=True, reason="Step response has valid structure")
        else:
            # Try to check if it's a DataModel object or StepResponse
            if hasattr(output, 'timestamps'):
                # Check if it has signals or outputs/inputs
                has_data = (hasattr(output, 'signals') or 
                           hasattr(output, 'outputs') or 
                           hasattr(output, 'inputs'))
                if has_data:
                    return EvaluationReason(value=True, reason="Step response has valid structure")
            
            return EvaluationReason(value=False, reason=f"Output is not a valid step response format: {type(output)}")


