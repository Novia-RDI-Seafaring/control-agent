import matplotlib.pyplot as plt
from agent.tools.functions.schema import (
    StepProps, TimeRange, SimulationModel, AnalysisProps, 
    DataModel, StepResponseAnalysis,
    UltimateTuningProps, UltimateGainParameters
)
from agent.tools.fmi_tools import generate_step_tool, simulate_tool, analyse_step_response, zn_pid_tuning
import numpy as np


def plot_results(
    data: DataModel,
    analysis: StepResponseAnalysis = None,
    title: str = "Step Response Results"
):
    """
    Plot simulation results using matplotlib.
    
    Args:
        data: DataModel containing timestamps and signals to plot
        analysis: Optional StepResponseAnalysis to overlay characteristic points
        title: Title for the plot
    """
    fig, axes = plt.subplots(len(data.signals), 1, figsize=(10, 6 * len(data.signals)))
    
    timestamps = data.timestamps

    t = np.asarray(timestamps, dtype=float)
    y = None
    u = None
    for s in data.signals:
        if s.name == "y":
            y = np.asarray(s.values, dtype=float)
        elif s.name == "u":
            u = np.asarray(s.values, dtype=float)

    ax = axes[0]
    ax.plot(t, y, label="y", linewidth=2)
    ax.legend()
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Value")
    ax.set_title("Step Response")
    ax.grid(True)
    ax.legend()

    ax = axes[1]
    ax.plot(t, u, label="u", linewidth=2)
    ax.legend()
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Value")
    ax.set_title("Step Response")
    ax.grid(True)
    ax.legend()

    # add characteristic points with text labels
    ax = axes[0]
    points = [
        ("p0", analysis.characteristic_points.p0, "p0", 'x', 'red'),
        #("p10", analysis.characteristic_points.p10, "p10", 'x', 'red'),
        ("p63", analysis.characteristic_points.p63, "p63", 'x', 'red'),
        #("p90", analysis.characteristic_points.p90, "p90", 'x', 'red'),
        ("p98", analysis.characteristic_points.p98, "p98", 'x', 'red'),
        ("pRT0", analysis.characteristic_points.pRT0, "pRT0", 'x', 'green'),
        ("pRT1", analysis.characteristic_points.pRT1, "pRT1", 'x', 'green'),
        ("pST", analysis.characteristic_points.pST, "pST", 'x', 'blue'),
        ("pPeak", analysis.characteristic_points.pPeak, "Overshoot", 'x', 'magenta'),
        ("pUndershoot", analysis.characteristic_points.pUndershoot, "Undershoot", 'x', 'magenta'),
    ]
    for name, (x, y), label, marker, color in points:
        ax.scatter(x, y, color=color, marker=marker, s=100)
        # Add label next to the point, slightly shifted for readability
        ax.text(x, y, f" {label}, ({x:.2f}, {y:.2f})", color=color, fontsize=10, verticalalignment="bottom", horizontalalignment="left")
        
    plt.suptitle(title, fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.show()


## Generate input signal
step_props = StepProps(
    signal_name="input",
    time_range=TimeRange(start=0.0, stop=30.0, sampling_time=0.1),
    step_time=2.0,
    initial_value=0.0,
    final_value=1.0
)

step= generate_step_tool(step_props)
print("STEP: ")
print(step.model_dump_json(indent=2))

## Simulate system
simulate_props = SimulationModel(
    fmu_name="PI_FOPDT_2",
    start_time=0.0,
    stop_time=30.0,
    input=step,
    output=["y", "u"],
    output_interval=0.1,
    start_values={
        "Kp": 1.71,
        "Ti": 2.84,
        "mode": 1
    }
)

result = simulate_tool(simulate_props)

#print("STEP RESPONSE: ")
#print(result.model_dump_json(indent=2))

## Analyse results

analysis_props = AnalysisProps(
    settling_time_treshhold=0.02,
    rise_time_limits=(0.1, 0.9)
)

analysis = analyse_step_response(signal_name="y", data=result, props=analysis_props)

print("ANALYSIS: ")
print(analysis.model_dump_json(indent=2))

## Plot results
plot_results(result, analysis=analysis)



## tuning tests

#Z-N tuning
tuning_props = UltimateTuningProps(
    params=UltimateGainParameters(Ku=3.8, Pu=3.41),
    controller="pi",
    method="classic"
)

tuning = zn_pid_tuning(tuning_props)
print("Z-N TUNING: ")
print(tuning.model_dump_json(indent=2))


#lambda tuning
K = 1
T= 2
L = 1
lam = L #balanced response
#lambda tuning
Kp = T / (K * (lam + L))
Ti = min(T, 4 * (lam + L))
print("Lambda TUNING: ")
print(f"Kp: {Kp}, Ti: {Ti}")