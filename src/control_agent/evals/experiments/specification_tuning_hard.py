from control_agent.evals.common import * 
from control_agent.evals.response_schema import SpecificaitonTuningResponse, CaseResponse
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec
from control_agent.evals.evaluators.specification_tuning_evaluator import SpecificationTuningEvaluator
OutputDataT = CaseResponse[SpecificaitonTuningResponse]

GT_KP = 1.0
GT_TI = 2.0
GT_MODE = True
GT_OUTPUT_INTERVAL = 0.1
GT_START_TIME = 0.0
GT_STOP_TIME = 20.0
GT_START_VALUE = 0.0
GT_FINAL_VALUE = 1.0

RMSE_TOLERANCE = 0.05

GT_RISE_TIME = 2.0
GT_OVERSHOOT = 0.1 

mode_map = {
    True: "automatic",
    False: "manual",
}

QUERY = (
        f"""Perform simulated experiments to determine PI-controller parameters Kp and Ti such that 
        the closed-loop system has a rise time less than {GT_RISE_TIME} seconds and a maximum overshoot less than {GT_OVERSHOOT} (10%).
        """
        )

dataset = Dataset[str, CaseResponse[SpecificaitonTuningResponse], Any](
    name='specification_tuning_hard',
    cases=[
        Case(
            name='specification_tuning_hard',
            inputs= QUERY.strip(),
            expected_output=None,
            evaluators=[
                SpecificationTuningEvaluator(
                    gt_rise_time=GT_RISE_TIME,
                    gt_overshoot=GT_OVERSHOOT,
                )
            ],
        ),
    ],
)

