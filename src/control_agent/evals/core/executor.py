"""
Plan executor that executes experiments following a pre-generated plan.

The executor:
1. Reconstructs context from the plan
2. Executes tool calls in the planned sequence
3. Monitors execution against the plan
"""
from __future__ import annotations
from typing import Dict, Any, Optional, Type, Callable, Coroutine, List
from pydantic import BaseModel, Field
from control_agent.agent.core.types import *
from control_agent.agent.core.agent import create_agent, OutputDataT
from control_agent.agent.tools.context import get_tools as get_tools_ctx, DepsType, SimContext
from control_agent.agent.core.model import get_default_model
from control_agent.evals.core.planning import ExperimentPlan, ToolCallPlan
from pydantic_ai.ag_ui import StateDeps as PydanticStateDeps
from pathlib import Path
from rich.console import Console

console = Console()


class PlanExecutionResult(BaseModel):
    """Result of plan execution."""
    experiment_name: str
    plan: ExperimentPlan
    success: bool
    executed_tools: List[str] = Field(default_factory=list)
    skipped_tools: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    result: Optional[Any] = None


def reconstruct_context_from_plan(plan: ExperimentPlan) -> SimContext:
    """
    Reconstruct SimContext from the experiment plan.
    
    Args:
        plan: Experiment plan with context setup information
        
    Returns:
        SimContext configured according to the plan
    """
    context_setup = plan.context_setup
    
    sim_context = SimContext(
        fmu_folder=context_setup.get("fmu_folder", str(Path("models/fmus"))),
        notes=context_setup.get("notes", [])
    )
    
    # Set current FMU if specified
    if "current_fmu" in context_setup:
        sim_context.current_fmu = context_setup["current_fmu"]
    
    return sim_context


def create_plan_guided_prompt(plan: ExperimentPlan) -> str:
    """
    Create a system prompt that guides the agent to follow the plan.
    
    Args:
        plan: Experiment plan to follow
        
    Returns:
        Enhanced prompt with plan guidance and motivations
    """
    tool_sequence_parts = []
    for i, tool in enumerate(plan.tool_sequence, 1):
        req_marker = "(REQUIRED)" if tool.is_required else "(OPTIONAL)"
        tool_line = f"{i}. {tool.tool_name} {req_marker}"
        tool_line += f"\n   Description: {tool.description}"
        if tool.motivation:
            tool_line += f"\n   Why: {tool.motivation}"
        tool_sequence_parts.append(tool_line)
    
    tool_sequence_str = "\n".join(tool_sequence_parts)
    
    prompt = f"""You are executing a pre-planned experiment: {plan.experiment_name}

EXECUTION PLAN:
{tool_sequence_str}

INSTRUCTIONS:
1. Follow the tool sequence above in order
2. Required tools MUST be called (they are essential for the experiment)
3. Optional tools may be called if needed for context or verification
4. Do not skip required tools
5. Each tool should be called at most {max([t.max_runs for t in plan.tool_sequence] + [1])} time(s)
6. The "Why" explanations above describe the purpose of each tool - use them to guide your execution

User Query: {plan.input_query}

Execute this experiment following the plan above."""
    
    return prompt


def get_plan_executor_runner(
    plan: ExperimentPlan,
    output_model: Type[OutputDataT],
    results_keeper: Dict[str, AgentRunResult[OutputDataT]],
    ctx_keeper: Dict[str, SimContext]
) -> Callable[[str], Coroutine[Any, Any, AgentRunResult[OutputDataT]]]:
    """
    Create a runner function that executes an experiment following a plan.
    
    Args:
        plan: Experiment plan to follow
        output_model: Expected output type
        results_keeper: Dictionary to store results
        ctx_keeper: Dictionary to store contexts
        
    Returns:
        Runner function that executes the plan
    """
    # Reconstruct context from plan
    sim_context = reconstruct_context_from_plan(plan)
    
    # Create agent with context-aware tools
    agent = create_agent(
        model=get_default_model(),
        tools=get_tools_ctx(),
        deps=DepsType,
        output_type=output_model,
        max_retries=20,
    )
    
    # Create plan-guided prompt
    plan_prompt = create_plan_guided_prompt(plan)
    
    def runner(input: str) -> AgentRunResult[OutputDataT]:
        try:
            # Store context
            ctx_keeper[input] = sim_context
            
            # Execute with plan-guided prompt
            # Combine plan guidance with original input
            enhanced_input = f"{plan_prompt}\n\nOriginal Query: {input}"
            
            result = agent.run_sync(
                enhanced_input,
                output_type=output_model,
                deps=PydanticStateDeps(sim_context)
            )
            
            results_keeper[input] = result
            
            # Verify plan execution
            executed_tools = extract_executed_tools(result)
            verify_plan_execution(plan, executed_tools)
            
            return result
        except Exception as e:
            console.print(f"[red]ERROR in plan executor: {e}[/red]")
            raise
    
    return runner


def extract_executed_tools(result: AgentRunResult[Any]) -> List[str]:
    """
    Extract list of tools that were actually executed.
    
    Args:
        result: Agent run result
        
    Returns:
        List of tool names in execution order
    """
    executed_tools: List[str] = []
    
    for message in result.all_messages():
        for part in message.parts:
            if isinstance(part, ToolCallPart) and part.tool_name != "final_result":
                executed_tools.append(part.tool_name)
    
    return executed_tools


def verify_plan_execution(plan: ExperimentPlan, executed_tools: List[str]) -> PlanExecutionResult:
    """
    Verify that plan execution followed the plan.
    
    Args:
        plan: Original plan
        executed_tools: Tools that were actually executed
        
    Returns:
        PlanExecutionResult with verification details
    """
    required_tools = [t.tool_name for t in plan.tool_sequence if t.is_required]
    optional_tools = [t.tool_name for t in plan.tool_sequence if not t.is_required]
    
    executed_set = set(executed_tools)
    required_set = set(required_tools)
    
    missing_required = required_set - executed_set
    skipped_optional = set(optional_tools) - executed_set
    
    success = len(missing_required) == 0
    
    errors = []
    if missing_required:
        errors.append(f"Missing required tools: {', '.join(missing_required)}")
    
    return PlanExecutionResult(
        experiment_name=plan.experiment_name,
        plan=plan,
        success=success,
        executed_tools=executed_tools,
        skipped_tools=list(skipped_optional),
        errors=errors
    )


def execute_plan(
    plan: ExperimentPlan,
    output_model: Type[OutputDataT],
    results_keeper: Dict[str, AgentRunResult[OutputDataT]],
    ctx_keeper: Dict[str, SimContext],
    input_query: Optional[str] = None
) -> tuple[AgentRunResult[OutputDataT], PlanExecutionResult]:
    """
    Execute an experiment plan.
    
    Args:
        plan: Experiment plan to execute
        output_model: Expected output type
        results_keeper: Dictionary to store results
        ctx_keeper: Dictionary to store contexts
        input_query: Optional override for input query (uses plan's query if None)
        
    Returns:
        Tuple of (agent result, execution verification)
    """
    runner = get_plan_executor_runner(plan, output_model, results_keeper, ctx_keeper)
    
    query = input_query or plan.input_query
    result = runner(query)
    
    executed_tools = extract_executed_tools(result)
    verification = verify_plan_execution(plan, executed_tools)
    
    return result, verification

