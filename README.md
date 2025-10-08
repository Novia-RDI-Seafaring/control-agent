# mcp-fmi-ecc26
## Features

- The package **`mcp-fmi-ecc26.zn`** contains methods that return *ground-truth tuning parameters* for the **Ziegler–Nichols** method.  
- The package **`mcp-fmi-ecc26.lam`** contains methods that return *ground-truth tuning parameters* for the **Lambda-tuning** method.

## Experiment Setup
We consider a **First-Order Plus Dead-Time (FOPDT)** system:

$$
G_\mathrm{p}(s) = \frac{K\,e^{-Ls}}{T s + 1}
$$

to which an ideal **PI controller** with output

$$
u(t) = K_\mathrm{p}\left( e(t) + \frac{1}{T_\mathrm{i}}\int_0^te(\tau)\mathrm{d}\tau \right),
$$

with $e(t) = r(t) - y(t)$ with $r(t)$ the setpoint and $y(t)$ the measured output of the system, is is to be tuned automatically using an **AI agent**. The agent can perform simulated experiments. It has access to access to tools that:
- Reads the model descriptions  
- Designs input signals  
- Sets model parameters  
- Run simulations 

Tools are provided through the [`mcp-fmi`](https://github.com/Novia-RDI-Seafaring/mcp-fmi) through the Model Context Protocol (MCP). 


### Functional Mock-Up Unit
The system and controller are packaged as a single **Functional Mock-up Unit (FMU)** that ahs the following two models
- `manual`: The operator directly determines the control signal $u(t)$. This is, e.g., used when performing open-loop experiments.
- `automatic`: The PI control law is active and the controller computes the control signal $u(t)$. This is the normal operating mode and also used when performing closed-loop experiments.

### Lambda-Tuning Method

## Installation
```bash
# Clone and sync dependencies
git clone <repository-url>
cd mcp-fmi-ecc26
uv sync
```

## Usage

### Command Line Interface

```bash
# Run with custom parameters
uv run ecc26 --K 1.0 --T 1.0 --L 1.0 --method zn

# Default method (zn)
uv run ecc26 --K 2.0 --T 1.5 --L 0.5

# Get help
uv run ecc26 --help
```

### Python API

```python
from mcp_fmi_ecc26 import FOPDT, ZieglerNicholsMethod

# Create FOPDT system
system = FOPDT(K=2.0, T=1.0, L=0.5)

# Calculate Ziegler-Nichols parameters
zn_method = ZieglerNicholsMethod(system)

print(f"Ultimate Point: {zn_method.ultimate_point}")
print(f"PI Controller: {zn_method.pi_controller}")
```

## PI-controller tuning
- The experiment prodecure for the Ziegler-Nichols closed-loop (ultimate gain) tuning method is outlined in [`docs/zn_method.md`](docs/zn_method.md)
- The experiment prodecure for the Lambda-tuning method is outlined in [`docs/lam_method.md`](docs/lam_method.md)






