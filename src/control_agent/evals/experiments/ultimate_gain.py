from control_agent.evals.common import * # type: ignore
from control_agent.evals.response_schema import UltimateGainResponse, CaseResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = CaseResponse[UltimateGainResponse]

dataset = Dataset[str, CaseResponse[UltimateGainResponse], Any](
    name='ultimate_gain',
    cases=[
        Case(
            name='ultimate_gain',
            inputs="Perform closed-loop experimentes to determine the ultimate gain (Ku) and ultimate period (Pu). Use output_interval 0.1 second and maximum simulation time 10 seconds.",
            expected_output=None,
            evaluators=(
                EqualsExpected(),
                RequiredToolUseEvaluator(
                    required_tools=[
                        ToolUseSpec(name="simulate_step_response", max_runs=10),
                        ToolUseSpec(name="find_peaks", max_runs=1)
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

