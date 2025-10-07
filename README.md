# mcp-fmi-ecc26

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
# Run with default parameters (K=2.0, T=1.0, L=0.5)
uv run python -m mcp_fmi_ecc26.cli

# Run with custom parameters
uv run python -m mcp_fmi_ecc26.cli --K 3.0 --T 2.0 --L 1.0

# Get help
uv run python -m mcp_fmi_ecc26.cli --help
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


