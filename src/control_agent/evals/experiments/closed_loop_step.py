from control_agent.evals.common import * 
from control_agent.experiment_definitions.response_schema import StepResponse, CaseResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = CaseResponse[StepResponse]

GT_KP = 1.0
GT_TI = 2.0
GT_MODE = True
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
        f"""Simulate an closed-loop step response with input change from {GT_START_VALUE}
        to {GT_FINAL_VALUE}. Set controller mode to {mode_map[GT_MODE]}, parameters Kp={GT_KP} 
        and Ti={GT_TI}. Use output sampling time 'output_interval' {GT_OUTPUT_INTERVAL} second 
        and simulate on the time range from {GT_START_TIME} to {GT_STOP_TIME} seconds."""
        )

dataset = Dataset[str, CaseResponse[StepResponse], Any](
    name='closed_loop_step',
    cases=[
        Case(
            name='closed_loop_step',
            inputs= QUERY.strip(),
            expected_output=None,
            evaluators=(
                RequiredToolUseEvaluator(
                    required_tools=[
                        ToolUseSpec(name="simulate_step_response", max_runs=1)
                    ],
                    optional_tools=[
                        ToolUseSpec(name="get_fmu_names", max_runs=1),
                        ToolUseSpec(name="get_model_description", max_runs=1)
                    ]
                ),
                StepResponseEvaluator(
                    rmse_tolerance=RMSE_TOLERANCE,
                    gt_Kp=GT_KP,
                    gt_Ti=GT_TI,
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

