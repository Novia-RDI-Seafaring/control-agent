import pytest
from control_toolbox.tools.simulation import simulate, simulate_step_response, SimulationProps
from control_toolbox.schema import DataModel, Signal
from control_toolbox.tools.timeseries import StepProps, TimeRange

simulation_props = SimulationProps(
    fmu_name="PI_FOPDT",
    start_time=0.0,
    stop_time=2.0,
    output_interval=0.4,
    start_values={
        "mode": False,
    }
)

step_props = StepProps(
    signal_name="input",
    time_range=TimeRange(start=0.0, stop=1.0, sampling_time=0.2),
    step_time=0.4,
    initial_value=0.0,
    final_value=1.0
)

TOLERANCE = 1E-4

def test_simulate():
    simulation_results = simulate(sim_props=simulation_props)
    # data
    assert simulation_results.data is not None
    data = simulation_results.data
    
    # Check timestamps
    assert data.timestamps == pytest.approx([0.0, 0.4, 0.8, 1.2, 1.6, 2.0], abs=TOLERANCE)
    
    # Check signals exist
    signal_names = [s.name for s in data.signals]
    assert "y" in signal_names
    assert "u" in signal_names
    
    # Check values
    y_signal = next(s for s in data.signals if s.name == "y")
    u_signal = next(s for s in data.signals if s.name == "u")
    assert y_signal.values == pytest.approx([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], abs=TOLERANCE)
    assert u_signal.values == pytest.approx([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], abs=TOLERANCE)

def test_simulate_step_response():
    simulation_results = simulate_step_response(sim_props=simulation_props, step_props=step_props)
    # data
    assert simulation_results.data is not None
    data = simulation_results.data
    
    # Check timestamps
    assert data.timestamps == pytest.approx([0.0, 0.4, 0.8, 1.2, 1.6, 2.0], abs=TOLERANCE)
    
    # Check signals exist
    signal_names = [s.name for s in data.signals]
    assert "y" in signal_names
    assert "u" in signal_names
    
    # Check values
    y_signal = next(s for s in data.signals if s.name == "y")
    u_signal = next(s for s in data.signals if s.name == "u")
    
    # Check y values (output) - approximate values
    assert y_signal.values == pytest.approx([0.0, 0.0, 0.0, 0.0, 0.0488, 0.2212], abs=TOLERANCE)
    
    # Check u values (input) - step should be applied
    assert u_signal.values == pytest.approx([0.0, 0.0, 1.0, 1.0, 1.0, 1.0], abs=TOLERANCE)
