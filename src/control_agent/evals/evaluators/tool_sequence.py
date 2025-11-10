from dataclasses import dataclass
from typing import List

from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from logging import getLogger
logger = getLogger(__name__)


def get_called_tools(ctx: EvaluatorContext[object, object, object], agent_name: str) -> List[str]:
    called_tools: List[str] = []
    for span in ctx.span_tree:
        if span.name == 'agent run' and span.attributes['agent_name'] == agent_name:
            # Use a recursive function to traverse in order
            def collect_tools_in_order(node):
                if node.name == 'running tool':
                    called_tools.append(str(node.attributes['gen_ai.tool.name']))
                # Traverse children in order
                if hasattr(node, 'children'):
                    for child in node.children:
                        collect_tools_in_order(child)
            
            collect_tools_in_order(span)
    return called_tools


def check_list_item_sequence(list_to_check: List[str], expected_sequence: List[str]) -> bool:
    """
    Check if list_to_check contains all items from expected_sequence in the correct order.
    
    Returns:
        bool: True if all items are present and in correct order, False otherwise
    """
    # Check if all expected items are present
    missing = [item for item in expected_sequence if item not in list_to_check]
    if missing:
        return False
    
    # Check order: find each item sequentially in list_to_check
    current_index = 0
    for expected_item in expected_sequence:
        try:
            found_index = list_to_check.index(expected_item, current_index)
            current_index = found_index + 1
        except ValueError:
            return False
    
    return True

@dataclass
class ToolSequenceEvaluator(Evaluator[object, object, object]):
    agent_name: str
    tool_call_sequence: List[str]

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> EvaluationReason:
        called_tools = get_called_tools(ctx, self.agent_name)
        logger.info(f"Expected sequence: {self.tool_call_sequence}")
        logger.info(f"Actual called tools: {called_tools}")
        
        # Check if all expected tools are present
        missing = [tool for tool in self.tool_call_sequence if tool not in called_tools]
        if missing:
            reason = f"These tools were not called: {','.join(missing)}"
            logger.error(reason)
            return EvaluationReason(value=False, reason=reason)
        
        # Check order using helper function
        if not check_list_item_sequence(called_tools, self.tool_call_sequence):
            reason = f"Tools were not called in the correct order. Expected: {self.tool_call_sequence}, Found: {called_tools}"
            logger.error(reason)
            return EvaluationReason(value=False, reason=reason)
        
        reason = "All tools were called in the correct order"
        logger.info(reason)
        return EvaluationReason(value=True, reason=reason)
          