# control-agent

An LLM-based agent for performing control-oriented simulation tasks. Developed as part of the research paper:

> **Agent-in-the-Loop: Using AI Agents to Perform Control-Oriented Simulation Tasks**
> C. Bjorkskog, L. Jatta, M. Manngard — ECC 2026

## Overview

This repository contains the `control-agent` framework and benchmark experiments used to evaluate how effectively LLM-based agents can plan and execute multi-step control-engineering workflows such as system identification and PI controller tuning.

The agent is built with [PydanticAI](https://github.com/pydantic/pydantic-ai) and uses [agent-control-toolbox](https://github.com/Novia-RDI-Seafaring/agent-control-toolbox) for simulation and analysis tools. Simulation models are packaged as Functional Mock-up Units (FMUs) following the [FMI standard](https://fmi-standard.org/). The benchmark experiments reported in the paper were conducted using OpenAI's `gpt-5-mini` model deployed on Azure OpenAI.

## Installation

```bash
git clone https://github.com/Novia-RDI-Seafaring/control-agent.git
cd control-agent
uv sync
```

### Environment Setup

Copy the example environment file and fill in your credentials:

```bash
cp env.example .env
```

Required variables:
- `AZURE_OPENAI_ENDPOINT` — Your Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY` — Your Azure OpenAI API key
- `OPENAI_API_VERSION` — API version (e.g., `2024-12-01-preview`)

## Test Model

The benchmark experiments use a **First-Order Plus Dead-Time (FOPDT)** plant model:

$$
G_\mathrm{p}(s) = \frac{K\,e^{-Ls}}{T s + 1}
$$

controlled by an ideal **PI controller**:

$$
u(t) = K_\mathrm{p}\left( e(t) + \frac{1}{T_\mathrm{i}}\int_0^te(\tau)\mathrm{d}\tau \right)
$$

The controller and plant are packaged as a single FMU with exposed parameters (`Kp`, `Ti`, `mode`) and hidden plant dynamics, preventing the agent from exploiting prior knowledge.

## Benchmark Experiments

Six experiments of increasing complexity evaluate the agent's ability to chain tool calls:

| # | Experiment | Description |
|---|-----------|-------------|
| 1 | `open_loop_step` | Simulate an open-loop step response |
| 2 | `closed_loop_step` | Simulate a closed-loop step response with given PI parameters |
| 3 | `step_response_analysis` | Closed-loop simulation + compute rise time, settling time, overshoot |
| 4 | `system_identification` | Open-loop step test + identify FOPDT model parameters |
| 5 | `lambda_tuning` | System identification + PI tuning via SIMC/lambda method |
| 6 | `specification_tuning` | Iterative tuning to meet performance specifications |

### Running Experiments

```bash
# Run all experiments
uv run eval

# Run a specific experiment
uv run eval --experiment open_loop_step
```

## Ground-Truth Tuning Methods

The package includes ground-truth implementations for validating agent results:

```python
from control_agent import FOPDT, ZieglerNicholsMethod
from control_agent.lam import LambdaTuningMethod

system = FOPDT(K=2.0, T=1.0, L=0.5)

# Ziegler-Nichols
zn = ZieglerNicholsMethod(system)
print(f"PI Controller: {zn.pi_controller}")

# Lambda tuning
lam = LambdaTuningMethod(system, lam=2.0)
print(f"PI Controller: {lam.pi_controller}")
```

### CLI

```bash
# Ziegler-Nichols tuning
uv run ecc26 --K 1.0 --T 1.0 --L 1.0 --method zn

# Lambda tuning
uv run ecc26 --K 1.0 --T 1.0 --L 1.0 --method lam --lam 3.0
```

## Agent Resources

Background materials provided to the agent as markdown resources:

- [`docs/zn_method.md`](docs/zn_method.md) — Ziegler-Nichols closed-loop tuning procedure
- [`docs/lam_method.md`](docs/lam_method.md) — Lambda tuning procedure
- [`docs/seaborg.md`](docs/seaborg.md) — Selected chapters from Seborg et al. (2016), *Process Dynamics and Control*

## Project Structure

```
src/control_agent/
  agent/          # Agent framework (PydanticAI-based)
  evals/          # Evaluation framework and experiment definitions
  prompts/        # System prompts
  cli.py          # CLI entry point
  fopdt_sys.py    # FOPDT system model
  zn.py           # Ziegler-Nichols ground truth
  lam.py          # Lambda tuning ground truth
models/fmus/      # FMU simulation models
docs/             # Agent resources (markdown)
```

## License

See [LICENSE](LICENSE) for details.

## Citation

If you use this work, please cite:

```bibtex
@inproceedings{bjorkskog2026agent,
  title={Agent-in-the-Loop: Using AI Agents to Perform Control-Oriented Simulation Tasks},
  author={Bj{\"o}rkskog, Christoffer and Jatta, Lamin and Manng{\aa}rd, Mikael},
  booktitle={European Control Conference (ECC)},
  year={2026}
}
```
