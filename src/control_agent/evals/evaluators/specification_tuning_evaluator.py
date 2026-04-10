from dataclasses import dataclass
from control_agent.experiment_definitions.response_schema import CaseResponse
from control_agent.experiment_definitions.response_schema import SpecificaitonTuningResponse
from control_toolbox.tools.simulation import SimulationStepResponseProps
from control_toolbox.tools.signals import StepProps, TimeRange
from control_toolbox.tools.simulation import simulate_step_response
from control_toolbox.tools.analysis import find_rise_time, find_overshoot
from pathlib import Path
from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from logging import getLogger
import numpy as np

logger = getLogger(__name__)

@dataclass
class SpecificationTuningEvaluator(Evaluator[object, CaseResponse[SpecificaitonTuningResponse], object]):
    """Evaluate specification tuning results against ground truth"""
    tolerance: float = 0.10  # 10% tolerance
    gt_rise_time: float = 2.0
    gt_overshoot: float = 0.1 # percent
    
    def evaluate(self, ctx: EvaluatorContext[object, SpecificaitonTuningResponse, object]) -> EvaluationReason:
        """Compare specification tuning results with ground truth"""
        # Calculate ground truth using the same library
        output = ctx.output
        if hasattr(output, 'output'):
            output = output.output
        if hasattr(output, 'output'):
            output = output.output

        if not isinstance(output, SpecificaitonTuningResponse):
            return EvaluationReason(
                value=False,
                reason=f"Output is not of type SpecificaitonTuningResponse. Got {type(output).__name__!r}."
            )

        Kp = output.controller_parameters.Kp
        Ti = output.controller_parameters.Ti

        simulation_props = SimulationStepResponseProps(
            start_time=0.0,
            stop_time=10.0,
            output_interval=0.1,
            start_values={
                "Kp": Kp,
                "Ti": Ti,
                "mode": True,
            }
        )
        step_props = StepProps(
            signal_name="input",
            time_range=TimeRange(start=0.0, stop=10.0, sampling_time=0.1),
            initial_value=0.0,
            final_value=1.0
        )

        # Simulate step response with the controller parameters
        step_response = simulate_step_response(
            fmu_path=Path("models/fmus/PI_FOPDT_2.fmu"),
            sim_props=simulation_props,
            step_props=step_props
        )

        # Find rise time and overshoot from the simulated response
        results_rise_time = find_rise_time(step_response)
        results_overshoot = find_overshoot(step_response)

        # Extract values for signal "y"
        actual_rise_time = None
        actual_overshoot = None
        
        for attribute in results_rise_time.attributes:
            if attribute.signal_name == "y":
                actual_rise_time = attribute.rise_time
                break
        
        for attribute in results_overshoot.attributes:
            if attribute.signal_name == "y":
                actual_overshoot = attribute.percent
                break
        
        if actual_rise_time is None or actual_overshoot is None:
            return EvaluationReason(
                value=False,
                reason=f"Could not find rise time or overshoot for signal 'y' in the step response."
            )

        # Check if the performance specifications are satisfied
        rise_time_ok = actual_rise_time <= self.gt_rise_time
        overshoot_ok = actual_overshoot <= self.gt_overshoot * 100.0

        if rise_time_ok and overshoot_ok:
            return EvaluationReason(
                value=True,
                reason=f"Both rise time and overshoot meet the requirements: "
                       f"rise time ≤ {self.gt_rise_time:.3f}s (actual: {actual_rise_time:.3f}s), "
                       f"overshoot ≤ {self.gt_overshoot*100:.1f}% (actual: {actual_overshoot:.1f}%)"
            )
        else:
            return EvaluationReason(
                value=False,
                reason=f"Failed specification: "
                       f"rise time ≤ {self.gt_rise_time:.3f}s (actual: {actual_rise_time:.3f}s), "
                       f"overshoot ≤ {self.gt_overshoot*100:.1f}% (actual: {actual_overshoot:.1f}%)"
            )