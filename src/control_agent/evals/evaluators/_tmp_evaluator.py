"""Agent evaluation against ground truth."""

from typing import Dict, Any, Optional, List
import re
from control_agent import FOPDT, ZieglerNicholsMethod
from control_agent.lam import LambdaTuningMethod
from ._tmp_metrics import EvaluationMetrics


class AgentEvaluator:
    """Evaluator for comparing agent results with ground truth."""
    
    def __init__(self, tolerance_percent: float = 5.0):
        """Initialize evaluator.
        
        Args:
            tolerance_percent: Tolerance for pass/fail evaluation (default: 5%)
        """
        self.tolerance_percent = tolerance_percent
    
    def evaluate_result(
        self,
        query: str,
        agent_result: Dict[str, Any],
        ground_truth_method: Optional[str] = None,
        ground_truth_params: Optional[Dict[str, float]] = None,
    ) -> EvaluationMetrics:
        """Evaluate agent result against ground truth.
        
        Args:
            query: Original query string
            agent_result: Result from control_agent.agent.run() containing output, intermediate_steps
            ground_truth_method: Method for ground truth ('zn', 'lambda', or None)
            ground_truth_params: Ground truth parameters (K, T, L, lambda, etc.)
            
        Returns:
            EvaluationMetrics with comparison results
        """
        # Extract agent results
        agent_success = agent_result.get("success", True)
        output = agent_result.get("output", "")
        intermediate_steps = agent_result.get("intermediate_steps", [])
        
        # Extract tool calls
        tool_sequence = []
        tool_calls = 0
        for step in intermediate_steps:
            if len(step) >= 1:
                action = step[0]
                if hasattr(action, "tool"):
                    tool_sequence.append(action.tool)
                    tool_calls += 1
        
        # Extract values from agent output and tool results
        agent_values = self._extract_values_from_results(agent_result)
        
        # Calculate ground truth if method specified
        ground_truth_values = {}
        if ground_truth_method and ground_truth_params:
            ground_truth_values = self._calculate_ground_truth(
                ground_truth_method, ground_truth_params
            )
        
        # Determine query type
        query_type = self._classify_query(query)
        
        # Create metrics
        metrics = EvaluationMetrics(
            query=query,
            query_type=query_type,
            agent_success=agent_success,
            agent_Kp=agent_values.get("Kp"),
            agent_Ti=agent_values.get("Ti"),
            agent_K=agent_values.get("K"),
            agent_T=agent_values.get("T"),
            agent_L=agent_values.get("L"),
            ground_truth_Kp=ground_truth_values.get("Kp"),
            ground_truth_Ti=ground_truth_values.get("Ti"),
            ground_truth_K=ground_truth_values.get("K"),
            ground_truth_T=ground_truth_values.get("T"),
            ground_truth_L=ground_truth_values.get("L"),
            tool_calls=tool_calls,
            tool_sequence=tool_sequence,
            passed=False,  # Will be calculated
            tolerance_percent=self.tolerance_percent,
        )
        
        # Calculate errors and pass/fail
        metrics.calculate_errors()
        metrics.assess_pass_fail()
        
        return metrics
    
    def _extract_values_from_results(self, agent_result: Dict[str, Any]) -> Dict[str, float]:
        """Extract parameter values from agent results."""
        values = {}
        
        # Check intermediate steps for tool outputs
        intermediate_steps = agent_result.get("intermediate_steps", [])
        for step in intermediate_steps:
            if len(step) >= 2:
                tool_output = step[1]
                
                # Extract from identify_fopdt_tool output
                if isinstance(tool_output, dict):
                    if "K" in tool_output:
                        values["K"] = float(tool_output["K"])
                    if "T" in tool_output:
                        values["T"] = float(tool_output["T"])
                    if "L" in tool_output:
                        values["L"] = float(tool_output["L"])
                    
                    # Extract from set_fmu_parameters_tool output
                    if "parameters" in tool_output:
                        params = tool_output["parameters"]
                        if "Kp" in params:
                            values["Kp"] = float(params["Kp"])
                        if "Ti" in params:
                            values["Ti"] = float(params["Ti"])
        
        # Also try to extract from final output text using regex
        output_text = str(agent_result.get("output", ""))
        
        patterns = {
            "Kp": r"K[_p]?\s*[=:]\s*([\d.]+)",
            "Ti": r"T[_i]?\s*[=:]\s*([\d.]+)",
            "K": r"(?:^|\s)K\s*[=:]\s*([\d.]+)",
            "T": r"(?:^|\s)T\s*[=:]\s*([\d.]+)",
            "L": r"(?:^|\s)L\s*[=:]\s*([\d.]+)",
        }
        
        for key, pattern in patterns.items():
            if key not in values:
                match = re.search(pattern, output_text, re.IGNORECASE)
                if match:
                    try:
                        values[key] = float(match.group(1))
                    except ValueError:
                        pass
        
        return values
    
    def _calculate_ground_truth(
        self, method: str, params: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate ground truth using reference methods."""
        ground_truth = {}
        
        # Get FOPDT system parameters
        K = params.get("K", 1.0)
        T = params.get("T", 1.0)
        L = params.get("L", 0.5)
        
        system = FOPDT(K=K, T=T, L=L)
        
        if method.lower() in ["zn", "ziegler-nichols", "ziegler_nichols"]:
            # Ziegler-Nichols method
            zn = ZieglerNicholsMethod(system)
            ground_truth["Kp"] = zn.pi_controller.K_p
            ground_truth["Ti"] = zn.pi_controller.T_i
            ground_truth["K"] = K
            ground_truth["T"] = T
            ground_truth["L"] = L
            
        elif method.lower() in ["lam", "lambda", "lambda_tuning"]:
            # Lambda tuning method
            lam = params.get("lambda", params.get("lam", 2.0 * L))
            lam_method = LambdaTuningMethod(system, lam=lam)
            ground_truth["Kp"] = lam_method.pi_controller.K_p
            ground_truth["Ti"] = lam_method.pi_controller.T_i
            ground_truth["K"] = K
            ground_truth["T"] = T
            ground_truth["L"] = L
        
        return ground_truth
    
    def _classify_query(self, query: str) -> str:
        """Classify query type based on content."""
        query_lower = query.lower()
        
        if "ziegler" in query_lower or "zn" in query_lower:
            return "zn_tuning"
        elif "lambda" in query_lower or "lam" in query_lower:
            return "lambda_tuning"
        elif "simulate" in query_lower and "open" in query_lower:
            return "open_loop_simulation"
        elif "simulate" in query_lower and "closed" in query_lower:
            return "closed_loop_simulation"
        elif "identify" in query_lower or "fopdt" in query_lower:
            return "system_identification"
        elif "parameter" in query_lower:
            return "parameter_setting"
        else:
            return "general"

