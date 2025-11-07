from evals.experiments.demo.dataset import dataset
from evals.experiments.demo.agent import agent
from evals.report import render_report

async def answer_question(question: str) -> str:
    result = await agent.run(question)
    return result.output

def run_demo() -> None:
    report = dataset.evaluate_sync(answer_question)
    render_report(report, 'demo')
    print(report)

if __name__ == "__main__":
    # Run the evaluation demo
    run_demo()
    