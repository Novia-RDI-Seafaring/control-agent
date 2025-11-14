from control_agent.evals.common import * # type: ignore
from control_toolbox.tools.information import ModelDescription
from control_agent.evals.schemas.responses import CaseResponse
OutputDataT = ModelDescription

dataset = Dataset[str, CaseResponse[ModelDescription], Any](
    name='model_description',
    cases=[
        Case(
            name='model_description',
            inputs="Get the model description.",
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

