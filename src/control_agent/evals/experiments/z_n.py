from control_agent.evals.common import * # type: ignore
from control_agent.experiment_definitions.response_schema import ZNResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = ZNResponse

dataset = Dataset[str, ZNResponse, Any](
    name='z_n',
    cases=[
        Case(
            name='z_n',
            inputs="Tune the PI controller using Ziegler-Nichols closed-loop method.",
            expected_output=None,
            evaluators=(
                EqualsExpected(),
                RequiredToolUseEvaluator(
                    agent_name="FMIAgent",
                    required_tools=[
                        ToolUseSpec(name="simulate_step_response", max_runs=10),
                        ToolUseSpec(name="find_peaks", max_runs=1),
                        ToolUseSpec(name="zn_pid_tuning", max_runs=1)
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

