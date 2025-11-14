from control_agent.evals.common import * # type: ignore
from control_agent.evals.schemas.responses import TuningOvershootResponse, CaseResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = CaseResponse[TuningOvershootResponse]

dataset = Dataset[str, CaseResponse[TuningOvershootResponse], Any](
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
                        ToolUseSpec(name="find_overshoot", max_runs=10),
                        ToolUseSpec(name="find_rise_time", max_runs=10)
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

