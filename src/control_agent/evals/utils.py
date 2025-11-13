from typing import List, Dict, Any, Optional
from pydantic_evals.evaluators import EvaluatorContext
from pydantic_ai_examples.evals.custom_evaluators import SpanQuery
from logging import getLogger

logger = getLogger(__name__)


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


def is_tool_execution_error(result: Any) -> bool:
    """
    Check if a tool result is a ToolExecutionError.
    
    Args:
        result: The tool result to check
        
    Returns:
        True if result is a ToolExecutionError, False otherwise
    """
    if result is None:
        return False  # None is not an error, just missing data
    
    # Check if it's a ToolExecutionError instance
    if hasattr(result, '__class__') and result.__class__.__name__ == 'ToolExecutionError':
        return True
    
    # Check if it's a dict with ToolExecutionError structure
    if isinstance(result, dict):
        # StateSnapshotEvent has 'type' and 'snapshot' - this is a success indicator
        if result.get('type') == 'STATE_SNAPSHOT' or 'snapshot' in result:
            return False  # StateSnapshotEvent is a success
        
        # ToolExecutionError has only a 'message' field (no other expected fields)
        # Successful results typically have 'type', 'snapshot', 'signals', 'data', etc.
        if 'message' in result:
            # If it only has 'message' and no success indicators, it's likely an error
            success_indicators = {'type', 'snapshot', 'signals', 'data', 'fmu_names', 'model_names', 
                                 'attributes', 'fopdt_checks', 'simulations', 'content'}
            has_success_indicator = any(key in result for key in success_indicators)
            
            # If only 'message' field exists without success indicators, it's an error
            if not has_success_indicator:
                return True
            
            # Also check if message explicitly indicates an error
            message = str(result.get('message', ''))
            if 'Guardrail violation' in message or 'ToolExecutionError' in message or 'not found' in message.lower() or 'failed' in message.lower() or 'error' in message.lower():
                return True
    
    # Check if result string representation indicates error
    result_str = str(result)
    if 'Guardrail violation' in result_str or 'ToolExecutionError' in result_str:
        return True
    
    # Check if it's a StateSnapshotEvent object (has type and snapshot attributes)
    if hasattr(result, 'type') and hasattr(result, 'snapshot'):
        if getattr(result, 'type', None) == 'STATE_SNAPSHOT' or hasattr(result, 'snapshot'):
            return False  # StateSnapshotEvent is a success
    
    return False


def _debug_span_tree(node, depth=0, tool_name=None):
    """Debug function to print span tree structure"""
    indent = "  " * depth
    node_info = f"{indent}Node: {node.name}"
    if hasattr(node, 'attributes'):
        attrs = node.attributes
        node_info += f" | Attributes: {list(attrs.keys())}"
        if 'gen_ai.tool.name' in attrs:
            node_info += f" | Tool: {attrs['gen_ai.tool.name']}"
        if 'gen_ai.tool.result' in attrs:
            result = attrs['gen_ai.tool.result']
            result_type = type(result).__name__
            if isinstance(result, dict):
                result_keys = list(result.keys())[:5]  # First 5 keys
                node_info += f" | Result (dict keys): {result_keys}"
            else:
                node_info += f" | Result type: {result_type}"
        if 'result' in attrs:
            result = attrs['result']
            result_type = type(result).__name__
            node_info += f" | Result (attr 'result'): {result_type}"
        if 'content' in attrs:
            content = attrs['content']
            if isinstance(content, dict):
                content_keys = list(content.keys())[:5]
                node_info += f" | Content (dict keys): {content_keys}"
            else:
                node_info += f" | Content type: {type(content).__name__}"
    logger.debug(node_info)
    
    if hasattr(node, 'children'):
        for child in node.children:
            _debug_span_tree(child, depth + 1, tool_name)


def get_successful_tool_call_counts(ctx: EvaluatorContext[object, object, object], agent_name: str) -> Dict[str, int]:
    """
    Count how many times each tool was successfully called (excluding ToolExecutionError results).
    
    Args:
        ctx: Evaluation context with span tree
        agent_name: Name of the agent to extract tools from
        
    Returns:
        Dictionary mapping tool names to their successful call counts
    """
    counts: Dict[str, int] = {}
    
    # Try to access message history from ctx.output if it's an AgentRunResult
    # This is more reliable than span tree for getting tool results
    message_history_results: Dict[str, List[Any]] = {}
    try:
        if hasattr(ctx, 'output') and ctx.output is not None:
            # Check if output has all_messages method (AgentRunResult)
            if hasattr(ctx.output, 'all_messages'):
                from pydantic_ai import ToolReturnPart
                for message in ctx.output.all_messages():
                    for part in message.parts:
                        if isinstance(part, ToolReturnPart) and part.tool_name != 'final_result':
                            tool_name = part.tool_name
                            if tool_name not in message_history_results:
                                message_history_results[tool_name] = []
                            # Extract content from tool return
                            content = getattr(part, 'content', None)
                            if content is not None:
                                message_history_results[tool_name].append(content)
    except Exception as e:
        logger.debug(f"Could not access message history: {e}")
    
    # First, check if final_result was called (for fallback heuristic)
    all_called_tools = get_called_tools(ctx, agent_name)
    has_final_result = 'final_result' in all_called_tools
    final_result_index = all_called_tools.index('final_result') if has_final_result else None
    
    # Traverse span tree to find tool calls and their results
    for span in ctx.span_tree:
        if span.name == 'agent run' and span.attributes.get('agent_name') == agent_name:
            def collect_successful_tools(node):
                if node.name == 'running tool':
                    tool_name = str(node.attributes.get('gen_ai.tool.name', ''))
                    if not tool_name:
                        return
                    
                    # DEBUG: Print span tree structure for this tool
                    logger.debug(f"=== DEBUG: Tool '{tool_name}' ===")
                    _debug_span_tree(node, depth=0, tool_name=tool_name)
                    
                    # Try to find the tool result
                    result = None
                    
                    # First, check message history (most reliable)
                    if tool_name in message_history_results:
                        # Use the LAST result from message history (most recent call)
                        results_list = message_history_results[tool_name]
                        if results_list:
                            result = results_list[-1]
                            logger.debug(f"  Found result in message history (using last of {len(results_list)} results)")
                    
                    # If not in message history, check span tree
                    if result is None:
                        # Check node attributes first
                        if hasattr(node, 'attributes'):
                            result = node.attributes.get('gen_ai.tool.result') or node.attributes.get('result')
                            logger.debug(f"  Direct attributes result: {result is not None}")
                        
                        # Check all children recursively for result
                        if result is None and hasattr(node, 'children'):
                            def find_result_in_children(child_node):
                                nonlocal result
                                if result is not None:
                                    return
                                
                                # Check this node's attributes
                                if hasattr(child_node, 'attributes'):
                                    attrs = child_node.attributes
                                    result = (attrs.get('result') or 
                                             attrs.get('gen_ai.tool.result') or 
                                             attrs.get('content'))
                                    if result is not None:
                                        logger.debug(f"  Found result in child '{child_node.name}'")
                                        return
                                
                                # Recursively check children
                                if hasattr(child_node, 'children'):
                                    for grandchild in child_node.children:
                                        find_result_in_children(grandchild)
                            
                            for child in node.children:
                                find_result_in_children(child)
                    
                    logger.debug(f"  Final result found: {result is not None}")
                    if result is not None:
                        logger.debug(f"  Result type: {type(result).__name__}")
                        if isinstance(result, dict):
                            logger.debug(f"  Result keys: {list(result.keys())[:10]}")
                    
                    # If we found a result, check if it's an error
                    if result is not None:
                        is_error = is_tool_execution_error(result)
                        logger.debug(f"  Is error: {is_error}")
                        if not is_error:
                            counts[tool_name] = counts.get(tool_name, 0) + 1
                    else:
                        # FALLBACK: If we can't find the result anywhere, use heuristic
                        # If final_result was called and this tool appears before it, assume at least one success
                        tool_indices = [i for i, t in enumerate(all_called_tools) if t == tool_name]
                        if has_final_result and tool_indices:
                            # Check if LAST occurrence is before final_result
                            last_tool_index = tool_indices[-1]
                            if last_tool_index < final_result_index:
                                logger.debug(f"  Fallback: Counting as successful (final_result called after last tool call)")
                                counts[tool_name] = counts.get(tool_name, 0) + 1
                            else:
                                logger.debug(f"  Fallback: Not counting (last tool call not before final_result)")
                        else:
                            logger.debug(f"  Fallback: Not counting (no final_result or tool not called)")
                
                # Traverse children
                if hasattr(node, 'children'):
                    for child in node.children:
                        collect_successful_tools(child)
            
            collect_successful_tools(span)
    
    # Count successful calls from message history (more accurate)
    # This counts ALL successful calls, not just one per tool
    for tool_name, results_list in message_history_results.items():
        successful_count = sum(1 for r in results_list if not is_tool_execution_error(r))
        if successful_count > 0:
            counts[tool_name] = successful_count
            logger.debug(f"Message history: Tool '{tool_name}' had {successful_count} successful calls out of {len(results_list)}")
    
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
