"""Metrics for evaluating agent performance."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class EvaluationMetrics(BaseModel):
    """Metrics for evaluating agent performance against ground truth."""
    
    # Query info
    query: str = Field(..., description="The original query")
    query_type: str = Field(..., description="Type of query (e.g., 'zn_tuning', 'lambda_tuning', 'simulation')")
    
    # Agent results
    agent_success: bool = Field(..., description="Whether agent completed successfully")
    agent_Kp: Optional[float] = Field(None, description="Agent's calculated Kp value")
    agent_Ti: Optional[float] = Field(None, description="Agent's calculated Ti value")
    agent_K: Optional[float] = Field(None, description="Agent's identified K value")
    agent_T: Optional[float] = Field(None, description="Agent's identified T value")
    agent_L: Optional[float] = Field(None, description="Agent's identified L value")
    
    # Ground truth
    ground_truth_Kp: Optional[float] = Field(None, description="Ground truth Kp value")
    ground_truth_Ti: Optional[float] = Field(None, description="Ground truth Ti value")
    ground_truth_K: Optional[float] = Field(None, description="Ground truth K value")
    ground_truth_T: Optional[float] = Field(None, description="Ground truth T value")
    ground_truth_L: Optional[float] = Field(None, description="Ground truth L value")
    
    # Errors
    Kp_error_percent: Optional[float] = Field(None, description="Percentage error in Kp")
    Ti_error_percent: Optional[float] = Field(None, description="Percentage error in Ti")
    K_error_percent: Optional[float] = Field(None, description="Percentage error in K")
    T_error_percent: Optional[float] = Field(None, description="Percentage error in T")
    L_error_percent: Optional[float] = Field(None, description="Percentage error in L")
    
    # Tool usage
    tool_calls: int = Field(..., description="Number of tool calls made")
    tool_sequence: list = Field(default_factory=list, description="Sequence of tools called")
    
    # Overall assessment
    passed: bool = Field(..., description="Whether evaluation passed (within tolerance)")
    tolerance_percent: float = Field(5.0, description="Tolerance for pass/fail (percentage)")
    
    def calculate_errors(self) -> None:
        """Calculate percentage errors between agent and ground truth."""
        if self.agent_Kp is not None and self.ground_truth_Kp is not None:
            if abs(self.ground_truth_Kp) > 1e-10:
                self.Kp_error_percent = abs(self.agent_Kp - self.ground_truth_Kp) / abs(self.ground_truth_Kp) * 100
        
        if self.agent_Ti is not None and self.ground_truth_Ti is not None:
            if abs(self.ground_truth_Ti) > 1e-10:
                self.Ti_error_percent = abs(self.agent_Ti - self.ground_truth_Ti) / abs(self.ground_truth_Ti) * 100
        
        if self.agent_K is not None and self.ground_truth_K is not None:
            if abs(self.ground_truth_K) > 1e-10:
                self.K_error_percent = abs(self.agent_K - self.ground_truth_K) / abs(self.ground_truth_K) * 100
        
        if self.agent_T is not None and self.ground_truth_T is not None:
            if abs(self.ground_truth_T) > 1e-10:
                self.T_error_percent = abs(self.agent_T - self.ground_truth_T) / abs(self.ground_truth_T) * 100
        
        if self.agent_L is not None and self.ground_truth_L is not None:
            if abs(self.ground_truth_L) > 1e-10:
                self.L_error_percent = abs(self.agent_L - self.ground_truth_L) / abs(self.ground_truth_L) * 100
    
    def assess_pass_fail(self) -> None:
        """Assess whether evaluation passed based on tolerance."""
        errors = [
            e for e in [
                self.Kp_error_percent,
                self.Ti_error_percent,
                self.K_error_percent,
                self.T_error_percent,
                self.L_error_percent,
            ]
            if e is not None
        ]
        
        if not errors:
            # No ground truth to compare against
            self.passed = self.agent_success
        else:
            # All errors must be within tolerance
            self.passed = self.agent_success and all(e <= self.tolerance_percent for e in errors)
    
    def to_summary(self) -> Dict[str, Any]:
        """Generate human-readable summary."""
        summary = {
            "query": self.query,
            "status": "PASSED" if self.passed else "FAILED",
            "agent_success": self.agent_success,
        }
        
        if self.agent_Kp is not None:
            summary["Kp"] = {
                "agent": self.agent_Kp,
                "ground_truth": self.ground_truth_Kp,
                "error_%": self.Kp_error_percent,
            }
        
        if self.agent_Ti is not None:
            summary["Ti"] = {
                "agent": self.agent_Ti,
                "ground_truth": self.ground_truth_Ti,
                "error_%": self.Ti_error_percent,
            }
        
        if self.agent_K is not None:
            summary["K"] = {
                "agent": self.agent_K,
                "ground_truth": self.ground_truth_K,
                "error_%": self.K_error_percent,
            }
        
        summary["tool_calls"] = self.tool_calls
        summary["tool_sequence"] = self.tool_sequence
        
        return summary

