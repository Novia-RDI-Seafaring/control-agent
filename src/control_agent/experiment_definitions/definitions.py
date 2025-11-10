from pydantic import BaseModel, Field
from typing import List, Any, Dict, Optional, Callable

from control_agent.experiment_definitions.response_schema import (
    get_json_schema,
    ListModelNamesResponse,
    ListIOPResponse,
    GetMetadataResponse,
    StepResponse,
    SystemIdentificationResponse,
    LambdaTuningResponse,
    UltimateGainResponse,
    ZNResponse,
    TuningOvershootResponse
)

class ToolUse(BaseModel):
    name: str
    max_runs: Optional[int] = Field(default=1, description="Maximum allowed runs for this tool")

def define_tool_use(required: List[ToolUse], optional: List[ToolUse]) -> dict:
    return {"required": required, "optional": optional}

class ExperimentDefinitions:
    """
    Dynamic registry for experiment queries tied to a specific model.
    Use add_query(...) to register new queries with their schema and tool plans.
    """
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.queries: Dict[str, str] = {}
        self.response_schema: Dict[str, Any] = {}
        self.expected_tool_use: Dict[str, Dict[str, Any]] = {}

    # --- internals ---
    def _render(self, text: str) -> str:
        return text.replace("{MODEL_NAME}", self.model_name)

    def _ensure_exists(self, query_name: str) -> None:
        if query_name not in self.queries:
            raise KeyError(f"Unknown query '{query_name}'. Available: {list(self.queries.keys())}")

    # --- public API ---
    def register_query(
        self,
        query_name: str,
        query: str,
        response_schema: Any,
        expected_tool_use: Dict[str, Any],
    ) -> None:
        """
        Register a query with its schema and tool plan.
        - query: a template string
        - response_schema: any JSON-serializable schema object (dict, str, etc.)
        - expected_tool_use: dict like {"required":[...], "optional":[...]}
        """
        self.queries[query_name] = query
        self.response_schema[query_name] = response_schema
        self.expected_tool_use[query_name] = expected_tool_use

    def construct_query(self, query_name: str) -> str:
        """
        Produce a printable block with the rendered query and its response schema.
        """
        self._ensure_exists(query_name)
        rendered = self._render(self.queries[query_name])
        return f"""
        MODEL: {self.model_name}\n
        QUERY: {rendered}
        """

    def get_query(self, query_name: str) -> str:
        self._ensure_exists(query_name)
        return self._render(self.queries[query_name])

    def get_response_schema(self, query_name: str) -> Any:
        self._ensure_exists(query_name)
        return self.response_schema[query_name]

    def get_expected_tool_use(self, query_name: str) -> Dict[str, Any]:
        self._ensure_exists(query_name)
        return self.expected_tool_use[query_name]

    def list_queries(self) -> Dict[str, str]:
        """Return all query names with rendered text."""
        return {k: self._render(v) for k, v in self.queries.items()}

    def get_query_names(self) -> List[str]:
        return list(self.queries.keys())

    def get_queries(self) -> str:
        return {k: self._render(v) for k, v in self.queries.items()}

########################################################
# REGISTER QUERIES
########################################################
experiment_definitions = ExperimentDefinitions(model_name="PI_FOPDT_2")
experiment_definitions.model_name = "PI_FOPDT_2"

#1) list_model_names
experiment_definitions.register_query(
    query_name="list_model_names",
    query="List available FMU models.",
    response_schema=ListModelNamesResponse,
    expected_tool_use=define_tool_use(
        required=[ToolUse(name="get_fmu_names", max_runs=1)],
        optional=[]
    )
)

#2) list_iop
experiment_definitions.register_query(
    query_name="list_iop",
    query="List the inputs, outputs, and parameters of the model.",
    response_schema=ListIOPResponse,
    expected_tool_use=define_tool_use(
        required=[ToolUse(name="get_model_description", max_runs=1)],
        optional=[ToolUse(name="get_fmu_names")]
    )
)

#3) get_metadata
experiment_definitions.register_query(
    query_name="get_metadata",
    query="Get the metadata of the model.",
    response_schema=GetMetadataResponse,
    expected_tool_use=define_tool_use(
        required=[ToolUse(name="get_model_description", max_runs=1)],
        optional=[ToolUse(name="get_fmu_names")]
    )
)

#4) open_loop_step
experiment_definitions.register_query(
    query_name="open_loop_step",
    query="Simulate an open-loop step response with input change from 0 to 1. Use output_interval 0.5 second and maximum simulation time 30 seconds.",
    response_schema=StepResponse,
    expected_tool_use=define_tool_use(
        required=[ToolUse(name="simulate_step_response", max_runs=1)],
        optional=[ToolUse(name="get_fmu_names"), ToolUse(name="get_model_description")]
    )
)

#5) closed_loop_step
experiment_definitions.register_query(
    query_name="closed_loop_step",
    query="Simulate a closed-loop step response with input change from 0 to 1. Use output_interval 0.5 second and maximum simulation time 30 seconds.",
    response_schema=StepResponse,
    expected_tool_use=define_tool_use(
        required=[ToolUse(name="simulate_step_response", max_runs=1)],
        optional=[ToolUse(name="get_fmu_names"), ToolUse(name="get_model_description")]
    )
)

#6) system_identification
experiment_definitions.register_query(
    query_name="system_identification",
    query="Simulate an open-loop step response and identify the static gain (K), time constant (T), and dead time (L). Use output_interval 1 second and maximum simulation time 30 seconds.",
    response_schema=SystemIdentificationResponse,
    expected_tool_use=define_tool_use(
        required=[
            ToolUse(name="simulate_step_response", max_runs=1),
            ToolUse(name="identify_fopdt_from_step", max_runs=1)
        ],
        optional=[ToolUse(name="get_fmu_names"), ToolUse(name="get_model_description")]
    )
)

#7) ultimate_gain
experiment_definitions.register_query(
    query_name="ultimate_gain",
    query="Perform closed-loop experimentes to determine the ultimate gain (Ku) and ultimate period (Pu). Use output_interval 0.1 second and maximum simulation time 10 seconds.",
    response_schema=UltimateGainResponse,
    expected_tool_use=define_tool_use(
        required=[
            ToolUse(name="simulate_step_response", max_runs=10),
            ToolUse(name="find_peaks", max_runs=1)
        ],
        optional=[ToolUse(name="get_fmu_names"), ToolUse(name="get_model_description")]
    )
)

#8) lambda_tuning
experiment_definitions.register_query(
    query_name="lambda_tuning",
    query="Tune the PI controller using λ-tuning for a balanced response.",
    response_schema=LambdaTuningResponse,
    expected_tool_use=define_tool_use(
        required=[
            ToolUse(name="simulate_step_response", max_runs=1),
            ToolUse(name="identify_fopdt_from_step", max_runs=1),
            ToolUse(name="pid_lambda_tuning", max_runs=1)
        ],
        optional=[ToolUse(name="get_fmu_names"), ToolUse(name="get_model_description")]
    )
)

#9) z_n
experiment_definitions.register_query(
    query_name="z_n",
    query="Tune the PI controller using Ziegler-Nichols closed-loop method.",
    response_schema=ZNResponse,
    expected_tool_use=define_tool_use(
        required=[
            ToolUse(name="simulate_step_response", max_runs=10),
            ToolUse(name="find_peaks", max_runs=1),
            ToolUse(name="zn_pid_tuning", max_runs=1)
        ],
        optional=[ToolUse(name="get_fmu_names"), ToolUse(name="get_model_description")]
    )
)

#10) tuning_overshoot
experiment_definitions.register_query(
    query_name="tuning_overshoot",
    query="Tune the PI controller to have approximately 10 percentage overshoot and rise time less than 2 seconds.",
    response_schema=TuningOvershootResponse,
    expected_tool_use=define_tool_use(
        required=[
            ToolUse(name="simulate_step_response", max_runs=10),
            ToolUse(name="find_overshoot", max_runs=1),
            ToolUse(name="find_rise_time", max_runs=1)
        ],
        optional=[ToolUse(name="get_fmu_names"), ToolUse(name="get_model_description")]
    )
)

#11) get model description
from control_toolbox.tools.information import ModelDescription
experiment_definitions.register_query(
    query_name="model_description",
    query="Get the model description.",
    response_schema=ModelDescription,
    expected_tool_use=define_tool_use(
        required=[
            ToolUse(name="get_model_description"),
        ],
        optional=[ToolUse(name="get_fmu_names")]
    )
)