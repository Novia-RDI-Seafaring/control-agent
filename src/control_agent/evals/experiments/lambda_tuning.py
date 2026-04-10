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
                        ToolUseSpec(name="simulate_step_response", max_runs=3),
                        ToolUseSpec(name="identify_fopdt_from_step", max_runs=3),
                        ToolUseSpec(name="lambda_tuning", max_runs=3)
                    ],
                    optional_tools=[
                        ToolUseSpec(name="get_fmu_names", max_runs=3),
                        ToolUseSpec(name="get_model_description", max_runs=3)
                    ]
                ),
                # ToolSequenceEvaluator(
                #    tool_call_sequence=["simulate_step_response", "identify_fopdt_from_step", "lambda_tuning"]
                #),
                LambdaTuningEvaluator(
                    tolerance=0.10,
                    gt_Kp=1.0,
                    gt_Ti=2.0,
                    gt_Td=0.0,
                    gt_response="balanced"
                    )
            ),
        ),
    ],
)

