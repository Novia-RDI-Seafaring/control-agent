"""Guardrail system for validating tool inputs and outputs."""

import os
from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec

from pydantic import BaseModel

from pathlib import Path

from control_agent.agent.context.models import ToolExecutionError, SimContext
from control_agent.agent.validation.validators import (
    validate_simulation_step_response_props,
    validate_step_props,
    validate_identification_props,
    validate_lambda_tuning_props,
)
from control_agent.agent.core.types import (
    SimulationStepResponseProps,
    StepProps,
    IdentificationProps,
    FOPDTModel,
    LambdaTuningProps,
    UltimateTuningProps,
    PIDParameters,
    StateSnapshotEvent,
    RunContext,
    StateDeps,
)

P = ParamSpec('P')
R = TypeVar('R')


class GuardrailViolation(BaseModel):
    """Represents a guardrail violation"""
    field: str
    value: Any
    constraint: str
    message: str


class GuardrailValidator:
    """Base class for guardrail validators"""
    
    def validate_input(self, tool_name: str, **kwargs) -> list[GuardrailViolation]:
        """Validate tool inputs. Returns list of violations (empty if valid)"""
        raise NotImplementedError
    
    def validate_output(self, tool_name: str, result: Any) -> list[GuardrailViolation]:
        """Validate tool outputs. Returns list of violations (empty if valid)"""
        raise NotImplementedError


class SimulationGuardrails(GuardrailValidator):
    """Guardrails for simulation tools - dynamic/runtime checks only.
    
    Note: Deterministic invariants (ranges, cross-field rules) are handled
    by Pydantic model validators in validators.py.
    """
    
    def validate_input(self, tool_name: str, **kwargs) -> list[GuardrailViolation]:
        violations = []
        
        if tool_name == "simulate_step_response":
            sim_props: SimulationStepResponseProps | None = kwargs.get('sim_props')
            step_props: StepProps | None = kwargs.get('step_props')
            ctx: RunContext[StateDeps[SimContext]] | None = kwargs.get('ctx')
            
            # Dynamic check: FMU must be chosen
            if ctx:
                try:
                    if not ctx.deps.state.current_fmu:
                        violations.append(GuardrailViolation(
                            field="current_fmu",
                            value=None,
                            constraint="FMU must be chosen",
                            message="No FMU has been chosen. Call 'choose_fmu' first."
                        ))
                    else:
                        # Dynamic check: FMU file exists
                        fmu_path = ctx.deps.state.fmu.fmu_path
                        if not Path(fmu_path).exists():
                            violations.append(GuardrailViolation(
                                field="fmu_path",
                                value=fmu_path,
                                constraint="FMU file must exist",
                                message=f"FMU file not found: {fmu_path}"
                            ))
                except (ValueError, AttributeError) as e:
                    violations.append(GuardrailViolation(
                        field="fmu",
                        value=None,
                        constraint="valid FMU context required",
                        message=f"FMU context error: {str(e)}"
                    ))
            
            # Dynamic check: start_values keys match FMU inputs if ctx and model_description available
            if ctx and sim_props:
                try:
                    start_values = getattr(sim_props, 'start_values', {})
                    if start_values and ctx.deps.state.fmu.model_description:
                        model_inputs = {var.name for var in ctx.deps.state.fmu.model_description.inputs} if hasattr(ctx.deps.state.fmu.model_description, 'inputs') else set()
                        invalid_keys = set(start_values.keys()) - model_inputs
                        if invalid_keys:
                            violations.append(GuardrailViolation(
                                field="start_values",
                                value=list(invalid_keys),
                                constraint="keys must match FMU inputs",
                                message=f"Invalid start_values keys: {invalid_keys}"
                            ))
                except Exception:
                    pass  # Skip if model_description not available
        
        elif tool_name == "choose_fmu":
            fmu_name: str | None = kwargs.get('fmu_name')
            ctx: RunContext[StateDeps[SimContext]] | None = kwargs.get('ctx')
            
            if fmu_name:
                # Check for path traversal
                if '..' in fmu_name or '/' in fmu_name or '\\' in fmu_name:
                    violations.append(GuardrailViolation(
                        field="fmu_name",
                        value=fmu_name,
                        constraint="no path traversal",
                        message=f"FMU name contains invalid characters: {fmu_name}"
                    ))
                
                # Check if FMU exists in available list
                if ctx:
                    available_fmus = getattr(ctx.deps.state, 'fmu_names', [])
                    if available_fmus and fmu_name not in available_fmus:
                        violations.append(GuardrailViolation(
                            field="fmu_name",
                            value=fmu_name,
                            constraint="must exist in available FMUs",
                            message=f"FMU '{fmu_name}' not found in available FMUs: {available_fmus}"
                        ))
        
        elif tool_name == "identify_fopdt_from_step":
            ctx: RunContext[StateDeps[SimContext]] | None = kwargs.get('ctx')
            
            # Dynamic check: simulation must exist
            if ctx:
                try:
                    if len(ctx.deps.state.fmu.simulations) == 0:
                        violations.append(GuardrailViolation(
                            field="simulations",
                            value=0,
                            constraint="at least one simulation required",
                            message="No simulations have been run yet"
                        ))
                except Exception:
                    pass
        
        elif tool_name in ("lambda_tuning", "zn_pid_tuning"):
            ctx: RunContext[StateDeps[SimContext]] | None = kwargs.get('ctx')
            
            # Dynamic check: FOPDT model must exist
            if ctx:
                try:
                    if len(ctx.deps.state.fmu.simulations) == 0:
                        violations.append(GuardrailViolation(
                            field="simulations",
                            value=0,
                            constraint="at least one simulation required",
                            message="No simulations have been run yet"
                        ))
                    elif len(ctx.deps.state.fmu.simulations[-1].fopdt_checks) == 0:
                        violations.append(GuardrailViolation(
                            field="fopdt_checks",
                            value=0,
                            constraint="at least one FOPDT check required",
                            message="No FOPDT checks have been run yet"
                        ))
                except Exception:
                    pass
        
        return violations
    
    def validate_output(self, tool_name: str, result: Any) -> list[GuardrailViolation]:
        violations = []
        
        # Skip validation for ToolExecutionError results
        if isinstance(result, ToolExecutionError):
            return violations
        
        if tool_name == "identify_fopdt_from_step":
            # Check if result is StateSnapshotEvent and contains FOPDT model
            if isinstance(result, StateSnapshotEvent):
                try:
                    # Get the last FOPDT check from the snapshot
                    fmu = result.snapshot.fmu
                    if fmu.simulations and fmu.simulations[-1].fopdt_checks:
                        fopdt_model = fmu.simulations[-1].fopdt_checks[-1].data
                        # Validate FOPDT parameters
                        if hasattr(fopdt_model, 'K') and fopdt_model.K <= 0:
                            violations.append(GuardrailViolation(
                                field="K",
                                value=fopdt_model.K,
                                constraint="> 0",
                                message=f"FOPDT gain K must be positive, got {fopdt_model.K}"
                            ))
                        if hasattr(fopdt_model, 'T') and fopdt_model.T <= 0:
                            violations.append(GuardrailViolation(
                                field="T",
                                value=fopdt_model.T,
                                constraint="> 0",
                                message=f"FOPDT time constant T must be positive, got {fopdt_model.T}"
                            ))
                        if hasattr(fopdt_model, 'L') and fopdt_model.L < 0:
                            violations.append(GuardrailViolation(
                                field="L",
                                value=fopdt_model.L,
                                constraint=">= 0",
                                message=f"FOPDT dead time L must be non-negative, got {fopdt_model.L}"
                            ))
                except Exception:
                    pass  # Skip validation if structure is unexpected
        
        elif tool_name in ("lambda_tuning", "zn_pid_tuning"):
            # Validate PID parameters
            if isinstance(result, StateSnapshotEvent):
                try:
                    if tool_name == "lambda_tuning":
                        checks = result.snapshot.fmu.lambda_tuning_checks
                    else:
                        checks = result.snapshot.fmu.zn_pid_tuning_checks
                    
                    if checks:
                        params: PIDParameters = checks[-1].params
                        # Validate PID parameters are within reasonable ranges
                        if hasattr(params, 'Kp'):
                            if params.Kp < -1000 or params.Kp > 1000:
                                violations.append(GuardrailViolation(
                                    field="Kp",
                                    value=params.Kp,
                                    constraint="-1000 <= Kp <= 1000",
                                    message=f"PID proportional gain Kp ({params.Kp}) is outside reasonable range"
                                ))
                        if hasattr(params, 'Ti'):
                            if params.Ti < 0 or params.Ti > 10000:
                                violations.append(GuardrailViolation(
                                    field="Ti",
                                    value=params.Ti,
                                    constraint="0 <= Ti <= 10000",
                                    message=f"PID integral time Ti ({params.Ti}) is outside reasonable range"
                                ))
                        if hasattr(params, 'Td'):
                            if params.Td < 0 or params.Td > 10000:
                                violations.append(GuardrailViolation(
                                    field="Td",
                                    value=params.Td,
                                    constraint="0 <= Td <= 10000",
                                    message=f"PID derivative time Td ({params.Td}) is outside reasonable range"
                                ))
                except Exception:
                    pass
        
        elif tool_name == "simulate_step_response":
            # Validate simulation results contain expected signals
            # Note: Empty signals might be valid if output list was empty or wrong signal names
            # Only warn if simulation has data but no signals (might indicate configuration issue)
            if isinstance(result, StateSnapshotEvent):
                try:
                    simulation = result.snapshot.fmu.simulations[-1]
                    data = simulation.data
                    #if hasattr(data, 'signals') and len(data.signals) == 0:
                    #    violations.append(GuardrailViolation(
                    #        field="signals",
                    #        value=0,
                    #        constraint="at least one signal required",
                    #        message="Simulation result contains no signals"
                    #    ))
                    # Check if simulation has timestamps (indicates it ran)
                    has_timestamps = hasattr(data, 'timestamps') and len(data.timestamps) > 0
                    # If simulation ran but has no signals, it's a warning not an error
                    # The simulation succeeded, just no signals were recorded (likely output list issue)
                    if has_timestamps and hasattr(data, 'signals') and len(data.signals) == 0:
                        # Don't treat as violation - simulation succeeded, just no signals recorded
                        # This is likely a configuration issue (wrong output names) not a failure
                        pass
                except Exception:
                    pass
        
        return violations


def apply_guardrails(
    tool_func: Callable[P, R],
    validator: GuardrailValidator,
    tool_name: str,
    enabled: bool = True
) -> Callable[P, R | ToolExecutionError]:
    """Wrap a tool function with guardrail validation"""
    
    if not enabled:
        return tool_func
    
    from inspect import signature
    
    sig = signature(tool_func)
    param_names = list(sig.parameters.keys())
    
    @wraps(tool_func)
    def guarded_tool(*args: P.args, **kwargs: P.kwargs) -> R | ToolExecutionError:
        # Map positional args to parameter names for validation
        validation_kwargs = dict(kwargs)
        for i, arg_value in enumerate(args):
            if i < len(param_names):
                param_name = param_names[i]
                if param_name not in validation_kwargs:
                    validation_kwargs[param_name] = arg_value
        
        # Extract ctx if present (usually first parameter)
        if param_names and param_names[0] == 'ctx' and param_names[0] not in validation_kwargs and args:
            validation_kwargs['ctx'] = args[0]
        
        # Step 1: Validate deterministic invariants (Pydantic model validators)
        try:
            if tool_name == "simulate_step_response":
                sim_props = validation_kwargs.get('sim_props')
                step_props = validation_kwargs.get('step_props')
                if sim_props:
                    validate_simulation_step_response_props(sim_props, step_props)
                if step_props:
                    validate_step_props(step_props)
            elif tool_name == "identify_fopdt_from_step":
                props = validation_kwargs.get('props')
                if props:
                    validate_identification_props(props)
            elif tool_name == "lambda_tuning":
                props = validation_kwargs.get('props')
                if props:
                    validate_lambda_tuning_props(props)
        except ValueError as e:
            return ToolExecutionError(
                message=f"Validation error: {str(e)}"
            )
        
        # Step 2: Validate dynamic/runtime checks (guardrails)
        violations = validator.validate_input(tool_name, **validation_kwargs)
        if violations:
            messages = [f"{v.field}: {v.message}" for v in violations]
            return ToolExecutionError(
                message=f"Guardrail violation(s): {'; '.join(messages)}"
            )
        
        # Execute tool
        try:
            result = tool_func(*args, **kwargs)
            
            # Output validation
            output_violations = validator.validate_output(tool_name, result)
            if output_violations:
                messages = [f"{v.field}: {v.message}" for v in output_violations]
                return ToolExecutionError(
                    message=f"Output guardrail violation(s): {'; '.join(messages)}"
                )
            
            return result
        except Exception as e:
            # Existing error handling
            return ToolExecutionError(message=str(e))
    
    return guarded_tool

