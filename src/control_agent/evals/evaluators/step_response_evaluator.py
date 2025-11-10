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
        output = ctx.output
        
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
            # Try to check if it's a DataModel object
            if hasattr(output, 'timestamps') and hasattr(output, 'signals'):
                return EvaluationReason(value=True, reason="Step response has valid DataModel structure")
            
            return EvaluationReason(value=False, reason=f"Output is not a valid step response format: {type(output)}")


