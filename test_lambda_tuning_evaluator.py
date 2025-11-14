"""Test script for LambdaTuningEvaluator without running the full agent.

NOTE: There's a bug in lambda_tuning_evaluator.py line 47 - it references
self.gt_K, self.gt_T, self.gt_L which are not defined in the dataclass.
You'll need to add these fields or fix the reference.
"""

from typing import Any
from control_agent.evals.evaluators.lambda_tuning_evaluator import LambdaTuningEvaluator
from control_agent.experiment_definitions.response_schema import (
    LambdaTuningResponse, 
    CaseResponse,
    SystemParameters,
    PIDParameters
)
from pydantic_evals.evaluators import EvaluatorContext


class MockEvaluatorContext:
    """Mock EvaluatorContext for testing"""
    def __init__(self, output: Any, input: Any = None, expected: Any = None):
        self.output = output
        self.input = input
        self.expected = expected


def test_lambda_tuning_evaluator():
    """Test the lambda tuning evaluator with sample data"""
    
    print("=" * 60)
    print("Testing LambdaTuningEvaluator")
    print("=" * 60)
    
    # Create evaluator with custom ground truth values
    # NOTE: You may need to add gt_K, gt_T, gt_L to the evaluator class
    evaluator = LambdaTuningEvaluator(
        tolerance=0.10,
        gt_Kp=1.0,
        gt_Ti=2.0,
        gt_Td=0.0,
        gt_response="balanced"
    )
    
    # Test case 1: Perfect match
    print("\n--- Test 1: Perfect match ---")
    sample_response_1 = LambdaTuningResponse(
        system_parameters=SystemParameters(K=1.0, T=2.0, L=1.0),
        controller_parameters=PIDParameters(Kp=1.0, Ti=2.0, Td=0.0),
        lambda_parameter=1.0
    )
    case_response_1 = CaseResponse(output=sample_response_1)
    ctx_1 = MockEvaluatorContext(output=case_response_1)
    
    try:
        result_1 = evaluator.evaluate(ctx_1)
        print(f"✓ Evaluation result: {result_1.value}")
        print(f"  Reason: {result_1.reason}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test case 2: Parameters outside tolerance
    print("\n--- Test 2: Parameters outside tolerance ---")
    sample_response_2 = LambdaTuningResponse(
        system_parameters=SystemParameters(K=1.0, T=2.0, L=1.0),
        controller_parameters=PIDParameters(Kp=1.5, Ti=3.0, Td=0.0),  # Different values
        lambda_parameter=1.0
    )
    case_response_2 = CaseResponse(output=sample_response_2)
    ctx_2 = MockEvaluatorContext(output=case_response_2)
    
    try:
        result_2 = evaluator.evaluate(ctx_2)
        print(f"✓ Evaluation result: {result_2.value}")
        print(f"  Reason: {result_2.reason}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test case 3: Wrong output type
    print("\n--- Test 3: Wrong output type ---")
    ctx_3 = MockEvaluatorContext(output=CaseResponse(output="not a LambdaTuningResponse"))
    
    try:
        result_3 = evaluator.evaluate(ctx_3)
        print(f"✓ Evaluation result: {result_3.value}")
        print(f"  Reason: {result_3.reason}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_lambda_tuning_evaluator()

