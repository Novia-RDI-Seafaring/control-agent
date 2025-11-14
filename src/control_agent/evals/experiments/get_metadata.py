from control_agent.evals.common import * # type: ignore
from control_agent.evals.schemas.responses import GetMetadataResponse, CaseResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = CaseResponse[GetMetadataResponse]

dataset = Dataset[str, CaseResponse[GetMetadataResponse], Any](
    name='get_metadata',
    cases=[
        Case(
            name='get_metadata',
            inputs="Get the metadata of the model.",
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

