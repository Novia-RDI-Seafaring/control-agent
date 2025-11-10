from control_agent.evals.common import * # type: ignore
from control_agent.experiment_definitions.response_schema import ListIOPResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = ListIOPResponse

dataset = Dataset[str, ListIOPResponse, Any](
    name='list_iop',
    cases=[
        Case(
            name='list_iop',
            inputs="List the inputs, outputs, and parameters of the model.",
            expected_output=None,
            evaluators=(
                EqualsExpected(),
                RequiredToolUseEvaluator(
                    required_tools=[
                        ToolUseSpec(name="get_model_description", max_runs=1)
                    ],
                    optional_tools=[
                        ToolUseSpec(name="get_fmu_names", max_runs=1)
                    ]
                ),
            ),
        ),
    ],
)

