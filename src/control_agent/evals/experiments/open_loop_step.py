from control_agent.evals.common import * # type: ignore
from control_agent.evals.schemas.responses import StepResponse, CaseResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec
from control_agent.evals.evaluators.step_response_evaluator import StepResponseEvaluator
import sys

# Debug: Print when module is imported
print("open_loop_step.py imported!", file=sys.stderr, flush=True)

OutputDataT = CaseResponse[StepResponse]
#dataset = Dataset[str, CaseResponse[StepResponse], Any](
#    name='open_loop_step',
#    cases=[
#        Case(
#            name='open_loop_step',
#            inputs="Simulate an open-loop step response with input change from 0 to 1. Set controller mode to 'manual' and parameters Kp=1.0 and Ti=2.0. Use output_interval 0.1 second and maximum simulation time 20 seconds.",
#            expected_output=None,
#            evaluators=(
#                EqualsExpected(),
#                RequiredToolUseEvaluator(
#                    required_tools=[
#                        ToolUseSpec(name="simulate_step_response", max_runs=1)
#                    ],
#                    optional_tools=[
#                        ToolUseSpec(name="get_fmu_names", max_runs=1),
#                        ToolUseSpec(name="get_model_description", max_runs=1)
#                    ]
#                ),
#                StepResponseEvaluator(
#                    rmse_tolerance=0.1,
#                    # gt_Kp=1.0,  # Original agent simulation
#                    gt_Kp=3.0,  # Wrong value - should be 1.0 to test failure
#                    gt_Ti=2.0,
#                    # gt_mode=False,
#                    gt_mode=True,  # Original agent simulation (manual/open-loop)
#                    gt_output_interval=0.1,
#                    gt_start_time=0.0,
#                    gt_stop_time=20.0,
#                    gt_start_value=0.0,
#                    gt_final_value=1.0
#                )
#            ),
# Create evaluators tuple
evaluators_tuple = (
    EqualsExpected(),
    RequiredToolUseEvaluator(
        required_tools=[
            ToolUseSpec(name="simulate_step_response", max_runs=3)  # Allow retries for guardrail failures
        ],
        optional_tools=[
            ToolUseSpec(name="get_fmu_names", max_runs=3),
            ToolUseSpec(name="get_model_description", max_runs=3)
        ]
    ),
    StepResponseEvaluator(
        rmse_tolerance=0.1,
        gt_Kp=3.0,
        gt_Ti=2.0,
        gt_mode=True,
        gt_output_interval=0.1,
        gt_start_time=0.0,
        gt_stop_time=20.0,
        gt_start_value=0.0,
        gt_final_value=1.0
    )
)

# Debug: Print evaluators before creating dataset
#print(f"[DEBUG] Evaluators tuple: {[type(e).__name__ for e in evaluators_tuple]}", file=sys.stderr, flush=True)
#print(f"[DEBUG] Evaluators count: {len(evaluators_tuple)}", file=sys.stderr, flush=True)

GT_MODE = False # False: open-loop, True: closed-loop
GT_OUTPUT_INTERVAL = 0.1
GT_START_TIME = 0.0
GT_STOP_TIME = 20.0
GT_START_VALUE = 0.0
GT_FINAL_VALUE = 1.0
RMSE_TOLERANCE = 0.05

mode_map = {
    True: "automatic",
    False: "manual",
}

QUERY = (
        f"""Simulate an closed-loop step response with input step change from {GT_START_VALUE}
        to {GT_FINAL_VALUE}. Set controller mode to {mode_map[GT_MODE]}. Use output sampling 
        time 'output_interval' {GT_OUTPUT_INTERVAL} second and simulate on the time range from 
        {GT_START_TIME} to {GT_STOP_TIME} seconds."""
        )

dataset = Dataset[str, CaseResponse[StepResponse], Any](
    name='open_loop_step',
    cases=[
        Case(
            name='open_loop_step',
            inputs = QUERY.strip()
            ,            
            expected_output=None,
            evaluators=(
                EqualsExpected(),
                RequiredToolUseEvaluator(
                    required_tools=[
                        ToolUseSpec(name="simulate_step_response", max_runs=2)
                    ],
                    optional_tools=[
                        ToolUseSpec(name="get_fmu_names", max_runs=1),
                        ToolUseSpec(name="get_model_description", max_runs=1)
                    ]
                ),
                StepResponseEvaluator(
                    rmse_tolerance=RMSE_TOLERANCE,
                    gt_mode=GT_MODE,
                    gt_output_interval=GT_OUTPUT_INTERVAL,
                    gt_start_time=GT_START_TIME,
                    gt_stop_time=GT_STOP_TIME,
                    gt_start_value=GT_START_VALUE,
                    gt_final_value=GT_FINAL_VALUE
                )
            ),
        ),
    ],
)

# Debug: Print evaluators after creating dataset
#print(f"[DEBUG] Dataset evaluators: {[type(e).__name__ for e in dataset.cases[0].evaluators]}", file=sys.stderr, flush=True)
#print(f"[DEBUG] Dataset evaluators count: {len(dataset.cases[0].evaluators)}", file=sys.stderr, flush=True)

