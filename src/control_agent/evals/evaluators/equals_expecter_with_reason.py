from pydantic_evals.evaluators import EqualsExpected
from pydantic_evals.evaluators.common import EvaluationReason
from pydantic_evals.evaluators import EvaluatorContext

class EqualsExpectedWithReason(EqualsExpected):
    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> EvaluationReason:
        print(ctx.output)
        print(ctx.expected_output)
        return EvaluationReason(
            value=ctx.output == ctx.expected_output,
            reason=f"Expected {ctx.expected_output} but got {ctx.output}")