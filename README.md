# mcp-fmi-ecc26
## Features

- The package **`mcp-fmi-ecc26.zn`** contains methods that return *ground-truth tuning parameters* for the **Ziegler–Nichols** method.  
- The package **`mcp-fmi-ecc26.lam`** contains methods that return *ground-truth tuning parameters* for the **Lambda-tuning** method.

## Installation
```bash
# Clone and sync dependencies
git clone <repository-url>
cd mcp-fmi-ecc26
uv sync
```

## Usage

### Command Line Interface

#### Ziegler-Nichols Method
```bash
# Ziegler-Nichols tuning
uv run ecc26 --K 1.0 --T 1.0 --L 1.0 --method zn

# Default method (zn)
uv run ecc26 --K 2.0 --T 1.5 --L 0.5
```

#### Lambda-Tuning Method
```bash
# Lambda-tuning with default lambda=2.0
uv run ecc26 --K 1.0 --T 1.0 --L 1.0 --method lam

# Lambda-tuning with custom lambda=3.0
uv run ecc26 --K 1.0 --T 1.0 --L 1.0 --method lam --lam 3.0

# Get help
uv run ecc26 --help
```

### Python API

#### Ziegler-Nichols Method
```python
from control_agent import FOPDT, ZieglerNicholsMethod

# Create FOPDT system
system = FOPDT(K=2.0, T=1.0, L=0.5)

# Calculate Ziegler-Nichols parameters
zn_method = ZieglerNicholsMethod(system)

print(f"Ultimate Point: {zn_method.ultimate_point}")
print(f"PI Controller: {zn_method.pi_controller}")
```

#### Lambda-Tuning Method
```python
from control_agent import FOPDT
from control_agent import LambdaTuningMethod

# Create FOPDT system
system = FOPDT(K=2.0, T=1.0, L=0.5)

# Calculate Lambda-tuning parameters with default lambda=2.0
lam_method = LambdaTuningMethod(system, lam=2.0)

print(f"PI Controller: {lam_method.pi_controller}")
print(f"Lambda Parameter: {lam_method.lam}")
```

# Experiment Setup
 The agent can perform simulated experiments. It has access to access to tools that:
- Reads the model descriptions  
- Designs input signals  
- Sets model parameters  
- Run simulations

## Simulation models
We consider a **First-Order Plus Dead-Time (FOPDT)** system:

$$
G_\mathrm{p}(s) = \frac{K\,e^{-Ls}}{T s + 1}
$$

to which an ideal **PI controller** with output

$$
u(t) = K_\mathrm{p}\left( e(t) + \frac{1}{T_\mathrm{i}}\int_0^te(\tau)\mathrm{d}\tau \right),
$$

with $e(t) = r(t) - y(t)$ with $r(t)$ the setpoint and $y(t)$ the measured output of the system. The controller and system are packaged as a [Functional Mock-Up Unit](https://fmi-standard.org/)

The system and controller are packaged as a single **Functional Mock-up Unit (FMU)** that has the following two parameters, inputs, and outputs.

### Parameters


- **K**: Static gain of the plant
- **T** : Time constant of the plant
- **L**: DEat time of the plant
- **K_c**: PI-controller proportional gain
- **T_i**: PI-contoller integration time constant
- **mode**:
    - `manual`: The operator directly determines the control signal $u(t)$. This is, e.g., used when performing open-loop experiments.
    - `automatic`: The PI control law is active and the controller computes the control signal $u(t)$. This is the normal operating mode and also used when performing closed-loop experiments.

### Inputs
- **input**: Input signal when operating in open loop, i.e., `mode = "manual"`
- **setpoint**: Controller setppiont signal when operating in closed loop, i.e., `model = "automatic"`
- **measurement**: Measured output of the plant

### Outputs
- **y** Measured output of the plant
- **u** Control signal applied to the plant

## Tools
- [MCP-FMI](https://github.com/Novia-RDI-Seafaring/mcp-fmi)

### Resources
It is often useful to provide resources to an agent to help it understand how specific tools are expected to be used. Therefore, we have compiled documentation relevant to **PI controller tuning**.

- [`docs/zn_method.md`](docs/zn_method.md): Outlines the experimental procedure for the **Ziegler–Nichols closed-loop (ultimate gain) tuning method**.  
- [`docs/lam_method.md`](docs/lam_method.md): Describes the experimental procedure for the **Lambda tuning method**.  
- [`docs/seaborg.md`](docs/seaborg.md): Contains selected chapters from *Seborg, D. E., Edgar, T. F., Mellichamp, D. A., & Doyle III, F. J. (2016). Process Dynamics and Control*. John Wiley & Sons.

## The Agent

The FMI Agent is an intelligent assistant that can interact with FMU models, perform simulations, and provide generative UI components for visualization. It uses the AG-UI protocol to enable dynamic UI rendering based on simulation results.

### Features
- **Generative UI**: Automatically renders appropriate UI components based on context
- **FMU Simulation**: Run simulations and visualize results with interactive plots
- **Model Information**: Display detailed FMU metadata and variable information
- **Signal Creation**: Create and visualize custom input signals
- **Real-time Chat**: Interactive chat interface with the agent

### Quick Start

1. **Setup the environment:**
```bash
# Install Python dependencies
uv sync

# Setup frontend (requires Node.js)
python setup_frontend.py
```

2. **Start the development servers:**
```bash
# Start both backend and frontend
python start_dev.py
```

3. **Access the interface:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Usage Examples

- "Show me information about the fopdt_pi model" → Displays model metadata and variables
- "Simulate the fopdt_pi model for 10 seconds" → Shows interactive simulation plot
- "Create a sine wave signal" → Displays signal visualization
- "Tune the PI controller using Lambda tuning" → Shows controller parameters and performance

## Experiment queries

| Query                                                                 | Expected Tool Calls                                                                                                  | Expected Output                                                                 |
|-----------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| "Change the control parameters to K_p = 1.0 and T_i = 2.0"            | 1. `set_parameters`                                                                                                  | Controller updated with $K_p = 1.0$ and $T_i = 2.0$.                            |
| "Simulate an open-loop step response with input change from 0 to 1"   | 1. Set controller to mode "manual" with `set_parameters`.<br>2. `generate_input`.<br>3. `simulate`.                   | Return open-loop step response.                                                 |
| "Simulate a closed-loop step response with input change from 0 to 1"  | 1. Set controller to mode "automatic" with `set_parameters`.<br>2. `generate_input`.<br>3. `simulate`.                | Return closed-loop step response and performance metrics (rise time, overshoot).|
| "Make a step response and identify a first-order plus dead time (FOPDT) model" | 1. `simulate` open-loop.<br>2. `fit_model` with FOPDT structure.<br>3. Extract $K$, $T$, and $L$ from step response.                     | FOPDT model: $G_p(s) = \dfrac{K e^{-Ls}}{Ts + 1}$.                              |
| "Tune the PI controller with Lambda tuning lambda = 1.0"              | 1. Use identified $K$, $T$, $L$.<br>2. Compute $K_c = \dfrac{T}{K(\lambda + L)}$, $T_i = T$.<br>3. `set_parameters`. | Controller updated for $\lambda = 1.0$ tuning.                                  |
| "Tune the PI controller with Lambda tuning for fast response"         | 1. Select $\lambda \approx L$.<br>2. Compute $K_c = \dfrac{T}{K(\lambda + L)}$, $T_i = T$.<br>3. `set_parameters`.   | Controller updated for fast-response tuning.                                    |
| "Tune the PI controller with Lambda tuning for balanced response"     | 1. Select $\lambda = T$.<br>2. Compute $K_c = \dfrac{T}{K(\lambda + L)}$, $T_i = T$.<br>3. `set_parameters`.         | Controller updated for balanced-response tuning.                                |
| "Tune the PI controller with Lambda tuning for robust response"       | 1. Select $\lambda \ge 2T$.<br>2. Compute $K_c = \dfrac{T}{K(\lambda + L)}$, $T_i = T$.<br>3. `set_parameters`.      | Controller updated for robust-response tuning.                                  |
| "Tune the PI controller using Ziegler-Nichols closed-loop method"     | 1. Disable integral action ($T_i \to \infty$).<br>2. Increase $K_p$ until sustained oscillations → record $K_u$, $T_u$.<br>3. Compute $K_p = 0.45K_u$, $T_i = \dfrac{T_u}{1.2}$.<br>4. `set_parameters`. | Controller updated using Ziegler–Nichols closed-loop tuning.                    |

# Logfire
- Run `logfire auth` and follow instructions to authenticate your local envoronment
- Point to correct project: `uv run logfire projects use "agent-fmi"`
- 








