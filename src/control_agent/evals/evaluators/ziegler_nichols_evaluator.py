from dataclasses import dataclass

from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from control_agent import FOPDT
#from control_agent import ZieglerNicholsMethod
from logging import getLogger
from control_toolbox.tools.pid_tuning import zn_pid_tuning as _zn_pid_tuning
from control_toolbox.tools.pid_tuning import UltimateTuningProps
from control_agent.evals.schemas.responses import ZNResponse
from control_toolbox.tools.pid_tuning import UltimateTuningProps, UltimateGainParameters
from control_toolbox.tools.simulation import SimulationStepResponseProps, simulate_step_response
from control_toolbox.tools.simulation import StepProps 
from control_toolbox.tools.signals import TimeRange
from control_toolbox.tools.analysis import find_peaks, FindPeaksProps

logger = getLogger(__name__)


@dataclass
class ZieglerNicholsEvaluator(Evaluator[object, object, object]):
    """Evaluate Ziegler-Nichols tuning results against ground truth"""
    tolerance: float = 0.05  # 5% tolerance
    
    def evaluate(self, ctx: EvaluatorContext[object, ZNResponse, object]) -> EvaluationReason:
        """Compare Ziegler-Nichols tuning results with ground truth"""
        output: ZNResponse = ctx.output

        # ground truth ultimate gain
        gt_Kpu = 3.84

        # groudn truth step response
        step_props = StepProps(
            signal_name="input",
            time_range=TimeRange(start=0.0, stop=10.0, sampling_time=0.1),
            initial_value=0.0,
            final_value=1.0
        )
        simulation_props = SimulationStepResponseProps(
            fmu_name="PI_FOPDT_2",
            start_time=0.0,
            stop_time=20.0,
            output_interval=0.1,
            start_values={
                "mode": True,
                "Kp": gt_Kpu,
                "Ti": float("inf"),
            }
        )
        gt_step_response = simulate_step_response(sim_props=simulation_props, step_props=step_props)

        # ground truth peaks detection
        gt_peaks = find_peaks(data=gt_step_response, props=FindPeaksProps())

        # ground truth ultimate gain and period
        gt_Ku=gt_Kpu
        gt_Pu=gt_peaks.attributes[0].average_peak_period

        # ground truthh props for zn_pid_tuning
        gt_zn_props=UltimateTuningProps(
            params=UltimateTuningProps(
                Ku=gt_Ku,
                Pu=gt_Pu
            ),
            controller = "pi",
            method = "classic"
        )

        zn_method = _zn_pid_tuning(gt_zn_props)

        # gt PID parameters
        gt_Kp = zn_method.Kp
        gt_Ti = zn_method.Ti
        gt_Td = zn_method.Td

        # estiamted PID parameters
        Kp = output.Kp
        Ti = output.Ti
        Td = output.Td

        # Calculate relative errors for PID parameters
        kp_error = abs(Kp - gt_Kp) / gt_Kp if gt_Kp != 0 else abs(Kp - gt_Kp)
        ti_error = abs(Ti - gt_Ti) / gt_Ti if gt_Ti != 0 else abs(Ti - gt_Ti)
        td_error = abs(Td - gt_Td) / gt_Td if gt_Td != 0 else abs(Td - gt_Td)

        # Check if parameters are within tolerance
        if kp_error <= self.tolerance and ti_error <= self.tolerance and td_error <= self.tolerance:
            return EvaluationReason(
                value=True,
                reason=f"Controller parameters match ground truth (Kp={Kp:.3f}, Ti={Ti:.3f}, Td={Td:.3f})"  
            )
        else:
            return EvaluationReason(
                value=False,
                reason=f"Parameter errors exceed tolerance: Kp={kp_error:.2%}, Ti={ti_error:.2%}, Td={td_error:.2%} "
                       f"(expected Kp={gt_Kp:.3f}, Ti={gt_Ti:.3f}, Td={gt_Td:.3f})"
            )
        
        """    
        # Parse agent output
        output = ctx.output
        if isinstance(output, dict):
            # Try different possible structures
            controller = output.get('controller_parameters', {})
            if not controller:
                controller = output.get('pid_parameters', {})
            if not controller:
                controller = output  # Maybe output is the controller directly
            
            Kp = controller.get('Kp') or controller.get('K_p')
            Ti = controller.get('Ti') or controller.get('T_i')
        else:
            logger.error(f"Could not parse output: {type(output)}")
            return EvaluationReason(value=False, reason=f"Could not parse output: expected dict, got {type(output)}")
        
        if Kp is None or Ti is None:
            return EvaluationReason(value=False, reason="Missing controller parameters: Kp or Ti not found in output")
        
        # Calculate relative errors
        kp_error = abs(Kp - ground_truth_Kp) / ground_truth_Kp if ground_truth_Kp != 0 else abs(Kp - ground_truth_Kp)
        ti_error = abs(Ti - ground_truth_Ti) / ground_truth_Ti if ground_truth_Ti != 0 else abs(Ti - ground_truth_Ti)
        
        # Check if parameters are within tolerance
        if kp_error <= self.tolerance and ti_error <= self.tolerance:
            return EvaluationReason(
                value=True,
                reason=f"Controller parameters match ground truth (Kp={Kp:.3f}, Ti={Ti:.3f})"
            )
        else:
            return EvaluationReason(
                value=False,
                reason=f"Parameter errors exceed tolerance: Kp={kp_error:.2%}, Ti={ti_error:.2%} "
                       f"(expected Kp={ground_truth_Kp:.3f}, Ti={ground_truth_Ti:.3f})"
            )
        """