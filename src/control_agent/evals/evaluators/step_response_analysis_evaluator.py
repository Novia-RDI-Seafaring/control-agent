from dataclasses import dataclass
# from typing import Dict, Any  # Not used
from control_agent.experiment_definitions.response_schema import CaseResponse
from control_agent.experiment_definitions.response_schema import StepResponse
from control_toolbox.tools.simulation import SimulationProps, simulate_step_response
from control_toolbox.tools.signals import StepProps, TimeRange
from control_toolbox.tools.analysis import find_rise_time, find_settling_time, find_overshoot
from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
# from control_agent import FOPDT  # Not used
# from logging import getLogger  # Not used
import numpy as np
from pathlib import Path

# logger = getLogger(__name__)  # Not used

def _relative_error(x: float, y: float) -> float:
    return abs(x - y) / y if y != 0 else abs(x - y)

@dataclass
class StepResponseAnalysisEvaluator(Evaluator[object, CaseResponse[StepResponse], object]):
    """Evaluate system identification results against ground truth FOPDT parameters"""
    rmse_tolerance: float = 0.1
    gt_Kp: float = 1.0
    gt_Ti: float = 2.0
    gt_mode: bool = False
    gt_output_interval: float = 0.1
    gt_start_time: float = 0.0
    gt_stop_time: float = 30.0
    gt_start_value: float = 0.0
    gt_final_value: float = 1.0
    
    def evaluate(self, ctx: EvaluatorContext[object, CaseResponse[StepResponse], object]) -> EvaluationReason:
        """Compare identified parameters with ground truth"""
        # Extract nested output: AgentRunResult -> CaseResponse -> StepResponse
        output = ctx.output
        if hasattr(output, 'output'):
            output = output.output
        if hasattr(output, 'output'):
            output = output.output

        rise_time = output.rise_time
        settling_time = output.settling_time
        overshoot = output.overshoot

        #########################################################
        # CALCUALTE GROUND TRUTH VALUES
        #########################################################
        
        # Find the "y" signal in the output
        y = None
        # Check both outputs and signals attributes
        signals_list = []
        if hasattr(output, 'outputs'):
            signals_list = output.outputs or []
        elif hasattr(output, 'signals'):
            signals_list = output.signals or []
        
        for signal in signals_list:
            if signal.name == "y":
                y = np.array(signal.values)
                break
        
        if y is None:
            available_signals = [s.name for s in signals_list] if signals_list else []
            return EvaluationReason(
                value=False,
                reason=f"Output signal 'y' not found. Available signals: {available_signals}"
                # reason=f"Output signal 'y' not found. Available signals: {available_signals}. Debug: {debug_info}"  # Debug version
            )

        # simulate to get ground truth
        gt_simulation_props = SimulationProps(
            start_time=self.gt_start_time,
            stop_time=self.gt_stop_time,
            output_interval=self.gt_output_interval,
            start_values={
                "Kp": self.gt_Kp,
                "Ti": self.gt_Ti,
                "mode": self.gt_mode,
            }
        )
        gt_step_props = StepProps(
            signal_name="input",
            time_range=TimeRange(start=self.gt_start_time, stop=self.gt_stop_time, sampling_time=self.gt_output_interval),
            initial_value=self.gt_start_value,
            final_value=self.gt_final_value
        )

        # ground truth step response. Note: this is a DataModel object!
        gt_step_response = simulate_step_response(
            fmu_path=Path("models/fmus/PI_FOPDT_2.fmu"),
            sim_props=gt_simulation_props,
            step_props=gt_step_props
        )

        # get tise time
        gt_rise_time = find_rise_time(gt_step_response)
        gt_settling_time = find_settling_time(gt_step_response)
        gt_overshoot = find_overshoot(gt_step_response)
      
        #########################################################
        # EVALUATION
        #########################################################
        rise_time_error = _relative_error(rise_time, gt_rise_time)
        settling_error = _relative_error(settling_time, gt_settling_time)
        overshoot_error = _relative_error(overshoot, gt_overshoot)
        
        # Check if all parameters are within tolerance
        if rise_time_error <= self.tolerance and settling_error <= self.tolerance and overshoot_error <= self.tolerance:
            return EvaluationReason(
                value=True,
                reason=(
                    f"System parameters match ground truth. "
                    "   - Rise time: {rise_time:.3f} (expected {gt_rise_time:.3f}), "
                    "   - Settling time: {settling_time:.3f} (expected {gt_settling_time:.3f}), "
                    "   - Overshoot: {overshoot:.3f} (expected {gt_overshoot:.3f}) "
                )
            )
        else:
            return EvaluationReason(
                value=False,
                reason=(
                    f"Parameter errors exceed tolerance. "
                    "   - Rise time: {rise_time_error:.2%}, "
                    "   - Settling time: {settling_error:.2%}, "
                    "   - Overshoot: {overshoot_error:.2%} "
                )
            )
