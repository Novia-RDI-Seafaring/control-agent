from control_agent.evals.common import * # type: ignore
from control_agent.experiment_definitions.response_schema import StepResponseAnalysisResponse, CaseResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec
from control_agent.evals.evaluators.step_response_analysis_evaluator import StepResponseAnalysisEvaluator

OutputDataT = CaseResponse[StepResponseAnalysisResponse]

GT_KP = 3.0
GT_TI = float("inf")
GT_MODE = True
GT_OUTPUT_INTERVAL = 0.1
GT_START_TIME = 0.0
GT_STOP_TIME = 20.0
GT_START_VALUE = 0.0
GT_FINAL_VALUE = 1.0

TOLERANCE = 0.05

mode_map = {
    True: "automatic",
    False: "manual",
}

QUERY = (
        f"""Simulate an closed-loop step response with input change from {GT_START_VALUE}
        to {GT_FINAL_VALUE}. Set controller mode to {mode_map[GT_MODE]}, parameters Kp={GT_KP} 
        and Ti={GT_TI}. Use output sampling time 'output_interval' {GT_OUTPUT_INTERVAL} second 
        and simulate on the time range from {GT_START_TIME} to {GT_STOP_TIME} seconds.
        Return the *rise time*, *settling time*, and *maximum overshoot* of the output 'y'."""
        )

dataset = Dataset[str, CaseResponse[StepResponseAnalysisResponse], Any](
    name='step_response_analysis',
    cases=[
        Case(
            name='step_response_analysis',
            inputs = QUERY.strip()
            ,            
            expected_output=None,
            evaluators=(
                RequiredToolUseEvaluator(
                    required_tools=[
                        ToolUseSpec(name="simulate_step_response", max_runs=3),
                        ToolUseSpec(name="find_rise_time", max_runs=3),
                        ToolUseSpec(name="find_settling_time", max_runs=3),
                        ToolUseSpec(name="find_overshoot", max_runs=3),
                    ],
                    optional_tools=[
                        ToolUseSpec(name="get_fmu_names", max_runs=3),
                        ToolUseSpec(name="get_model_description", max_runs=3)
                    ]
                ),
                StepResponseAnalysisEvaluator(
                    tolerance=TOLERANCE,
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
