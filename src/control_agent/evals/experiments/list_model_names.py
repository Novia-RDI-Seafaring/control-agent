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