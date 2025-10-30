"""Python API interface for the FMI Agent."""

from typing import Dict, Any, List, Optional
from agent.core import create_agent
import logfire

class FMIAgent:
    """High-level Python API for FMI Agent."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        verbose: bool = False,
        max_iterations: int = 20,
    ):
        """Initialize FMI Agent.

        Args:
            model_name: Azure OpenAI deployment name (default from env)
            temperature: LLM temperature (default: 0.0)
            verbose: Enable verbose logging (default: False)
            max_iterations: Maximum agent iterations (default: 20)
        """
        self.agent_executor = create_agent(
            model_name=model_name,
            temperature=temperature,
            verbose=verbose,
            max_iterations=max_iterations,
        )
        self.max_iterations = max_iterations
        self.verbose = verbose

        self.logger = logfire.get_logger("agent-fmi")
        self.logger.info("Initializing Agent")


    def run(
        self,
        query: str,
        #callbacks: Optional[List[BaseCallbackHandler]] = None,
    ) -> Dict[str, Any]:
        """Run agent on a query.

        Args:
            query: Natural language query for the agent
            callbacks: List of callbacks to use

        Returns:
            Dictionary containing:
                - output: Agent's final response
                - intermediate_steps: List of (action, observation) tuples
                - success: Whether execution succeeded
                - trace: chronological agent/LLM/tool events
                - prompts: prompts sent to the LLM
                - first_llm_msg: first LLM output before tools
        """
        self.logger.info(f"Agent received query: {query}", query=query)

        try:
            #trace_collector = TraceCollector()
            # Run agent using LangChain 1.0 API
            result = self.agent_executor.invoke(
                {"messages": [{"role": "user", "content": query}]},
                config={
                    "recursion_limit": self.max_iterations if hasattr(self, "max_iterations") else 50,
                    #"callbacks": [trace_collector] + (callbacks or []),
                },
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
                        except Exception:
                            tool_call_map[tool_call_id] = content

            # Second pass: match tool calls with responses
            for msg in messages:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_call_id = tool_call.get("id", "")
                        action = type(
                            "Action",
                            (),
                            {
                                "tool": tool_call.get("name", ""),
                                "tool_input": tool_call.get("args", {}),
                            },
                        )()
                        observation = tool_call_map.get(tool_call_id, {})
                        intermediate_steps.append((action, observation))

            agent_result = {
                "output": output,
                "intermediate_steps": intermediate_steps,
                "success": True,
                # "trace": trace_collector.events,
                # "prompts": trace_collector.prompts,
                # "first_llm_msg": trace_collector.first_llm_msg,
            }

            # logfire logging
            self.logger.success(f"Agent run successful: {output[:200]}", result_summary=output[:200])

            return agent_result

        except Exception as e:
            self.logger.exception(f"Agent run failed with error: {str(e)}", error=str(e))
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
            queries: List of dicts, each containing:
                - query: str

        Returns:
            List of result dictionaries
        """
        results = []
        for i, query_dict in enumerate(queries):
            if self.verbose:
                print(f"\n{'='*60}")
                print(f"Query {i+1}/{len(queries)}: {query_dict['query']}")
                print(f"{'='*60}\n")

            result = self.run(query=query_dict["query"])
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

        return report