from dataclasses import dataclass
from typing import Dict, Any, Optional, Union

from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from control_agent.evals.utils import get_tool_result, parse_result
from logging import getLogger

logger = getLogger(__name__)


@dataclass
class ToolCallResultEvaluator(Evaluator[object, object, object]):
    """Evaluate that a tool call produces results within expected range/tolerance"""
    agent_name: str
    tool_name: str
    expected_values: Dict[str, Union[float, int]]  # e.g., {'K': 1.0, 'T': 1.0, 'L': 0.5}
    tolerance: float = 0.05  # 5% tolerance (relative error)
    absolute_tolerance: Optional[float] = None  # Optional absolute tolerance
    
    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> EvaluationReason:
        """Check that tool call result matches expected values within tolerance"""
        # Get the tool result
        tool_result = get_tool_result(ctx, self.agent_name, self.tool_name)
        
        if tool_result is None:
            return EvaluationReason(
                value=False,
                reason=f"Tool '{self.tool_name}' was not called or result not found"
            )
        
        # Parse tool result - handle different formats
        result_dict = parse_result(tool_result)
        if result_dict is None:
            return EvaluationReason(
                value=False,
                reason=f"Could not parse tool result: {type(tool_result)}"
            )
        
        # Validate each expected value
        errors = []
        for key, expected_value in self.expected_values.items():
            actual_value = result_dict.get(key)
            
            if actual_value is None:
                errors.append(f"{key}: not found in result")
                continue
            
            # Calculate error
            if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                # Use absolute tolerance if specified, otherwise relative
                if self.absolute_tolerance is not None:
                    error = abs(actual_value - expected_value)
                    if error > self.absolute_tolerance:
                        errors.append(f"{key}: {actual_value:.3f} (expected {expected_value:.3f} ± {self.absolute_tolerance:.3f})")
                else:
                    # Relative error
                    if expected_value != 0:
                        relative_error = abs(actual_value - expected_value) / abs(expected_value)
                        if relative_error > self.tolerance:
                            errors.append(f"{key}: {actual_value:.3f} (expected {expected_value:.3f}, error {relative_error:.2%})")
                    else:
                        # If expected is 0, use absolute tolerance
                        error = abs(actual_value - expected_value)
                        if error > (self.absolute_tolerance or 0.01):
                            errors.append(f"{key}: {actual_value:.3f} (expected {expected_value:.3f})")
            else:
                # For non-numeric values, exact match
                if actual_value != expected_value:
                    errors.append(f"{key}: {actual_value} (expected {expected_value})")
        
        if errors:
            return EvaluationReason(
                value=False,
                reason=f"Tool '{self.tool_name}' result validation failed: {', '.join(errors)}"
            )
        
        return EvaluationReason(
            value=True,
            reason=f"Tool '{self.tool_name}' result matches expected values within tolerance"
        )


@dataclass
class ToolCallResultRangeEvaluator(Evaluator[object, object, object]):
    """Evaluate that a tool call produces results within a range (min/max)"""
    agent_name: str
    tool_name: str
    value_ranges: Dict[str, tuple[float, float]]  # e.g., {'K': (0.8, 1.2), 'T': (0.9, 1.1)}
    
    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> EvaluationReason:
        """Check that tool call result values are within specified ranges"""
        tool_result = get_tool_result(ctx, self.agent_name, self.tool_name)
        
        if tool_result is None:
            return EvaluationReason(
                value=False,
                reason=f"Tool '{self.tool_name}' was not called or result not found"
            )
        
        # Parse tool result
        result_dict = parse_result(tool_result)
        if result_dict is None:
            return EvaluationReason(
                value=False,
                reason=f"Could not parse tool result: {type(tool_result)}"
            )
        
        # Validate each value is within range
        errors = []
        for key, (min_val, max_val) in self.value_ranges.items():
            actual_value = result_dict.get(key)
            
            if actual_value is None:
                errors.append(f"{key}: not found in result")
                continue
            
            if isinstance(actual_value, (int, float)):
                if actual_value < min_val or actual_value > max_val:
                    errors.append(f"{key}: {actual_value:.3f} (expected range [{min_val:.3f}, {max_val:.3f}])")
            else:
                errors.append(f"{key}: {actual_value} (expected numeric value)")
        
        if errors:
            return EvaluationReason(
                value=False,
                reason=f"Tool '{self.tool_name}' result validation failed: {', '.join(errors)}"
            )
        
        return EvaluationReason(
            value=True,
            reason=f"Tool '{self.tool_name}' result values are within expected ranges"
        )
