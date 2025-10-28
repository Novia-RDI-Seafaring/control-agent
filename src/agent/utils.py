from collections.abc import Mapping # for more robust extractor (handles nested keys, JSON strings, and different shapes)
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# def create_plot(result: dict) -> str:
#     """Create Plotly visualization of simulation results."""
#     if not result.get("success") or not result.get("intermediate_steps"):
#         return "<p>No simulation data available</p>"
#     
#     # Extract simulation data from intermediate steps
#     sim_data = None
#     for step in result["intermediate_steps"]:
#         if len(step) >= 2:
#             observation = step[1]
#             if isinstance(observation, dict) and "time" in observation and "y" in observation:
#                 sim_data = observation
#                 break
#     
#    if not sim_data:
#        return "<p>No simulation data found</p>"
#    
#    # Create subplot figure
#    fig = make_subplots(
#        rows=2, cols=1,
#        subplot_titles=("Process Output (y)", "Control Signal (u)"),
#        vertical_spacing=0.12,
#        shared_xaxes=True,
#    )
#    
#    time = sim_data.get("time", [])
#    
#    # Plot y
#    if "y" in sim_data:
#        fig.add_trace(
#           go.Scatter(x=time, y=sim_data["y"], name="y (output)", line=dict(color="blue")),
#            row=1, col=1
#        )
#    
#    # Plot setpoint if available
#    if "setpoint" in sim_data:
#        fig.add_trace(
#            go.Scatter(x=time, y=sim_data["setpoint"], name="setpoint", line=dict(color="red", dash="dash")),
#            row=1, col=1
#        )
#    
#    # Plot u
#   if "u" in sim_data:
#        fig.add_trace(
#            go.Scatter(x=time, y=sim_data["u"], name="u (control)", line=dict(color="orange")),
#            row=2, col=1
#        )
#    
#    # Update layout
#    fig.update_xaxes(title_text="Time [s]", row=2, col=1)
#    fig.update_yaxes(title_text="y", row=1, col=1)
#    fig.update_yaxes(title_text="u", row=2, col=1)
#    fig.update_layout(height=600, showlegend=True, hovermode='x unified')
#    
#    return fig.to_html(div_id="plot", include_plotlyjs=False)


def create_plot(result: dict) -> str:
    """Create Plotly visualization of simulation results (robust key/shape handling)."""
    if not result.get("success"):
        return "<p>No simulation data available</p>"

    steps = result.get("intermediate_steps") or []

    def _extract(obs):
        # parse JSON strings
        if isinstance(obs, str):
            try:
                obs = json.loads(obs)
            except Exception:
                return None

        # try normalize dict
        if isinstance(obs, Mapping):
            def get_path(d, *paths):
                for p in paths:
                    if isinstance(p, tuple):  # nested path
                        cur = d
                        ok = True
                        for k in p:
                            if not isinstance(cur, Mapping) or k not in cur:
                                ok = False; break
                            cur = cur[k]
                        if ok and cur is not None:
                            return cur
                    else:
                        if p in d and d[p] is not None:
                            return d[p]
                return None

            time = get_path(obs, "time", "t", ("data","time"), ("result","time"), ("outputs","time"))
            y    = get_path(obs, "y", ("outputs","y"), ("result","y"), ("data","y"))
            u    = get_path(obs, "u", ("outputs","u"), ("result","u"), ("data","u"))
            sp   = get_path(obs, "setpoint", ("inputs","setpoint"), ("result","setpoint"), ("data","setpoint"))

            # handle signal list format: {"signals":[{"name":"y","values":[...]},...]}
            if (y is None or u is None or sp is None) and "signals" in obs and isinstance(obs["signals"], list):
                for sig in obs["signals"]:
                    if isinstance(sig, Mapping):
                        name = sig.get("name")
                        vals = sig.get("values")
                        if name == "y" and y is None: y = vals
                        if name == "u" and u is None: u = vals
                        if name in ("setpoint","r") and sp is None: sp = vals

            if time is not None and any(s is not None for s in (y, u, sp)):
                # convert numpy arrays to lists if present
                def to_list(x):
                    try:
                        import numpy as np
                        if isinstance(x, np.ndarray): return x.tolist()
                    except Exception:
                        pass
                    return list(x) if hasattr(x, "__iter__") and not isinstance(x, (str, bytes)) else x

                data = {"time": to_list(time)}
                if y is not None:  data["y"] = to_list(y)
                if u is not None:  data["u"] = to_list(u)
                if sp is not None: data["setpoint"] = to_list(sp)
                return data

            # recurse into children
            for v in obs.values():
                if isinstance(v, (Mapping, list, tuple)):
                    cand = _extract(v)
                    if cand: return cand

        # list/tuple containers
        if isinstance(obs, (list, tuple)):
            for v in obs:
                cand = _extract(v)
                if cand: return cand
        return None

    # search from latest tool output backwards
    sim_data = None
    for _, observation in reversed(steps):
        sim_data = _extract(observation)
        if sim_data: break

    if not sim_data:
        return "<p>No simulation data found</p>"

    # ---- plotting ----
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Process Output (y)", "Control Signal (u)"),
        vertical_spacing=0.12,
        shared_xaxes=True,
    )

    time = sim_data.get("time", [])
    if sim_data.get("y") is not None:
        fig.add_trace(go.Scatter(x=time, y=sim_data["y"], name="y (output)", line=dict(color="blue")), row=1, col=1)
    if sim_data.get("setpoint") is not None:
        fig.add_trace(go.Scatter(x=time, y=sim_data["setpoint"], name="setpoint", line=dict(color="red", dash="dash")), row=1, col=1)
    if sim_data.get("u") is not None:
        fig.add_trace(go.Scatter(x=time, y=sim_data["u"], name="u (control)", line=dict(color="orange")), row=2, col=1)

    fig.update_xaxes(title_text="Time [s]", row=2, col=1)
    fig.update_yaxes(title_text="y", row=1, col=1)
    fig.update_yaxes(title_text="u", row=2, col=1)
    fig.update_layout(height=600, showlegend=True, hovermode="x unified")
    return fig.to_html(div_id="plot", include_plotlyjs=False)
