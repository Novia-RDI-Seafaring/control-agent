from control_agent.evals.experiments.demo.dataset import dataset
from control_agent.evals.experiments.demo.agent import agent
from control_agent.evals.report import render_report

from control_agent.evals.experiments.demo.agent import answer_question

def run_demo() -> None:
    report = dataset.evaluate_sync(answer_question)
    render_report(report, 'demo')
    print(report)

if __name__ == "__main__":
    # Run the evaluation demo
    run_demo()
    