from dataclasses import dataclass
from typing import List

from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluatorOutput,
    EvaluationReason,
)

@dataclass
class ListModels_Evaluator(Evaluator[object, object, object]):
    model_names: List[str]
    
    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> EvaluatorOutput:
        if not hasattr(ctx.output, 'model_names'):
            print(ctx.output)
            return EvaluationReason(value=False, reason=f"Output does not have a model_names attribute")
        
        if ctx.output is None:
            return EvaluationReason(value=False, reason="Output is None")
        
        _value = getattr(ctx.output, 'model_names', [])
        
        if not isinstance(_value, list):
            return EvaluationReason(value=False, reason="Output model_names is not a list")
        
        if len(_value) != len(self.model_names):
            return EvaluationReason(value=False, reason="Output model_names list length does not match expected length")
        
        if not all(item in _value for item in self.model_names):
            return EvaluationReason(value=False, reason="Output model_names list does not contain all expected model names")
        
        return EvaluationReason(value=True, reason="Output model_names list contains all expected model names")
