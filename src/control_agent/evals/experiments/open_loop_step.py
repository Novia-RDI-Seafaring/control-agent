from control_agent.evals.common import * # type: ignore
from control_agent.experiment_definitions.response_schema import StepResponse, CaseResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec
from control_agent.evals.evaluators.step_response_evaluator import StepResponseEvaluator

OutputDataT = CaseResponse[StepResponse]

dataset = Dataset[str, CaseResponse[StepResponse], Any](
    name='open_loop_step',
    cases=[
        Case(
            name='open_loop_step',
            inputs="Simulate an open-loop step response with input change from 0 to 1. Set controller mode to 'manual' and parameters Kp=1.0 and Ti=2.0. Use output_interval 0.1 second and maximum simulation time 20 seconds.",
            expected_output=None,
            evaluators=(
                EqualsExpected(),
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
                    rmse_tolerance=0.1,
                    gt_Kp=1.0,
                    gt_Ti=2.0,
                    gt_mode=False,
                    gt_output_interval=0.1,
                    gt_start_time=0.0,
                    gt_stop_time=20.0,
                    gt_start_value=0.0,
                    gt_final_value=1.0
                )
            ),
        ),
    ],
)
