from control_agent.evals.experiments.list_models.dataset import dataset
from control_agent.evals.experiments.list_models.agent import agent
from control_agent.evals.report import render_report
if __name__ == "__main__":
    async def agent_runner(experiment_input): # type: ignore
        result = await agent.run(experiment_input)
        return result.output
    
    report = dataset.evaluate_sync(agent_runner)
    render_report(report, 'list_models')