from control_agent.evals.common import * # type: ignore
from control_agent.experiment_definitions.response_schema import ZNResponse, CaseResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec

OutputDataT = CaseResponse[ZNResponse]

GT_KP = 1.0
GT_TI = 2.0
GT_MODE = True
GT_OUTPUT_INTERVAL = 0.1
GT_START_TIME = 0.0
GT_STOP_TIME = 20.0
GT_START_VALUE = 0.0
GT_FINAL_VALUE = 1.0

TOLERANCE = 0.05

mode_map = {
    True: "automatic",
    False: "manual",
}

QUERY = (
        f"""Perform multiple repeated step-response simulation experiments to tune a PI controller using the Ziegler-Nichols method.
        Get useful instructions from available resources to better understand the tuning procedure.
        
        Experiment procedure:
        0. Set controller to 'automatic' mode and set Ti = float("inf").
        1. run simulate_step_response Kp = 1.0
        2. run oscillation_analysis
        3. If iscillations are decreasing, icrease Kp += 0.4, if oscillations are increasing, decrease Kp -= 0.1
        4. run oscillation_analysis
        REPEAT until sustained oscillations are obtained.
        X. When sustained iscillations are obtained, run zn_pid_tuning tool with the ultimate gain Ku and period Pu.
        Return Kp, Ti, Td
        
         -The ultimate gain Ku=Kp when sustained oscillations are obtained.
         -The ultimate period Pu is the average period time between peaks when sustained oscillations are obtained.

        """
        )

dataset = Dataset[str, CaseResponse[ZNResponse], Any](
    name='z_n',
    cases=[
        Case(
            name='z_n',
            inputs=QUERY,
            expected_output=None,
            evaluators=(
                RequiredToolUseEvaluator(
                    required_tools=[
                        ToolUseSpec(name="simulate_step_response", max_runs=10),
                        ToolUseSpec(name="oscillation_analysis", max_runs=10),
                        ToolUseSpec(name="zn_pid_tuning", max_runs=1)
                    ],
                    optional_tools=[
                        ToolUseSpec(name="get_fmu_names", max_runs=1),
                        ToolUseSpec(name="find_peaks", max_runs=10),
                        ToolUseSpec(name="get_model_description", max_runs=1)
                    ]
                ),
                ZieglerNicholsEvaluator(tolerance=TOLERANCE),
            ),
        ),
    ],
)

