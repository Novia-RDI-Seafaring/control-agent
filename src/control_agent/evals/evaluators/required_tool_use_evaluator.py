from dataclasses import dataclass, field
from typing import List, Optional

from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from control_agent.evals.utils import get_called_tools, get_tool_call_counts, get_successful_tool_call_counts
from logging import getLogger

logger = getLogger(__name__)


@dataclass
class ToolUseSpec:
    """Specification for a tool that should be used"""
    name: str
    max_runs: Optional[int] = 1  # Maximum allowed runs for this tool


@dataclass
class RequiredToolUseEvaluator(Evaluator[object, object, object]):
    """
    Evaluator that checks if required tools were called and within their max_runs limit.
    Also optionally logs which optional tools were called.
    """
    required_tools: List[ToolUseSpec]  # Tools that must be called
    optional_tools: List[ToolUseSpec] = field(default_factory=list)  # Tools that may be called (won't fail if missing)
    agent_name: str = "FMIAgent"
    
    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> EvaluationReason:
        """Check that required tools were called and within max_runs limits"""
        called_tools = get_called_tools(ctx, self.agent_name)
        # Use successful tool call counts (excludes ToolExecutionError results)
        tool_counts = get_successful_tool_call_counts(ctx, self.agent_name)
        # Also get total counts for logging
        total_tool_counts = get_tool_call_counts(ctx, self.agent_name)
        
        logger.info(f"Expected required tools: {[t.name for t in self.required_tools]}")
        logger.info(f"Expected optional tools: {[t.name for t in self.optional_tools]}")
        logger.info(f"Actual called tools: {called_tools}")
        logger.info(f"Total tool call counts (including failures): {total_tool_counts}")
        logger.info(f"Successful tool call counts (excluding failures): {tool_counts}")
        
        errors = []
        warnings = []
        
        # Check required tools
        for tool_spec in self.required_tools:
            tool_name = tool_spec.name
            max_runs = tool_spec.max_runs or 1
            
            # Check if tool was called at all (including failures)
            if tool_name not in called_tools:
                errors.append(f"Required tool '{tool_name}' was not called")
                continue
            
            # Check max_runs limit using successful calls only
            successful_count = tool_counts.get(tool_name, 0)
            total_count = total_tool_counts.get(tool_name, 0)
            
            if successful_count > max_runs:
                errors.append(
                    f"Required tool '{tool_name}' was successfully called {successful_count} times, "
                    f"but max_runs is {max_runs}"
                )
            elif successful_count == 0 and total_count > 0:
                # Tool was called but all calls failed
                errors.append(
                    f"Required tool '{tool_name}' was called {total_count} time(s) but all calls failed "
                    f"(likely due to guardrail violations or errors)"
                )
            else:
                if total_count > successful_count:
                    logger.info(
                        f"Required tool '{tool_name}' called {total_count} time(s) total, "
                        f"{successful_count} successful (max: {max_runs})"
                    )
                else:
                    logger.info(f"Required tool '{tool_name}' called {successful_count} time(s) (max: {max_runs})")
        
        # Check optional tools (only log, don't fail)
        for tool_spec in self.optional_tools:
            tool_name = tool_spec.name
            max_runs = tool_spec.max_runs or 1
            
            if tool_name not in called_tools:
                logger.info(f"Optional tool '{tool_name}' was not called (this is OK)")
                continue
            
            # Check max_runs limit for optional tools using successful calls
            successful_count = tool_counts.get(tool_name, 0)
            total_count = total_tool_counts.get(tool_name, 0)
            
            if successful_count > max_runs:
                warnings.append(
                    f"Optional tool '{tool_name}' was successfully called {successful_count} times, "
                    f"but max_runs is {max_runs}"
                )
            else:
                if total_count > successful_count:
                    logger.info(
                        f"Optional tool '{tool_name}' called {total_count} time(s) total, "
                        f"{successful_count} successful (max: {max_runs})"
                    )
                else:
                    logger.info(f"Optional tool '{tool_name}' called {successful_count} time(s) (max: {max_runs})")
        
        # If there are errors, fail
        if errors:
            reason = "Tool usage validation failed: " + "; ".join(errors)
            if warnings:
                reason += " | Warnings: " + "; ".join(warnings)
            logger.error(reason)
            return EvaluationReason(value=False, reason=reason)
        
        # If there are only warnings, still pass but log them
        if warnings:
            reason = "All required tools called correctly. Warnings: " + "; ".join(warnings)
            logger.warning(reason)
            return EvaluationReason(value=True, reason=reason)
        
        # All checks passed
        reason = "All required tools were called within their max_runs limits"
        logger.info(reason)
        return EvaluationReason(value=True, reason=reason)

