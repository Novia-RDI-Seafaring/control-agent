"""
Planning agent that analyzes experiments and creates execution plans.

The planning agent:
1. Analyzes experiment datasets to understand required tools
2. Creates structured execution plans with tool call sequences
3. Provides context reconstruction for plan execution
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from control_agent.agent.core.types import *
from control_agent.agent.core.model import get_default_model
from control_agent.agent.core.agent import create_agent
from control_agent.evals.experiments import datasets
from control_agent.evals.evaluators.required_tool_use_evaluator import RequiredToolUseEvaluator, ToolUseSpec
from control_agent.agent.tools.context import SimContext, get_tools as get_tools_ctx
from pathlib import Path


@dataclass
class ToolCallPlan:
    """Represents a planned tool call in the execution sequence."""
    tool_name: str
    description: str
    expected_order: int
    is_required: bool = True
    max_runs: int = 1
    parameters_hint: Optional[Dict[str, Any]] = None
    motivation: str = ""  # Explanation of why this tool is needed


@dataclass
class ExperimentPlan:
    """Complete execution plan for an experiment."""
    experiment_name: str
    input_query: str
    output_type: Type[OutputDataT]
    tool_sequence: List[ToolCallPlan]
    context_setup: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


class PlanningResponse(BaseModel):
    """Response from planning agent containing execution plan."""
    experiment_name: str
    plan: ExperimentPlan
    reasoning: str


def get_tool_motivation(tool_name: str, experiment_name: str, input_query: str, is_required: bool) -> str:
    """
    Generate motivation/reasoning for why a tool is needed in the plan.
    
    The planning agent should only see:
    1. System prompt (from create_agent)
    2. Query (from experiment input)
    3. Tool docstrings (public API documentation)
    
    It should NOT see:
    - Tool implementations
    - Internal tool details
    - Execution context or state
    
    Args:
        tool_name: Name of the tool (from RequiredToolUseEvaluator)
        experiment_name: Name of the experiment
        input_query: The input query for the experiment
        is_required: Whether the tool is required or optional (from evaluator)
        
    Returns:
        Motivation string explaining why this tool is needed
    """
    # Get tool description from docstring (public API documentation)
    # This is what the planning agent should see - tool documentation, not implementation
    base_motivation = None
    try:
        tools = get_tools_ctx()
        for tool in tools:
            if tool.name == tool_name:
                # Extract description/docstring (public API documentation)
                docstring = tool.description or ""
                if docstring:
                    # Get first meaningful sentence/line from docstring
                    lines = docstring.strip().split('\n')
                    # Skip metadata lines (PREREQUISITES, IMPORTANT, etc.)
                    for line in lines:
                        cleaned = line.strip()
                        # Skip empty lines and metadata markers
                        if cleaned and not cleaned.startswith('**') and len(cleaned) > 10:
                            # Remove any remaining metadata prefixes
                            cleaned = cleaned.replace('**PREREQUISITES**:', '').replace('**IMPORTANT**:', '').strip()
                            if cleaned:
                                base_motivation = cleaned
                                break
                break
    except Exception:
        pass  # Fall back to name-based inference
    
    # Fallback: Infer from tool name if docstring not available
    if not base_motivation:
        if "simulate" in tool_name.lower() and "step" in tool_name.lower():
            base_motivation = "Run a step response simulation to generate time-domain data"
        elif "identify" in tool_name.lower() or "fopdt" in tool_name.lower():
            base_motivation = "Extract model parameters from simulation data"
        elif "find" in tool_name.lower() and "peak" in tool_name.lower():
            base_motivation = "Detect oscillation peaks in response data"
        elif "find" in tool_name.lower() and "characteristic" in tool_name.lower():
            base_motivation = "Identify key response characteristics"
        elif "find" in tool_name.lower() and "settling" in tool_name.lower():
            base_motivation = "Determine settling time from response data"
        elif "tuning" in tool_name.lower() and "zn" in tool_name.lower():
            base_motivation = "Calculate PI/PID controller parameters using Ziegler-Nichols method"
        elif "tuning" in tool_name.lower() and "lambda" in tool_name.lower():
            base_motivation = "Calculate PI/PID controller parameters using Lambda tuning method"
        elif "get" in tool_name.lower() and "fmu" in tool_name.lower() and "name" in tool_name.lower():
            base_motivation = "Discover available FMU models in the system"
        elif "choose" in tool_name.lower() and "fmu" in tool_name.lower():
            base_motivation = "Select a specific FMU model to work with"
        elif "get" in tool_name.lower() and "model" in tool_name.lower() and "description" in tool_name.lower():
            base_motivation = "Obtain model metadata and structure information"
        elif "plot" in tool_name.lower() or "visual" in tool_name.lower():
            base_motivation = "Visualize signal data to verify results or inspect characteristics"
        else:
            base_motivation = f"Execute {tool_name} as part of the experiment workflow"
    
    # Add experiment-specific context based on query and experiment name
    if experiment_name == "system_identification":
        if tool_name == "simulate_step_response":
            base_motivation = f"{base_motivation}. Required to generate step response data that will be analyzed to identify FOPDT parameters."
        elif tool_name == "identify_fopdt_from_step":
            base_motivation = f"{base_motivation}. This extracts K, T, L parameters from the step response data."
    elif experiment_name == "ultimate_gain":
        if tool_name == "find_peaks":
            base_motivation = f"{base_motivation}. Needed for Ziegler-Nichols ultimate gain method."
    elif experiment_name in ["z_n", "lambda_tuning", "tuning_overshoot"]:
        if "tuning" in tool_name.lower():
            base_motivation = f"{base_motivation}. Calculates the controller parameters needed for the experiment."
    
    # Add required/optional status (from evaluator)
    if is_required:
        return f"{base_motivation}. This tool is REQUIRED for the experiment to succeed."
    else:
        return f"{base_motivation}. This tool is OPTIONAL but may provide helpful context or verification."


def analyze_experiment_for_planning(experiment_name: str) -> ExperimentPlan:
    """
    Analyze an experiment dataset to create an execution plan.
    
    Args:
        experiment_name: Name of the experiment to analyze
        
    Returns:
        ExperimentPlan with tool sequence and context requirements
    """
    if experiment_name not in datasets:
        raise ValueError(f"Experiment '{experiment_name}' not found in datasets")
    
    dataset, OutputDataT = datasets[experiment_name]
    
    # Extract tool requirements from evaluators
    tool_sequence: List[ToolCallPlan] = []
    required_tools: List[str] = []
    optional_tools: List[str] = []
    
    # Analyze each case in the dataset
    for case in dataset.cases:
        input_query = case.inputs
        
        # Look for RequiredToolUseEvaluator in evaluators
        for evaluator in case.evaluators:
            if isinstance(evaluator, RequiredToolUseEvaluator):
                # Extract required tools
                for tool_spec in evaluator.required_tools:
                    required_tools.append(tool_spec.name)
                    motivation = get_tool_motivation(tool_spec.name, experiment_name, input_query, is_required=True)
                    tool_sequence.append(ToolCallPlan(
                        tool_name=tool_spec.name,
                        description=f"Required tool: {tool_spec.name}",
                        expected_order=len(tool_sequence),
                        is_required=True,
                        max_runs=tool_spec.max_runs or 1,
                        motivation=motivation
                    ))
                
                # Extract optional tools
                for tool_spec in evaluator.optional_tools:
                    optional_tools.append(tool_spec.name)
                    motivation = get_tool_motivation(tool_spec.name, experiment_name, input_query, is_required=False)
                    tool_sequence.append(ToolCallPlan(
                        tool_name=tool_spec.name,
                        description=f"Optional tool: {tool_spec.name}",
                        expected_order=len(tool_sequence),
                        is_required=False,
                        max_runs=tool_spec.max_runs or 1,
                        motivation=motivation
                    ))
    
    # If no explicit tool requirements found, infer from input query
    if not tool_sequence:
        tool_sequence = infer_tools_from_query(input_query, experiment_name)
    
    # Determine context setup based on experiment type
    context_setup = determine_context_setup(experiment_name, input_query)
    
    plan = ExperimentPlan(
        experiment_name=experiment_name,
        input_query=input_query if hasattr(dataset, 'cases') and dataset.cases else "",
        output_type=OutputDataT,
        tool_sequence=tool_sequence,
        context_setup=context_setup,
        notes=[
            f"Experiment: {experiment_name}",
            f"Required tools: {', '.join(required_tools) if required_tools else 'inferred from query'}",
            f"Optional tools: {', '.join(optional_tools) if optional_tools else 'none'}"
        ]
    )
    
    return plan


def infer_tools_from_query(query: str, experiment_name: str = "") -> List[ToolCallPlan]:
    """
    Infer likely tool sequence from the input query.
    
    This is a fallback when explicit tool requirements aren't available.
    """
    query_lower = query.lower()
    tool_sequence: List[ToolCallPlan] = []
    order = 0
    
    # Common patterns
    if "list" in query_lower and "model" in query_lower:
        tool_sequence.append(ToolCallPlan(
            tool_name="get_fmu_names",
            description="List available FMU models",
            expected_order=order,
            is_required=True,
            motivation=get_tool_motivation("get_fmu_names", experiment_name, query, True)
        ))
        order += 1
    
    if "description" in query_lower or "metadata" in query_lower:
        tool_sequence.append(ToolCallPlan(
            tool_name="get_model_description",
            description="Get model description/metadata",
            expected_order=order,
            is_required=True,
            motivation=get_tool_motivation("get_model_description", experiment_name, query, True)
        ))
        order += 1
    
    if "simulate" in query_lower or "step response" in query_lower:
        tool_sequence.append(ToolCallPlan(
            tool_name="simulate_step_response",
            description="Simulate step response",
            expected_order=order,
            is_required=True,
            motivation=get_tool_motivation("simulate_step_response", experiment_name, query, True)
        ))
        order += 1
    
    if "identify" in query_lower or "fopdt" in query_lower:
        tool_sequence.append(ToolCallPlan(
            tool_name="identify_fopdt_from_step",
            description="Identify FOPDT parameters",
            expected_order=order,
            is_required=True,
            motivation=get_tool_motivation("identify_fopdt_from_step", experiment_name, query, True)
        ))
        order += 1
    
    if "ultimate" in query_lower or "oscillation" in query_lower:
        tool_sequence.append(ToolCallPlan(
            tool_name="find_peaks",
            description="Find peaks in oscillations",
            expected_order=order,
            is_required=True,
            motivation=get_tool_motivation("find_peaks", experiment_name, query, True)
        ))
        order += 1
    
    if "tune" in query_lower or "lambda" in query_lower:
        tool_sequence.append(ToolCallPlan(
            tool_name="lambda_tuning",
            description="Perform lambda tuning",
            expected_order=order,
            is_required=True,
            motivation=get_tool_motivation("lambda_tuning", experiment_name, query, True)
        ))
        order += 1
    
    if "ziegler" in query_lower or "nichols" in query_lower or "z_n" in query_lower:
        tool_sequence.append(ToolCallPlan(
            tool_name="zn_pid_tuning",
            description="Perform Ziegler-Nichols tuning",
            expected_order=order,
            is_required=True,
            motivation=get_tool_motivation("zn_pid_tuning", experiment_name, query, True)
        ))
        order += 1
    
    return tool_sequence


def determine_context_setup(experiment_name: str, query: str) -> Dict[str, Any]:
    """
    Determine what context setup is needed for the experiment.
    
    Returns:
        Dictionary with context configuration
    """
    context_setup = {
        "fmu_folder": str(Path("models/fmus")),
        "current_fmu": "PI_FOPDT_2",  # Default FMU
        "notes": []
    }
    
    # Experiment-specific context adjustments
    if experiment_name in ["list_model_names"]:
        context_setup["needs_fmu_selection"] = False
    elif experiment_name in ["list_iop", "get_metadata", "model_description"]:
        context_setup["needs_fmu_selection"] = True
    else:
        context_setup["needs_fmu_selection"] = True
    
    return context_setup


def create_planning_agent() -> Agent[str, PlanningResponse]:
    """
    Create an agent that analyzes experiments and creates execution plans.
    
    Returns:
        Planning agent configured to generate ExperimentPlan objects
    """
    planning_prompt = """You are a planning agent that analyzes control system experiments and creates detailed execution plans.

Your task is to:
1. Analyze the experiment's requirements and input query
2. Determine the sequence of tool calls needed
3. Identify any context setup requirements
4. Create a structured execution plan

Consider:
- Tool dependencies (some tools must be called before others)
- Context requirements (FMU selection, simulation setup)
- Expected tool call order based on the experiment type
- Required vs optional tools

Be thorough and consider all necessary steps for successful experiment execution.
"""
    
    agent = create_agent(
        model=get_default_model(),
        tools=[],  # Planning agent doesn't need tools, just analyzes
        output_type=PlanningResponse,
        max_retries=3,
        name="PlanningAgent"
    )
    
    # Override instructions for planning
    agent._instructions = planning_prompt
    
    return agent


def plan_experiment(experiment_name: str) -> ExperimentPlan:
    """
    Create an execution plan for an experiment using rule-based analysis.
    
    Args:
        experiment_name: Name of the experiment
        
    Returns:
        ExperimentPlan with tool sequence, context setup, and motivations
        
    Note:
        Uses rule-based planning that extracts all necessary information from
        experiment evaluators. Each tool in the plan includes a motivation
        explaining why it's needed.
    """
    return analyze_experiment_for_planning(experiment_name)


def plan_all_experiments(experiment_names: List[str]) -> Dict[str, ExperimentPlan]:
    """
    Create execution plans for multiple experiments.
    
    Args:
        experiment_names: List of experiment names to plan
        
    Returns:
        Dictionary mapping experiment names to their plans
    """
    plans: Dict[str, ExperimentPlan] = {}
    
    for exp_name in experiment_names:
        try:
            plan = plan_experiment(exp_name)
            plans[exp_name] = plan
        except Exception as e:
            print(f"Warning: Could not create plan for '{exp_name}': {e}")
    
    return plans

