"""Export evaluation results to CSV and pickle for analysis"""
import pandas as pd
import pickle
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic_evals.reporting import EvaluationReport, ReportCase
from control_agent.agent.core.types import AgentRunResult, ToolCallPart
from control_agent.agent.core.model import get_default_model
from control_agent.evals.schemas.responses import CaseResponse
import os


def get_model_name() -> str:
    """Get the current model name from environment or model object"""
    model_name = os.getenv("DEFAULT_MODEL", "unknown")
    provider = os.getenv("DEFAULT_PROVIDER", os.getenv("AZURE_OPENAI_ENDPOINT", "unknown"))
    if provider == "azure":
        return f"azure:{model_name}"
    return model_name


def extract_tool_calls(result: Optional[AgentRunResult[Any]]) -> List[str]:
    """Extract list of executed tool names from AgentRunResult"""
    if result is None:
        return []
    tool_calls = []
    try:
        for message in result.all_messages():
            for part in message.parts:
                if isinstance(part, ToolCallPart) and part.tool_name != "final_result":
                    tool_calls.append(part.tool_name)
    except Exception:
        pass
    return tool_calls


def extract_agent_response(result: Optional[AgentRunResult[Any]]) -> tuple[str, Optional[Any], Optional[str]]:
    """
    Extract the agent's final response message and structured output.
    
    Returns:
        tuple: (message: str, structured_output: Any, structured_output_json: str)
    """
    if result is None:
        return "", None, None
    
    try:
        if hasattr(result, 'output'):
            output = result.output
            
            # Check if it's a CaseResponse
            if isinstance(output, CaseResponse):
                message = output.message
                structured_output = output.output
                # Serialize structured output to JSON for CSV
                try:
                    if hasattr(structured_output, 'model_dump_json'):
                        # Pydantic v2 - use model_dump_json for direct JSON serialization
                        structured_output_json = structured_output.model_dump_json(indent=2)
                    elif hasattr(structured_output, 'model_dump'):
                        # Pydantic v2 fallback
                        structured_output_json = json.dumps(structured_output.model_dump(), indent=2)
                    elif hasattr(structured_output, 'dict'):
                        # Pydantic v1
                        structured_output_json = json.dumps(structured_output.dict(), indent=2)
                    else:
                        # Fallback: try to convert to dict
                        structured_output_json = json.dumps(structured_output, indent=2, default=str)
                except Exception as e:
                    structured_output_json = json.dumps({"error": f"Failed to serialize: {str(e)}"}, indent=2)
                
                return message, structured_output, structured_output_json
            
            # Check nested CaseResponse
            if hasattr(output, 'output') and isinstance(output.output, CaseResponse):
                case_response = output.output
                message = case_response.message
                structured_output = case_response.output
                try:
                    if hasattr(structured_output, 'model_dump_json'):
                        # Pydantic v2 - use model_dump_json for direct JSON serialization
                        structured_output_json = structured_output.model_dump_json(indent=2)
                    elif hasattr(structured_output, 'model_dump'):
                        structured_output_json = json.dumps(structured_output.model_dump(), indent=2)
                    elif hasattr(structured_output, 'dict'):
                        structured_output_json = json.dumps(structured_output.dict(), indent=2)
                    else:
                        structured_output_json = json.dumps(structured_output, indent=2, default=str)
                except Exception as e:
                    structured_output_json = json.dumps({"error": f"Failed to serialize: {str(e)}"}, indent=2)
                
                return message, structured_output, structured_output_json
            
            # Fallback: try to get message
            if hasattr(output, 'message'):
                return str(output.message), None, None
        
        # Fallback: get the last text part
        for message in reversed(list(result.all_messages())):
            for part in reversed(message.parts):
                if hasattr(part, 'content') and part.content:
                    return str(part.content), None, None
        
        return str(result.output) if hasattr(result, 'output') else "", None, None
    except Exception as e:
        return str(result.output) if hasattr(result, 'output') else "", None, None


def export_results_to_csv(
    report: EvaluationReport,
    experiment_name: str,
    results_keeper: Dict[str, AgentRunResult[Any]],
    output_path: Optional[Path] = None
) -> tuple[Path, Path]:
    """
    Export evaluation results to CSV and pickle files.
    
    Args:
        report: EvaluationReport from pydantic-evals
        experiment_name: Name of the experiment
        results_keeper: Dictionary mapping query to AgentRunResult
        output_path: Optional base path. Defaults to data/results/{experiment_name}
    
    Returns:
        Tuple of (CSV path, pickle path) to the saved files
    """
    rows = []
    model_name = get_model_name()
    
    for case in report.cases:
        query = case.inputs
        result = results_keeper.get(query)
        
        # Extract tool calls
        executed_tools = extract_tool_calls(result) if result else []
        tools_str = ", ".join(executed_tools) if executed_tools else ""
        
        # Extract agent response (only the message, not the structured output)
        if result:
            agent_response, _, _ = extract_agent_response(result)
        else:
            agent_response = ""
        
        # Extract metrics
        input_tokens = case.metrics.get("input_tokens", 0)
        output_tokens = case.metrics.get("output_tokens", 0)
        reasoning_tokens = case.metrics.get("reasoning_tokens", 0)
        cache_read_tokens = case.metrics.get("cache_read_tokens", 0)
        requests = case.metrics.get("requests", 0)
        task_duration = case.task_duration
        total_duration = case.total_duration
        
        # Extract evaluations
        evaluator_names = []
        evaluator_results = []
        evaluator_reasons = []
        
        for eval_name, assertion in case.assertions.items():
            evaluator_names.append(eval_name)
            evaluator_results.append(assertion.value)
            evaluator_reasons.append(assertion.reason)
        
        # Create row with all data
        row = {
            "llm_model": model_name,
            "experiment_name": experiment_name,
            "case_name": case.name,
            "query": query,
            "executed_tools": tools_str,
            "tool_count": len(executed_tools),
            "agent_response": agent_response,  # Only the message text, not the structured schema
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "cache_read_tokens": cache_read_tokens,
            "total_tokens": input_tokens + output_tokens + reasoning_tokens,
            "requests": requests,
            "task_duration_seconds": task_duration,
            "total_duration_seconds": total_duration,
        }
        
        # Add evaluator columns (one per evaluator)
        for i, (eval_name, eval_result, eval_reason) in enumerate(zip(evaluator_names, evaluator_results, evaluator_reasons)):
            row[f"evaluator_{i+1}_name"] = eval_name
            row[f"evaluator_{i+1}_passed"] = eval_result
            row[f"evaluator_{i+1}_reason"] = eval_reason
        
        # Add all evaluators summary
        row["all_evaluators_passed"] = all(evaluator_results)
        row["evaluator_count"] = len(evaluator_names)
        row["evaluator_names"] = ", ".join(evaluator_names)
        
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Determine output directory
    if output_path is None:
        output_dir = Path("data/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = output_dir / f"{experiment_name}.csv"
        pickle_path = output_dir / f"{experiment_name}.pkl"
    else:
        # If output_path is provided, use it as base for both files
        csv_path = output_path.with_suffix('.csv')
        pickle_path = output_path.with_suffix('.pkl')
        csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(csv_path, index=False)
    
    # Save to pickle for easy loading in Python
    df.to_pickle(pickle_path)
    
    return csv_path, pickle_path


def combine_all_experiments(results_dir: Path = Path("data/results")) -> tuple[Path, Path]:
    """
    Combine all individual experiment CSV/pickle files into one combined DataFrame.
    
    Args:
        results_dir: Directory containing individual experiment files
    
    Returns:
        Tuple of (combined CSV path, combined pickle path)
    """
    import glob
    
    # Find all pickle files (they preserve data types better than CSV)
    pickle_files = list(results_dir.glob("*.pkl"))
    
    # Exclude the combined file itself if it exists
    pickle_files = [f for f in pickle_files if f.name != "all_experiments.pkl"]
    
    if not pickle_files:
        print(f"No experiment files found in {results_dir}")
        return None, None
    
    # Load all DataFrames
    dfs = []
    for pkl_file in pickle_files:
        try:
            df = pd.read_pickle(pkl_file)
            dfs.append(df)
        except Exception as e:
            print(f"Warning: Could not load {pkl_file}: {e}")
    
    if not dfs:
        print("No valid DataFrames found to combine")
        return None, None
    
    # Combine all DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Save combined files
    csv_path = results_dir / "all_experiments.csv"
    pickle_path = results_dir / "all_experiments.pkl"
    
    combined_df.to_csv(csv_path, index=False)
    combined_df.to_pickle(pickle_path)
    
    print(f"Combined {len(dfs)} experiments into {csv_path} and {pickle_path}")
    print(f"Total rows: {len(combined_df)}")
    
    return csv_path, pickle_path

