from control_agent.evals.common import * # type: ignore

class ListModelNamesResponse(BaseModel):
    model_names: List[str]

OutputDataT = ListModelNamesResponse

dataset = Dataset[str, ListModelNamesResponse, Any](
    name='list_model_names',
    cases=[
        Case(
            name='get_fmu_names',
            inputs="Please list all the FMU models in the system",
            expected_output=ListModelNamesResponse(model_names=["PI_FOPDT_2"]),
            evaluators=[ EqualsExpected()],
        ),
    ],
)


if __name__ == "__main__":
    from control_toolbox.tools.information import get_fmu_names
    from control_toolbox.config import set_fmu_dir
    from pathlib import Path
    set_fmu_dir(Path( "models/fmus"))
    
    report = dataset.evaluate_sync(get_agent_runner(OutputDataT))
    print(report)