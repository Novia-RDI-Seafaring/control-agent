from dataclasses import dataclass
from typing import List

from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
)
from control_agent.evals.utils import get_called_tools, check_list_item_sequence
from logging import getLogger
logger = getLogger(__name__)


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
          