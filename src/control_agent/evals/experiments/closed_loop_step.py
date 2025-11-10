from control_agent.evals.common import * # type: ignore
from control_agent.experiment_definitions.response_schema import StepResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = StepResponse

dataset = Dataset[str, StepResponse, Any](
    name='closed_loop_step',
    cases=[
        Case(
            name='closed_loop_step',
            inputs="Simulate a closed-loop step response with input change from 0 to 1. Use output_interval 0.5 second and maximum simulation time 30 seconds.",
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
                StepResponseEvaluator()
            ),
        ),
    ],
)

