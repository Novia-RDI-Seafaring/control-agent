"""Pydantic model validators for deterministic invariants.

This module provides validation for external models from control_toolbox.
Since we can't modify those models directly, we validate them before use.
"""

from pathlib import Path
from typing import Any
import os

from pydantic import ValidationError, model_validator
from control_agent.agent.core.types import (
    SimulationStepResponseProps,
    StepProps,
    IdentificationProps,
    LambdaTuningProps,
)


def validate_simulation_step_response_props(
    sim_props: SimulationStepResponseProps,
    step_props: StepProps | None = None,
) -> None:
    """Validate SimulationStepResponseProps with deterministic invariants.
    
    Raises:
        ValueError: If validation fails
    """
    # Basic range checks
    if sim_props.stop_time <= sim_props.start_time:
        raise ValueError(
            f"stop_time ({sim_props.stop_time}) must be greater than "
            f"start_time ({sim_props.start_time})"
        )
    
    if sim_props.output_interval <= 0:
        raise ValueError(
            f"output_interval ({sim_props.output_interval}) must be positive"
        )
    
    # Cross-field validation with step_props
    if step_props is not None:
        if hasattr(step_props, 'time_range') and step_props.time_range:
            sampling_time = step_props.time_range.sampling_time
            if sim_props.output_interval < sampling_time:
                raise ValueError(
                    f"output_interval ({sim_props.output_interval}) must be >= "
                    f"sampling_time ({sampling_time})"
                )
            
            if sampling_time <= 0:
                raise ValueError(
                    f"sampling_time ({sampling_time}) must be positive"
                )
        
        # Step value validation
        if hasattr(step_props, 'initial_value') and hasattr(step_props, 'final_value'):
            if step_props.initial_value == step_props.final_value:
                raise ValueError(
                    "initial_value and final_value must be different for a step response"
                )


def validate_step_props(step_props: StepProps) -> None:
    """Validate StepProps with deterministic invariants.
    
    Raises:
        ValueError: If validation fails
    """
    if hasattr(step_props, 'time_range') and step_props.time_range:
        time_range = step_props.time_range
        
        if time_range.stop <= time_range.start:
            raise ValueError(
                f"time_range.stop ({time_range.stop}) must be greater than "
                f"time_range.start ({time_range.start})"
            )
        
        if time_range.sampling_time <= 0:
            raise ValueError(
                f"sampling_time ({time_range.sampling_time}) must be positive"
            )
        
        if hasattr(step_props, 'initial_value') and hasattr(step_props, 'final_value'):
            if step_props.initial_value == step_props.final_value:
                raise ValueError(
                    "initial_value and final_value must be different for a step response"
                )


def validate_identification_props(props: IdentificationProps) -> None:
    """Validate IdentificationProps with deterministic invariants.
    
    Raises:
        ValueError: If validation fails
    """
    if hasattr(props, 'input_step_size') and props.input_step_size is not None:
        if props.input_step_size <= 0:
            raise ValueError(
                f"input_step_size ({props.input_step_size}) must be positive"
            )


def validate_lambda_tuning_props(props: LambdaTuningProps) -> None:
    """Validate LambdaTuningProps with deterministic invariants.
    
    Raises:
        ValueError: If validation fails
    """
    lambda_val = getattr(props, 'lambda', None)
    if lambda_val is not None:
        if lambda_val <= 0:
            raise ValueError(f"lambda ({lambda_val}) must be positive")

