from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, Any, Mapping

from pydantic_ai_examples.evals.models import (
    TimeRangeBuilderSuccess,
    TimeRangeInputs,
    TimeRangeResponse,
)
from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    EvaluationReason,
    EvaluatorOutput,
    EvaluationResult,
)
from pydantic_evals.evaluators.evaluator import EvaluationScalar

from logging import getLogger
logger = getLogger(__name__)

@dataclass
class Yaysayer(Evaluator[object, object, object]):
    foo: str
    bar: int
    baz: float
    zip: bool
    

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> EvaluationResult:
        # Access case data
        ctx.name              # Case name
        ctx.inputs            # Task inputs
        ctx.metadata          # Case metadata
        ctx.expected_output   # Expected output (may be None)
        ctx.output            # Actual output

        # Performance data
        ctx.duration          # Task execution time (seconds)

        # Custom metrics/attributes (see metrics guide)
        ctx.metrics           # dict[str, int | float]
        ctx.attributes        # dict[str, Any]

        # OpenTelemetry spans (if logfire configured)
        ctx.span_tree         # SpanTree for behavioral checks

        ###
        logger.info(self.foo)
        logger.info(self.bar)
        logger.info(self.baz)
        logger.info(self.zip)
        return EvaluationReason(value=True, reason="You are a yaysayer")
        """
        return Mapping[str, EvaluationScalar|EvaluationReason]({
            "foo": 0.4,
            "bar": True,
            "baz": EvaluationReason(value=False, reason="You need to score at least 0.5"),
            "zip": "yuppp",
        })"""
