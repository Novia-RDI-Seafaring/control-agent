from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ZnEvaluator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
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
        return self.is_withing_range(float(ctx.output), float(ctx.expected_output), 0.01)


        return True
    
    def is_withing_range(self, value: float, expected: float, tolerance: float = 0.01) -> bool:
        return abs(value - expected) / expected <= tolerance