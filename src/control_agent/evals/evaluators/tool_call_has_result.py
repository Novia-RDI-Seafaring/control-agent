from dataclasses import dataclass
from typing import Dict, Any

from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
    EvaluatorOutput,
    EvaluationResult,
)
from pydantic_evals.evaluators.evaluator import EvaluationScalar
from pydantic_ai_examples.evals.custom_evaluators import SpanQuery
from logging import getLogger
logger = getLogger(__name__)


@dataclass
class ToolCallHasResult(Evaluator[object, object, object]):
    agent_name: str
    tool_name: str
    results: Dict[str, Any]

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> bool:
        tool_call_span = ctx.span_tree.first(
            SpanQuery(
                name_equals='agent run',
                has_attributes={'agent_name': self.agent_name},
                stop_recursing_when=SpanQuery(name_equals='agent run'),
                some_descendant_has=SpanQuery(
                    name_equals='running tool',
                    has_attributes={'gen_ai.tool.name': self.tool_name},
                ),
            )
        )
        if tool_call_span is None: return EvaluationReason(value=False, reason=f"Tool call {self.tool_name} not called by agent {self.agent_name}")
        print(tool_call_span.attributes)
        return True