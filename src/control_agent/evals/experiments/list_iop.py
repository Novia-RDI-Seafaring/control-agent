from control_agent.evals.common import * # type: ignore
from control_agent.evals.schemas.responses import ListIOPResponse, CaseResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = CaseResponse[ListIOPResponse]

dataset = Dataset[str, CaseResponse[ListIOPResponse], Any](
    name='list_iop',
    cases=[
        Case(
            name='list_iop',
            inputs="List the inputs, outputs, and parameters of the model.",
            expected_output=None,
            evaluators=(
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

