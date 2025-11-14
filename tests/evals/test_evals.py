from control_agent.evals.schemas.definitions import experiment_definitions, ExperimentDefinitions
import pytest


@pytest.fixture
def exp_defs() -> ExperimentDefinitions:
    return experiment_definitions


def create_runner(exp_defs: ExperimentDefinitions) -> Runner:
    cases

def test_experiment_definitions(exp_defs: ExperimentDefinitions):
    for query_name in exp_defs.get_query_names():
        schema = exp_defs.get_response_schema(query_name)
        tool_use = exp_defs.get_expected_tool_use(query_name)

        print(schema)
        print("-" * 100)
        print(tool_use)
        print("-" * 100)
        break