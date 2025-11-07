from dataclasses import dataclass
from typing import Dict, Any, Literal, List

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
class Parameters:
    Kp: float
    Ti: float
    K: float
    T: float
    L: float

Method = Literal["zn", "lam"]

@dataclass
class ResultEvaluator(Evaluator[object, object, object]):
    agent_name: str
    tool_call_sequence: List[str]
    results: Parameters
    method: Method

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> bool:
        i = 0
        tools_to_be_called = self.tool_call_sequence[i:]
        
        for tool_call in self.tool_call_sequence:
            tool_call_span = ctx.span_tree.first(
                SpanQuery(
                    name_equals='agent run',
                    has_attributes={'agent_name': self.agent_name},
                    stop_recursing_when=SpanQuery(name_equals='agent run'),
                    some_descendant_has=SpanQuery(name_equals='running tool', has_attributes={'gen_ai.tool.name': tool_call}),
                )
            )
        
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