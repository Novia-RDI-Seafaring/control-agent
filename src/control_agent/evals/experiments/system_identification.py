from control_agent.evals.common import * # type: ignore
from control_agent.experiment_definitions.response_schema import SystemIdentificationResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = SystemIdentificationResponse

dataset = Dataset[str, SystemIdentificationResponse, Any](
    name='system_identification',
    cases=[
        Case(
            name='system_identification',
            inputs="Simulate an open-loop step response and identify the static gain (K), time constant (T), and dead time (L). Use output_interval 1 second and maximum simulation time 30 seconds.",
            expected_output=None,
            evaluators=(
                EqualsExpected(),
                RequiredToolUseEvaluator(
                    required_tools=[
                        ToolUseSpec(name="simulate_step_response", max_runs=1),
                        ToolUseSpec(name="identify_fopdt_from_step", max_runs=1)
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

