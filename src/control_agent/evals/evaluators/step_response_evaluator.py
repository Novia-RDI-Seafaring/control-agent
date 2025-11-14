from dataclasses import dataclass
# from typing import Dict, Any  # Not used
from control_agent.experiment_definitions.response_schema import CaseResponse
from control_agent.experiment_definitions.response_schema import StepResponse
from control_toolbox.tools.simulation import SimulationStepResponseProps, simulate_step_response
from control_toolbox.tools.signals import StepProps, TimeRange
from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
# from control_agent import FOPDT  # Not used
# from logging import getLogger  # Not used
import numpy as np
from pathlib import Path

from typing import List, Optional, Any
# logger = getLogger(__name__)  # Not used


@dataclass
class StepResponseEvaluator(Evaluator[object, CaseResponse[StepResponse], object]):
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
        
        # Now output should be StepResponse
        # # Debug: Check what we actually have
        # output_type = type(output).__name__
        # has_outputs = hasattr(output, 'outputs')
        # has_signals = hasattr(output, 'signals')
        
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
            # # Provide more detailed error message (debug code)
            # debug_info = f"Type: {output_type}, has_outputs: {has_outputs}, has_signals: {has_signals}"
            # if hasattr(output, 'outputs'):
            #     debug_info += f", outputs length: {len(output.outputs)}"
            # if hasattr(output, 'signals'):
            #     debug_info += f", signals length: {len(output.signals)}"
            return EvaluationReason(
                value=False,
                reason=f"Output signal 'y' not found. Available signals: {available_signals}"
                # reason=f"Output signal 'y' not found. Available signals: {available_signals}. Debug: {debug_info}"  # Debug version
            )

        # simulate to get ground truth
        gt_simulation_props = SimulationStepResponseProps(
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

        # Find the "y" signal in the ground truth response
        gt_y = None
        for signal in gt_step_response.signals:
            if signal.name == "y":
                gt_y = np.array(signal.values)
                break
        
        if gt_y is None:
            available_signals = [s.name for s in gt_step_response.signals]
            return EvaluationReason(
                value=False,
                reason=f"Ground truth signal 'y' not found. Available signals: {available_signals}"
            )

        # Ensure arrays have the same length for comparison
        # min_len = min(len(y), len(gt_y))  # Not used, can check directly

        if len(y) == 0 or len(gt_y) == 0:
            return EvaluationReason(
                value=False,
                reason=f"Cannot compare empty arrays. y length: {len(y)}, gt_y length: {len(gt_y)}"
            )

        if len(y) != len(gt_y):
            return EvaluationReason(
                value=False,
                reason=f"y and gt_y have different lengths. y length: {len(y)}, gt_y length: {len(gt_y)}"
            )
      
        # calculate RMSE
        e = y - gt_y
        y_rmse = np.sqrt(np.mean(e**2))

        # Check if signals are within tolerance
        if y_rmse <= self.rmse_tolerance:
            return EvaluationReason(
                value=True,
                reason=f"System response matches ground truth (RMSE={y_rmse:.3f})"
            )
        else:
            return EvaluationReason(
                value=False,
                reason=f"System response does not match ground truth (RMSE={y_rmse:.3f})"
            )
