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

The Lambda-tuning method is a model-based tuning approach that provides direct control over the closed-loop time constant. The method calculates PI controller parameters as:

- **Proportional gain**: $K_p = \frac{T}{K(\lambda + L)}$
- **Integral time**: $T_i = T$

Where $\lambda$ (lambda) is the desired closed-loop time constant, typically set to 1-3 times the process dead time $L$.

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
from mcp_fmi_ecc26 import FOPDT, ZieglerNicholsMethod

# Create FOPDT system
system = FOPDT(K=2.0, T=1.0, L=0.5)

# Calculate Ziegler-Nichols parameters
zn_method = ZieglerNicholsMethod(system)

print(f"Ultimate Point: {zn_method.ultimate_point}")
print(f"PI Controller: {zn_method.pi_controller}")
```

#### Lambda-Tuning Method
```python
from mcp_fmi_ecc26 import FOPDT
from mcp_fmi_ecc26.lam import LambdaTuningMethod

# Create FOPDT system
system = FOPDT(K=2.0, T=1.0, L=0.5)

# Calculate Lambda-tuning parameters with default lambda=2.0
lam_method = LambdaTuningMethod(system, lam=2.0)

print(f"PI Controller: {lam_method.pi_controller}")
print(f"Lambda Parameter: {lam_method.lam}")
```

## Parameters

### System Parameters
- **K**: Static process gain (output/input ratio)
- **T**: Process time constant [s] (must be > 0)
- **L**: Effective time delay [s] (must be ≥ 0)

### Lambda Parameter (λ)
The lambda parameter controls the closed-loop response speed:
- **Small λ** (0.2-1 × T): Faster response, less robust
- **Large λ** (1-3 × L): Slower response, more robust
- **Default**: 2.0 (good balance for most systems)

## PI-controller tuning
- The experiment prodecure for the Ziegler-Nichols closed-loop (ultimate gain) tuning method is outlined in [`docs/zn_method.md`](docs/zn_method.md)
- The experiment prodecure for the Lambda-tuning method is outlined in [`docs/lam_method.md`](docs/lam_method.md)






