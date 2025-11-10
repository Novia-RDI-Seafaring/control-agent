from control_agent.evals.common import * # type: ignore
from control_agent.experiment_definitions.response_schema import ListModelNamesResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = ListModelNamesResponse

dataset = Dataset[str, ListModelNamesResponse, Any](
    name='list_model_names',
    cases=[
        Case(
            name='get_fmu_names',
            inputs="Please list all the FMU models in the system",
            expected_output=ListModelNamesResponse(model_names=["PI_FOPDT_2"]),
            evaluators=(
                EqualsExpected(),
                RequiredToolUseEvaluator(
                    required_tools=[
                        ToolUseSpec(name="get_fmu_names", max_runs=1)
                    ],
                    optional_tools=[]
                ),
            ),
        ),
    ],
)