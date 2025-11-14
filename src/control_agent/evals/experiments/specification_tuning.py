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
        f"""Perform simulated experiments to determine PI-controller parameters Kp and Ti such that 
        the closed-loop system has a rise time less than 2.0 seconds and a maximum overshoot less than 0.1 (10%).
        Start with Kp = 1.7 and Ti = 3.0, and incrementally adjust Kp until the rise time and overshoot specifications are met. 
        Return the parameters that satisfy the specifications."""
        )

dataset = Dataset[str, CaseResponse[StepResponse], Any](
    name='specification_tuning',
    cases=[
        Case(
            name='specification_tuning',
            inputs= QUERY.strip(),
            expected_output=None,
            evaluators=(
                RequiredToolUseEvaluator(
                    required_tools=[
                        ToolUseSpec(name="simulate_step_response", max_runs=10),
                        ToolUseSpec(name="find_rise_time", max_runs=10),
                        ToolUseSpec(name="find_overshoot", max_runs=10),
                    ],
                    optional_tools=[
                        ToolUseSpec(name="get_fmu_names", max_runs=3),
                        ToolUseSpec(name="get_model_description", max_runs=3)
                    ]
                ),
            ),
        ),
    ],
)

