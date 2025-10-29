from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, Any

from pydantic_ai_examples.evals.models import (
    TimeRangeBuilderSuccess,
    TimeRangeInputs,
    TimeRangeResponse,
)
from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluatorOutput,
)
from pydantic_evals.otel import SpanQuery


@dataclass
class AgentCalledToolWithArgument(Evaluator[object, object, object]):
    agent_name: str
    tool_name: str
    arguments: Dict[str, Any]

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> bool:
        return ctx.span_tree.any(
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
