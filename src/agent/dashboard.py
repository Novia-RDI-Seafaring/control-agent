"""FastHTML dashboard for FMI Agent visualization."""

import json
from typing import Optional
from fasthtml.common import *
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from agent.api import FMIAgent
from agent.utils import create_plot

# Initialize FastHTML app
app, rt = fast_app(
    hdrs=(
        # Script(src="https://cdn.plot.ly/plotly-latest.min.js"),
        Script(src="https://cdn.plot.ly/plotly-3.1.2.min.js"),
    )
)

# Global agent instance
agent = None


def init_agent():
    """Initialize agent on first request."""
    global agent
    if agent is None or getattr(agent, "max_iterations", None) != 60:
        agent = FMIAgent(verbose=False, evaluate=True, max_iterations=60)
    return agent

def create_tool_sequence_html(intermediate_steps) -> str:
    """Create HTML for tool sequence."""
    if not intermediate_steps:
        return "<p>No tool calls</p>"
    
    html = "<ol>"
    for i, step in enumerate(intermediate_steps, 1):
        if len(step) >= 2:
            action = step[0]
            tool_name = getattr(action, "tool", "unknown")
            tool_input = getattr(action, "tool_input", {})
            html += f"<li><strong>{tool_name}</strong>"
            if tool_input:
                html += f"<pre style='margin-top: 5px; font-size: 0.85em;'>{json.dumps(tool_input, indent=2)}</pre>"
            html += "</li>"
    html += "</ol>"
    return html


def create_evaluation_html(evaluation) -> str:
    """Create HTML for evaluation results."""
    if not evaluation:
        return "<p>No evaluation data</p>"
    
    status_color = "green" if evaluation.passed else "red"
    status_text = "PASSED ✓" if evaluation.passed else "FAILED ✗"
    
    html = f"<h3 style='color: {status_color};'>{status_text}</h3>"
    html += "<table style='width: 100%; border-collapse: collapse;'>"
    html += "<tr style='background-color: #f0f0f0;'><th>Parameter</th><th>Agent</th><th>Ground Truth</th><th>Error %</th></tr>"
    
    params = [
        ("Kp", evaluation.agent_Kp, evaluation.ground_truth_Kp, evaluation.Kp_error_percent),
        ("Ti", evaluation.agent_Ti, evaluation.ground_truth_Ti, evaluation.Ti_error_percent),
        ("K", evaluation.agent_K, evaluation.ground_truth_K, evaluation.K_error_percent),
        ("T", evaluation.agent_T, evaluation.ground_truth_T, evaluation.T_error_percent),
        ("L", evaluation.agent_L, evaluation.ground_truth_L, evaluation.L_error_percent),
    ]
    
    for name, agent_val, gt_val, error in params:
        if agent_val is not None:
            agent_str = f"{agent_val:.4f}"
            gt_str = f"{gt_val:.4f}" if gt_val is not None else "N/A"
            error_str = f"{error:.2f}%" if error is not None else "N/A"
            html += f"<tr><td><strong>{name}</strong></td><td>{agent_str}</td><td>{gt_str}</td><td>{error_str}</td></tr>"
    
    html += "</table>"
    html += f"<p><strong>Tool Calls:</strong> {evaluation.tool_calls}</p>"
    
    return html

def create_trace_html(trace) -> str:
    if not trace:
        return "<p>No trace</p>"
    rows = []
    for ev in trace:
        kind = ev.get("type")
        if kind == "agent_action":
            rows.append(f"<li><b>Plan</b>: call <code>{ev.get('tool')}</code> with <pre>{json.dumps(ev.get('tool_input'), indent=2)}</pre></li>")
        elif kind == "tool_start":
            rows.append(f"<li><b>Tool start</b>: <code>{ev.get('tool')}</code></li>")
        elif kind == "tool_end":
            rows.append(f"<li><b>Tool end</b>: <pre>{ev.get('output')}</pre></li>")
        elif kind == "llm_start":
            rows.append(f"<li><b>LLM prompt batch</b>: {ev.get('prompts_count')}</li>")
        elif kind == "llm_end":
            rows.append(f"<li><b>LLM output (preview)</b>: <pre>{ev.get('preview') or ''}</pre></li>")
        else:
            rows.append(f"<li><b>{kind}</b></li>")
    return "<ol>" + "".join(rows) + "</ol>"


@rt("/")
def get():
    """Main dashboard page."""
    return Titled(
        "FMI Agent Dashboard",
        Card(
            H2("PI Controller Tuning Agent"),
            P("Enter a query to run the agent and visualize results."),
        ),
        Form(
            # style="position: fixed; left: 0; right: 0; bottom: 0; background: #ffffff; padding: 12px 16px; border-top: 1px solid #e5e7eb; box-shadow: 0 -6px 18px rgba(0,0,0,.05); z-index: 1000;",style="position: fixed; left: 0; right: 0; bottom: 0; background: #ffffff; padding: 12px 16px; border-top: 1px solid #e5e7eb; box-shadow: 0 -6px 18px rgba(0,0,0,.05); z-index: 1000;",
            Div(
                Label("Query:", For="query"),
                Textarea(
                    id="query",
                    name="query",
                    rows="4",
                    placeholder="e.g., Simulate an open-loop step response with input change from 0 to 1",
                    style="width: 100%; padding: 8px; font-size: 14px;",
                ),
                style="margin-bottom: 15px;"
            ),
            Details(
                Summary("Advanced Options"),
                Div(
                    Label("Ground Truth Method:"),
                    Select(
                        Option("None", value=""),
                        Option("Ziegler-Nichols", value="zn"),
                        Option("Lambda Tuning", value="lambda"),
                        name="gt_method",
                        style="margin-left: 10px;"
                    ),
                    style="margin-bottom: 10px;"
                ),
                Div(
                    Label("K:"),
                    Input(type="number", name="K", step="0.1", style="width: 80px; margin-right: 15px;"),
                    Label("T:"),
                    Input(type="number", name="T", step="0.1", style="width: 80px; margin-right: 15px;"),
                    Label("L:"),
                    Input(type="number", name="L", step="0.1", style="width: 80px; margin-right: 15px;"),
                    Label("Lambda:"),
                    Input(type="number", name="lam", step="0.1", style="width: 80px;"),
                    style="margin-bottom: 10px; display: flex; flex-direction: row; gap: 10px;"
                ),
            ),
            Button("Run Agent", type="submit", style="padding: 10px 20px; font-size: 16px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;"),
            hx_post="/run",
            hx_target="#results",
            hx_swap="innerHTML",
            hx_indicator="#loading",
        ),
        Div(
            Div("⏳ Agent is thinking...", id="loading", cls="htmx-indicator", style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; font-size: 16px;"),
            Div(id="results"),
            id="results_container", 
            style="margin-top: 30px;" # padding-bottom: 220px;
        ),
    )


@rt("/run", methods=["POST"])
async def post(request):
    """Handle query submission."""
    form_data = await request.form()
    query = form_data.get("query", "")
    gt_method = form_data.get("gt_method", "")
    K = float(form_data.get("K")) if form_data.get("K") else None
    T = float(form_data.get("T")) if form_data.get("T") else None
    L = float(form_data.get("L")) if form_data.get("L") else None
    lam = float(form_data.get("lam")) if form_data.get("lam") else None
    
    if not query.strip():
        return Div(
            Card(P("Please enter a query.", style="color: red;")),
            id="results"
        )
    
    # Initialize agent
    agent = init_agent()
    
    # Prepare ground truth params
    ground_truth_method = gt_method if gt_method else None
    ground_truth_params = None
    if ground_truth_method and K is not None and T is not None and L is not None:
        ground_truth_params = {"K": K, "T": T, "L": L}
        if lam is not None:
            ground_truth_params["lambda"] = lam
    
    # Run agent
    result = agent.run(
        query=query,
        ground_truth_method=ground_truth_method,
        ground_truth_params=ground_truth_params,
    )
    
    if not result.get("success"):
        return Div(
            Card(
                H3("Error", style="color: red;"),
                P(result.get("error", "Unknown error"))
            ),
            id="results"
        )
    
    # Create response components
    output_section = Card(
        H3("Agent Response"),
        Div(NotStr(result["output"].replace("\n", "<br>")))
    )
    
    tool_section = Details(
        Summary("Tool Sequence"),
        Card(Div(NotStr(create_tool_sequence_html(result.get("intermediate_steps", [])))))
    )
    
    plot_html = create_plot(result)
    plot_section = Details(
        Summary("Simulation Results"),
        Card(Div(NotStr(plot_html)))
    )
    
    eval_section = None
    if "evaluation" in result:
        eval_section = Card(
            H3("Evaluation"),
            Div(NotStr(create_evaluation_html(result["evaluation"])))
        )
    
    trace_section = Details(
        Summary("Execution Trace"),
        Card(Div(NotStr(create_trace_html(result.get("trace")))))
    )
    
    prompts_section = Card(
        H3("LLM Prompts (debug)"),
        Div(NotStr("<hr>".join(f"<pre>{p}</pre>" for p in result.get("llm_prompts", []))))
    )


    # Combine all sections
    sections = [output_section, tool_section, plot_section, trace_section, prompts_section]
    if eval_section:
        sections.append(eval_section)
    
    #return Div(*sections, id="results")
    return Div(*sections)  # swap into #results; don't duplicate the id


def main(host: str = "127.0.0.1", port: int = 5000):
    """Start the dashboard server."""
    print(f"Starting FMI Agent Dashboard at http://{host}:{port}")
    print("Press Ctrl+C to stop")
    print("\nRegistered routes:")
    for route in app.routes:
        methods = getattr(route, 'methods', ['GET'])
        print(f"  {route.path} - {methods}")
    serve(host=host, port=port)


if __name__ == "__main__":
    main()

