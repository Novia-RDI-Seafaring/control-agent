# mcp-fmi-ecc26

Ziegler-Nichols Method implementation for First-Order Plus Dead Time (FOPDT) system analysis.

## Features
- **FOPDT System Modeling**: First-Order Plus Dead Time system representation
- **Ziegler-Nichols Method**: Closed-loop ultimate gain method for controller tuning
- **PI Controller Design**: Automatic calculation of PI controller parameters
- **CLI Interface**: Command-line tool with individual parameter options

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




