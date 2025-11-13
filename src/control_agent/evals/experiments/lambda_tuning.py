from control_agent.evals.common import * # type: ignore
from control_agent.experiment_definitions.response_schema import LambdaTuningResponse, CaseResponse

OutputDataT = CaseResponse[LambdaTuningResponse]

dataset = Dataset[str, CaseResponse[LambdaTuningResponse], Any](
    name='lambda_tuning',
    cases=[
        Case(
            name='lambda_tuning',
            inputs="Simulate a step response. Identify a FOPDT model from the step response 'y'. Tune the PI controller using λ-tuning for a balanced response.",
            expected_output=None,
            evaluators=(
                RequiredToolUseEvaluator(
                    required_tools=[
                        # Allow up to 2 calls to account for guardrail failures/retries
                        ToolUseSpec(name="simulate_step_response", max_runs=2),
                        ToolUseSpec(name="identify_fopdt_from_step", max_runs=1),
                        ToolUseSpec(name="lambda_tuning", max_runs=1)
                    ],
                    optional_tools=[
                        ToolUseSpec(name="get_fmu_names", max_runs=1),
                        ToolUseSpec(name="get_model_description", max_runs=1)
                    ]
                ),
                ToolSequenceEvaluator(
                    tool_call_sequence=["simulate_step_response", "identify_fopdt_from_step", "lambda_tuning"]
                ),
                LambdaTuningEvaluator(tolerance=0.05)
            ),
        ),
    ],
)

