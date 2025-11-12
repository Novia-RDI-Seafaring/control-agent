from __future__ import annotations
import os
import uuid
from typing import List, Optional, Dict, Literal, Any, Type, TypeVar, Union, Any, Callable, Generic, Dict, Optional, Tuple, Type, TypeVar, Union, get_type_hints, get_origin, get_args, Optional, Union, TypeVar, Type, Literal, Dict, Any, List, get_origin, get_args, get_type_hints
from functools import wraps
from inspect import signature, Parameter, Signature
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from logging import getLogger
from pathlib import Path

from pydantic import BaseModel, Field

from ag_ui.core import EventType, StateSnapshotEvent # type: ignore
from pydantic_ai import Agent
from pydantic_ai.tools import Tool # type: ignore
from pydantic_ai.ag_ui import StateDeps
from pydantic_ai._run_context import RunContext, AgentDepsT
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.output import OutputDataT
from pydantic_ai.models import Model, KnownModelName
from pydantic_ai.providers import Provider

from control_toolbox.core import DataModel, AttributesGroup

from control_toolbox.tools.identification import IdentificationProps, FOPDTModel
from control_toolbox.tools.information import ModelDescription
from control_toolbox.tools.pid_tuning import UltimateTuningProps, PIDParameters, LambdaTuningProps
from control_toolbox.tools.analysis import SettlingTimeProps, InflectionPointProps, FindPeaksProps
from control_toolbox.tools.simulation import SimulationStepResponseProps, StepProps

from control_toolbox.tools.information import get_fmu_names as _get_fmu_names
from control_toolbox.tools.information import get_model_description as _get_model_description
from control_toolbox.tools.identification import identify_fopdt_from_step as _identify_fopdt_from_step
from control_toolbox.tools.simulation import simulate_step_response as _simulate_step_response
from control_toolbox.tools.simulation import simulate as _simulate
from control_toolbox.tools.analysis import find_inflection_point as _find_inflection_point
from control_toolbox.tools.analysis import find_characteristic_points as _find_characteristic_points
from control_toolbox.tools.analysis import find_peaks as _find_peaks
from control_toolbox.tools.analysis import find_settling_time as _find_settling_time
from control_toolbox.tools.analysis import find_rise_time as _find_rise_time
from control_toolbox.tools.pid_tuning import lambda_tuning as _lambda_tuning
from control_toolbox.tools.pid_tuning import zn_pid_tuning as _zn_pid_tuning
from control_toolbox.tools.plotting import plot_data


from openai import AsyncOpenAI

from control_toolbox.storage import InMemoryDataStorage, StoredRepresentation, ReprStore
from control_toolbox.core import DataModel, DataModelTeaser
from typing import Optional
import uuid

# System prompt with tuning method docume
__all__ = [
    # modules and global variables
    'os', 'uuid',
    # typing
    'List', 'Optional', 'Dict', 'Literal', 'Any', 'Type', 'TypeVar', 'Union', 'Callable', 'Generic', 'Dict', 'Optional', 'Tuple', 'Type', 'TypeVar', 'Union', 'get_type_hints', 'get_origin', 'get_args', 'Optional', 'Union', 'TypeVar', 'Type', 'Literal', 'Dict', 'Any', 'List', 'get_origin', 'get_args', 'get_type_hints',
    'wraps', 'signature', 'Parameter', 'Signature',
    # dotenv/logging/pathlib
    'load_dotenv', 'getLogger', 'Path',
    # pydantic
    'BaseModel', 'Field',
    # ag_ui
    'EventType', 'StateSnapshotEvent', 'StateDeps',
    # AI agent infrastructure
    'Agent', 'Tool', 'StateDeps', 'RunContext', 'OpenAIChatModel', 'AgentDepsT', 'OutputDataT', 'Model', 'KnownModelName', 'Provider',
    # control_toolbox core and tunings
    'DataModel', 'AttributesGroup',
    'InflectionPointProps', 'IdentificationProps', 'FOPDTModel', 'ModelDescription', 'UltimateTuningProps', 'PIDParameters', 'LambdaTuningProps',
    'SettlingTimeProps', 'SimulationStepResponseProps', 'StepProps', 'FindPeaksProps',
    # control_toolbox functions/tools (internal names)
    '_get_fmu_names', '_get_model_description', '_identify_fopdt_from_step', '_simulate_step_response', '_simulate',
    '_find_inflection_point', '_find_characteristic_points', '_find_peaks', '_find_settling_time', '_find_rise_time',
    '_lambda_tuning', '_zn_pid_tuning',
    'plot_data',
    # openai
    'AsyncOpenAI',
    # stored_model.py explicit imports
    'InMemoryDataStorage', 'StoredRepresentation', 'ReprStore', 'DataModelTeaser',
]