from control_agent.evals.common import * # type: ignore
from control_agent.experiment_definitions.response_schema import TuningOvershootResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = TuningOvershootResponse

dataset = Dataset[str, TuningOvershootResponse, Any](
    name='tuning_overshoot',
    cases=[
        Case(
            name='tuning_overshoot',
            inputs="Tune the PI controller to have approximately 10 percentage overshoot and rise time less than 2 seconds.",
            expected_output=None,
            evaluators=(
                EqualsExpected(),
                RequiredToolUseEvaluator(
                    required_tools=[
                        ToolUseSpec(name="simulate_step_response", max_runs=10),
                        ToolUseSpec(name="find_overshoot", max_runs=1),
                        ToolUseSpec(name="find_rise_time", max_runs=1)
                    ],
                    optional_tools=[
                        ToolUseSpec(name="get_fmu_names", max_runs=1),
                        ToolUseSpec(name="get_model_description", max_runs=1)
                    ]
                ),
            ),
        ),
    ],
)

