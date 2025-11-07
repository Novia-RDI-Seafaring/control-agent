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
    called_tools:List[str] = []
    for span in ctx.span_tree:
        if span.name == 'agent run' and span.attributes['agent_name'] == agent_name:
            for child in span.descendants:
                if child.name == 'running tool':
                    called_tools.append(str(child.attributes['gen_ai.tool.name']))
    return called_tools

@dataclass
class ToolSequenceEvaluator(Evaluator[object, object, object]):
    agent_name: str
    tool_call_sequence: List[str]

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> bool:
        called_tools = get_called_tools(ctx, self.agent_name)
        uncalled = []
        for tool in self.tool_call_sequence:
            if tool not in called_tools: uncalled.append(tool)
                
        if len(uncalled) > 0:
            logger.error(f"These tools were not called: {','.join(uncalled)}")
            return EvaluationReason(value=False, reason=f"These tools were not called: {','.join(uncalled)}")

        i2 = 0
        for i in range(len(self.tool_call_sequence)):
            tool = self.tool_call_sequence[i]
            if tool in called_tools[i2:]:
                i2 += 1
            else:
                logger.error(f"These tools were not called: {uncalled}")
                return EvaluationReason(value=False, reason=f"The tool {tool} was not called in the correct order")

        logger.info(f"All tools were called in the correct order")
        return EvaluationReason(value=True, reason="All tools were called in the correct order")
          