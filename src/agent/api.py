"""Python API interface for the FMI Agent."""

from typing import Dict, Any, List, Optional
from agent.core import create_agent
from agent.evaluation import AgentEvaluator
from langchain_core.callbacks.base import BaseCallbackHandler

class TraceCollector(BaseCallbackHandler):
    def __init__(self):
        self.events = []          # chronological trace
        self.prompts = []         # LLM prompts (no secrets)
        self.first_llm_msg = None # first LLM output before tools

    # LLM -> capture prompts and first output
    def on_llm_start(self, serialized, prompts, **kwargs):
        self.prompts.extend(prompts)
        self.events.append({"type": "llm_start", "prompts_count": len(prompts)})

    def on_llm_end(self, response, **kwargs):
        try:
            gen = response.generations[0][0]
            # .message for chat, .text for text models
            msg = getattr(gen, "message", None)
            text = getattr(msg, "content", None) if msg else getattr(gen, "text", None)
            self.first_llm_msg = text
            self.events.append({"type": "llm_end", "preview": (text or "")[:200]})
        except Exception:
            self.events.append({"type": "llm_end", "preview": None})

    # Agent -> planned tool action (before the tool runs)
    def on_agent_action(self, action, **kwargs):
        self.events.append({"type": "agent_action", "tool": action.tool, "tool_input": action.tool_input})

    # Tool -> execution start/end
    def on_tool_start(self, serialized, input_str, **kwargs):
        name = (serialized.get("name") if isinstance(serialized, dict) else None) or "tool"
        self.events.append({"type": "tool_start", "tool": name, "input": input_str})

    def on_tool_end(self, output, **kwargs):
        # keep short to avoid huge payloads
        preview = output if isinstance(output, str) else str(output)
        self.events.append({"type": "tool_end", "output": preview[:300]})


class FMIAgent:
    """High-level Python API for FMI Agent."""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        verbose: bool = False,
        max_iterations: int = 20,
        evaluate: bool = False,
        tolerance_percent: float = 5.0,
    ):
        """Initialize FMI Agent.
        
        Args:
            model_name: Azure OpenAI deployment name (default from env)
            temperature: LLM temperature (default: 0.0)
            verbose: Enable verbose logging (default: False)
            max_iterations: Maximum agent iterations (default: 20)
            evaluate: Enable evaluation mode (default: False)
            tolerance_percent: Tolerance for evaluation (default: 5%)
        """
        self.agent_executor = create_agent(
            model_name=model_name,
            temperature=temperature,
            verbose=verbose,
            max_iterations=max_iterations,
        )
        self.max_iterations = max_iterations            # <— save it
        self.evaluate = evaluate
        self.evaluator = AgentEvaluator(tolerance_percent=tolerance_percent) if evaluate else None
        self.verbose = verbose
    
    def run(
        self,
        query: str,
        ground_truth_method: Optional[str] = None,
        ground_truth_params: Optional[Dict[str, float]] = None,
        callbacks: Optional[List] = None,
    ) -> Dict[str, Any]:
        """Run agent on a query.
        
        Args:
            query: Natural language query for the agent
            ground_truth_method: Method for evaluation ('zn', 'lambda', or None)
            ground_truth_params: Parameters for ground truth calculation (K, T, L, lambda)
            callbacks: List of callbacks to use
        Returns:
            Dictionary containing:
                - output: Agent's final response
                - intermediate_steps: List of (action, observation) tuples
                - success: Whether execution succeeded
                - evaluation: EvaluationMetrics (if evaluate=True)
        """
        try:
            trace_collector = TraceCollector()
            # Run agent using LangChain 1.0 API
            result = self.agent_executor.invoke(
                {"messages": [{"role": "user", "content": query}]},
                #{"recursion_limit": self.max_iterations}  # Increase from default 25 instead of 50 or manual figuring out the limit
                config={"recursion_limit":  self.max_iterations if hasattr(self, "max_iterations") else 50, "callbacks": [trace_collector] + (callbacks or [])}
            )
            
            # Extract messages from result
            messages = result.get("messages", [])
            
            # Get final response (last AI message)
            output = ""
            for msg in reversed(messages):
                if hasattr(msg, "content") and msg.content:
                    output = msg.content
                    break
            
            # Extract tool calls and their responses from messages
            intermediate_steps = []
            tool_call_map = {}  # Map tool_call_id to response
            
            # First pass: collect tool responses
            for msg in messages:
                if hasattr(msg, "type") and msg.type == "tool":
                    tool_call_id = getattr(msg, "tool_call_id", None)
                    content = getattr(msg, "content", "")
                    if tool_call_id:
                        # Parse JSON content if it's a string
                        try:
                            import json
                            tool_call_map[tool_call_id] = json.loads(content) if isinstance(content, str) else content
                        except:
                            tool_call_map[tool_call_id] = content
            
            # Second pass: match tool calls with responses
            for msg in messages:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_call_id = tool_call.get("id", "")
                        action = type('Action', (), {
                            'tool': tool_call.get("name", ""),
                            'tool_input': tool_call.get("args", {})
                        })()
                        observation = tool_call_map.get(tool_call_id, {})
                        intermediate_steps.append((action, observation))
            
            agent_result = {
                "output": output,
                "intermediate_steps": intermediate_steps,
                "success": True,
                "trace": trace_collector.events,
                "prompts": trace_collector.prompts,
                "first_llm_msg": trace_collector.first_llm_msg,
            }
            
            # Evaluate if requested
            if self.evaluate and self.evaluator:
                metrics = self.evaluator.evaluate_result(
                    query=query,
                    agent_result=agent_result,
                    ground_truth_method=ground_truth_method,
                    ground_truth_params=ground_truth_params,
                )
                agent_result["evaluation"] = metrics
                
                if self.verbose:
                    print("\n" + "="*60)
                    print("EVALUATION RESULTS")
                    print("="*60)
                    summary = metrics.to_summary()
                    for key, value in summary.items():
                        print(f"{key}: {value}")
                    print("="*60 + "\n")
            
            return agent_result
            
        except Exception as e:
            return {
                "output": f"Error: {str(e)}",
                "intermediate_steps": [],
                "success": False,
                "error": str(e),
            }
    
    def run_batch(
        self,
        queries: list[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        """Run agent on multiple queries.
        
        Args:
            queries: List of query dictionaries, each containing:
                - query: str
                - ground_truth_method: Optional[str]
                - ground_truth_params: Optional[Dict[str, float]]
        
        Returns:
            List of result dictionaries
        """
        results = []
        for i, query_dict in enumerate(queries):
            if self.verbose:
                print(f"\n{'='*60}")
                print(f"Query {i+1}/{len(queries)}: {query_dict['query']}")
                print(f"{'='*60}\n")
            
            result = self.run(
                query=query_dict["query"],
                ground_truth_method=query_dict.get("ground_truth_method"),
                ground_truth_params=query_dict.get("ground_truth_params"),
            )
            results.append(result)
        
        return results
    
    def get_summary_report(self, results: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary report from batch results.
        
        Args:
            results: List of result dictionaries from run_batch
            
        Returns:
            Summary statistics
        """
        total = len(results)
        successful = sum(1 for r in results if r.get("success", False))
        
        report = {
            "total_queries": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
        }
        
        if self.evaluate:
            evaluated = [r for r in results if "evaluation" in r]
            passed = sum(1 for r in evaluated if r["evaluation"].passed)
            
            report["evaluated"] = len(evaluated)
            report["passed"] = passed
            report["pass_rate"] = (passed / len(evaluated) * 100) if evaluated else 0
            
            # Calculate average errors
            kp_errors = [r["evaluation"].Kp_error_percent for r in evaluated if r["evaluation"].Kp_error_percent is not None]
            ti_errors = [r["evaluation"].Ti_error_percent for r in evaluated if r["evaluation"].Ti_error_percent is not None]
            
            if kp_errors:
                report["avg_Kp_error_%"] = sum(kp_errors) / len(kp_errors)
            if ti_errors:
                report["avg_Ti_error_%"] = sum(ti_errors) / len(ti_errors)
        
        return report

