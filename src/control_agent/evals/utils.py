from typing import List, Dict, Any, Optional
from pydantic_evals.evaluators import EvaluatorContext
from pydantic_ai_examples.evals.custom_evaluators import SpanQuery


def get_called_tools(ctx: EvaluatorContext[object, object, object], agent_name: str) -> List[str]:
    """
    Extract the list of tools called by an agent in the order they were called.
    
    Args:
        ctx: Evaluation context with span tree
        agent_name: Name of the agent to extract tools from
        
    Returns:
        List of tool names in the order they were called
    """
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


def get_tool_call_counts(ctx: EvaluatorContext[object, object, object], agent_name: str) -> Dict[str, int]:
    """
    Count how many times each tool was called by an agent.
    
    Args:
        ctx: Evaluation context with span tree
        agent_name: Name of the agent to extract tools from
        
    Returns:
        Dictionary mapping tool names to their call counts
    """
    called_tools = get_called_tools(ctx, agent_name)
    counts: Dict[str, int] = {}
    for tool in called_tools:
        counts[tool] = counts.get(tool, 0) + 1
    return counts


def check_list_item_sequence(list_to_check: List[str], expected_sequence: List[str]) -> bool:
    """
    Check if list_to_check contains all items from expected_sequence in the correct order.
    
    Args:
        list_to_check: The list to check
        expected_sequence: The expected sequence of items
        
    Returns:
        True if all items are present and in correct order, False otherwise
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


def get_tool_result(ctx: EvaluatorContext[object, object, object], agent_name: str, tool_name: str) -> Optional[Any]:
    """
    Extract the result from a specific tool call in the span tree.
    
    Args:
        ctx: Evaluation context with span tree
        agent_name: Name of the agent
        tool_name: Name of the tool to get result from
        
    Returns:
        The tool result if found, None otherwise
    """
    tool_call_span = ctx.span_tree.first(
        SpanQuery(
            name_equals='agent run',
            has_attributes={'agent_name': agent_name},
            stop_recursing_when=SpanQuery(name_equals='agent run'),
            some_descendant_has=SpanQuery(
                name_equals='running tool',
                has_attributes={'gen_ai.tool.name': tool_name}
            ),
        )
    )
    
    if tool_call_span is None:
        return None
    
    # Try to find the tool result in the span attributes or children
    # Tool results might be in different places depending on the instrumentation
    if hasattr(tool_call_span, 'attributes'):
        # Check for result in attributes
        if 'gen_ai.tool.result' in tool_call_span.attributes:
            return tool_call_span.attributes['gen_ai.tool.result']
        if 'result' in tool_call_span.attributes:
            return tool_call_span.attributes['result']
    
    # Check children for result spans
    if hasattr(tool_call_span, 'children'):
        for child in tool_call_span.children:
            if hasattr(child, 'name') and 'result' in child.name.lower():
                if hasattr(child, 'attributes') and 'result' in child.attributes:
                    return child.attributes.get('result')
    
    return None


def parse_result(result: Any) -> Optional[Dict[str, Any]]:
    """
    Parse a tool result into a dictionary, handling various formats.
    
    Args:
        result: The result to parse (can be dict, Pydantic model, object, etc.)
        
    Returns:
        Dictionary representation of the result, or None if parsing fails
    """
    if isinstance(result, dict):
        return result
    
    # Try to extract from object attributes
    if hasattr(result, '__dict__'):
        return result.__dict__
    
    # Try to access common attributes
    if hasattr(result, 'data'):
        return parse_result(result.data)
    
    # If it's a Pydantic model, try model_dump
    if hasattr(result, 'model_dump'):
        return result.model_dump()
    
    # If it's a Pydantic model, try dict()
    if hasattr(result, 'dict'):
        return result.dict()
    
    return None
